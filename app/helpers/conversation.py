from botocore.exceptions import ClientError
import boto3
import uuid
from datetime import datetime
from decouple import config
import requests
from app.helpers.dynamodb_helpers import get_dynamodb_resource

# WA_ACCESS_TOKEN = config("WA_ACCESS_TOKEN")
# SPOUT_PHONE_NUMBER_ID = config("SPOUT_PHONE_NUMBER_ID")
WA_ACCESS_TOKEN = "EAATBZATwXvg0BOZBpmqyZB2gv2yQ3FK2mcJqbCYUxpXrOtZAYZBQDV0NFYilCZCadJWC7uVUbb795dT2zdnM5rGmNdP6fI47hLVNcG8g2LwRCzDsNb8KmmFgf717ZAfJek90q4hviMcDZBIvJAZAqrNg5nq2oYDivOxoHiQA0WToPulOkGtZCmfF01aVVmtnCIZBr6JgQTaXwvss71xmAYuuo76Bk91wZBlyKOmq9ZAYZBNFzUFu0ZD"
SPOUT_PHONE_NUMBER_ID = "146917221848578"
WA_CONFIG_TOKEN = config("WA_CONFIG_TOKEN")

# Initialize DynamoDB resource
dynamodb = get_dynamodb_resource()

def create_tables_if_not_exist():
    """Ensure that the required DynamoDB tables exist."""
    # Create Conversations table if it doesn't exist
    try:
        conversations_table = dynamodb.Table('Conversations')
        conversations_table.load()  # Check if the table exists
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("Table 'Conversations' not found, creating it now.")
            conversations_table = dynamodb.create_table(
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
            conversations_table.meta.client.get_waiter('table_exists').wait(TableName='Conversations')
            print("Table 'Conversations' created successfully.")
        else:
            print(f"Unexpected error: {e}")
            return None  # Indicate failure

    # Create Messages table if it doesn't exist
    try:
        messages_table = dynamodb.Table('Messages')
        messages_table.load()  # Check if the table exists
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("Table 'Messages' not found, creating it now.")
            messages_table = dynamodb.create_table(
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
            messages_table.meta.client.get_waiter('table_exists').wait(TableName='Messages')
            print("Table 'Messages' created successfully.")
        else:
            print(f"Unexpected error: {e}")
            return None  # Indicate failure

def create_conversation(customer_id):
    """Ensure that a conversation exists for the given customer_id.
    If not, create a new conversation item in the Conversations table.
    """
    # Ensure required tables exist
    create_tables_if_not_exist()

    # Check if customer_id exists in Conversations table
    conversations_table = dynamodb.Table('Conversations')
    response = conversations_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('customer_id').eq(customer_id)
    )
    if not response['Items']:
        # Create a new conversation item
        conversation_id = str(uuid.uuid4())  # Generate a new conversation_id
        conversations_table.put_item(
            Item={
                'conversation_id': conversation_id,
                'customer_id': customer_id,
                'vendor_id': 'your_vendor_id',  # Replace with actual vendorId logic
                'started_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_open': True,
                'assigned_user_id': None,
                'assigned_team_id': None,
                'colab_users': [],
            }
        )
        print(f"New conversation {conversation_id} created for customer_id {customer_id}.")
        return conversation_id  # Return the new conversation_id
    else:
        return response['Items'][0]['conversation_id']  # Return existing conversation_id

def send_whatsapp_message(to_phone_id, message):
    if not WA_ACCESS_TOKEN or not SPOUT_PHONE_NUMBER_ID:
        print("Error: Access token or phone number ID is not defined.")
        return {"error": "Missing credentials"}
    url = f"https://graph.facebook.com/v20.0/{SPOUT_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_ACCESS_TOKEN}", 
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone_id,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return {"error": str(e)}