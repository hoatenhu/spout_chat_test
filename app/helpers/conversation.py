from botocore.exceptions import ClientError
import boto3
import uuid
from datetime import datetime
from app.helpers.dynamodb_helpers import get_dynamodb_resource

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