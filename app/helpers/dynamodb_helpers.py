import boto3
from decouple import config

def get_conversations_table():
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=config('DYNAMODB_REGION', default='ap-southeast-1'),
        endpoint_url=config('DYNAMODB_ENDPOINT_URL', default='http://localhost:8002')
    )
    return dynamodb.Table('Conversations')
