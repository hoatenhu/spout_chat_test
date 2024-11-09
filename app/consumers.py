import os
import json
import boto3
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from datetime import datetime
import logging
from botocore.exceptions import ClientError
import uuid
from decouple import config

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Local testing: 
        # self.dynamodb = boto3.resource(
        #     'dynamodb',
        #     region_name=config('DYNAMODB_REGION', default='ap-southeast-1'),
        #     endpoint_url=config('DYNAMODB_ENDPOINT_URL', default='http://localhost:8002')
        # )
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
            region_name=config('AWS_DEFAULT_REGION')
        )
        
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

        # Check if the Conversations table exists, if not, create it
        try:
            self.conversations_table = self.dynamodb.Table('Conversations')
            self.conversations_table.load()  # This will raise an exception if the table does not exist
            logging.info(f"Using existing DynamoDB table: {self.conversations_table.name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logging.info("Table 'Conversations' not found, creating it now.")
                self.conversations_table = self.dynamodb.create_table(
                    TableName='Conversations',
                    KeySchema=[
                        {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'conversation_id', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                self.conversations_table.meta.client.get_waiter('table_exists').wait(TableName='Conversations')
                logging.info("Table 'Conversations' created successfully.")
            else:
                logging.error(f"Unexpected error: {e}")
                raise

    async def connect(self):
        # Extract customer_id from the URL route
        self.customer_id = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.customer_id}'

        # Check for an existing conversation based on customer_id
        try:
            conversations_table = self.dynamodb.Table('Conversations')
            # Query for an existing conversation with the same customer_id
            response = await sync_to_async(conversations_table.scan)(
                FilterExpression=boto3.dynamodb.conditions.Attr('customer_id').eq(self.customer_id)
            )
            if response['Items']:
                # Use the first existing conversation
                self.conversation_id = response['Items'][0]['conversation_id']
                logging.info(f"Using existing conversation: {self.conversation_id}")
                # Update the existing conversation with updated_at
                await sync_to_async(conversations_table.update_item)(
                    Key={'conversation_id': self.conversation_id},
                    UpdateExpression="set updated_at = :u",
                    ExpressionAttributeValues={
                        ':u': datetime.now().isoformat()
                    }
                )
                logging.info(f"Conversation {self.conversation_id} updated successfully.")
            else:
                # Generate a new conversation_id if no existing conversation is found
                self.conversation_id = str(uuid.uuid4())  # Store as an instance variable
                # Create a new conversation item
                await sync_to_async(conversations_table.put_item)(
                    Item={
                        'conversation_id': self.conversation_id,
                        'vendor_id': 'your_vendor_id',  # Replace with actual vendorId logic
                        'customer_id': self.customer_id,
                        'started_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                        'assigned_user_id': None,
                        'assigned_team_id': None,
                        'colab_users': [],
                        'is_open': True
                    }
                )
                logging.info(f"New conversation {self.conversation_id} created successfully.")
        except Exception as e:
            logging.error(f"Error fetching or creating conversation: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to fetch or create conversation.'
            }))

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
                    'timestamp': message['timestamp']
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
                    'conversation_id': self.conversation_id,  # Add conversation_id
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

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))