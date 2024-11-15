import json
import boto3
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from datetime import datetime
import logging
from botocore.exceptions import ClientError
from app.helpers.conversation import create_conversation, send_whatsapp_message
from app.helpers.dynamodb_helpers import get_dynamodb_resource

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender_id = None  # Initialize sender_id
        
        self.dynamodb = get_dynamodb_resource()
        
        # Check if the Messages table exists, if not, create it
        try:
            self.table = self.dynamodb.Table('Messages')
            self.table.load()  # This will raise an exception if the table does not exist
            logging.info(f"Using existing DynamoDB table: {self.table.name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logging.info("Table 'Messages' not found, creating it now.")
                self.table = self.dynamodb.create_table(
                    TableName='Messages',
                    KeySchema=[
                        {'AttributeName': 'customer_id', 'KeyType': 'HASH'},  # Partition key
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'customer_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                self.table.meta.client.get_waiter('table_exists').wait(TableName='Messages')
                logging.info("Table 'Messages' created successfully.")
            else:
                logging.error(f"Unexpected error: {e}")
                raise


    async def connect(self):
        # Extract customer_id from the URL route
        self.customer_id = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.customer_id}'

        try:
            self.conversation_id = await sync_to_async(create_conversation)(self.customer_id)
            if self.conversation_id is None:
                await self.send(text_data=json.dumps({
                    'error': 'Failed to access Conversations table.'
                }))
                return
            logging.info(f"Using conversation: {self.conversation_id}")
        except Exception as e:
            logging.error(f"Error fetching or creating conversation: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to fetch or create conversation.'
            }))
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Fetch message history from DynamoDB
        try:
            response = await sync_to_async(self.table.query)(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('customer_id').eq(self.customer_id)
            )
            messages = response.get('Items', [])
            # Send message history to the WebSocket
            for message in messages:
                await self.send(text_data=json.dumps({
                    'message': message['message'],
                    'timestamp': message['timestamp'],
                    'sender_id': message['sender_id']
                }))
        except Exception as e:
            logging.error(f"Error fetching message history: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to fetch message history.'
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        if not text_data.strip():
            logging.error("Received empty message.")
            await self.send(text_data=json.dumps({
                'error': 'Received empty message.'
            }))
            return

        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            # Extract sender_id from the first message
            self.sender_id = text_data_json.get('sender_id')

        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format.'
            }))
            return

        # Store message in DynamoDB with timestamp and conversation_id
        try:
            await sync_to_async(self.table.put_item)(
                Item={
                    'customer_id': self.customer_id,
                    'conversation_id': self.conversation_id,
                    'sender_id': self.sender_id,  # Use the extracted sender_id
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logging.error(f"Error storing message: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to store message.'
            }))

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        # Send WhatsApp message after storing in DynamoDB
        phone_number = self.customer_id
        whatsapp_response = await sync_to_async(send_whatsapp_message)(phone_number, message)
        logging.info(f"WhatsApp response: {whatsapp_response}")

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': self.sender_id,
            'timestamp': datetime.now().isoformat()
        }))