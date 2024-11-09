import boto3
from decouple import config

# Local testing: 
# dynamodb = boto3.resource(
#     'dynamodb',
#     region_name=config('DYNAMODB_REGION', default='ap-southeast-1'),
#     endpoint_url=config('DYNAMODB_ENDPOINT_URL', default='http://localhost:8002')
# )

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
    region_name=config('AWS_DEFAULT_REGION')
)

def get_dynamodb_resource():
    return dynamodb

def get_conversations_table():
    return dynamodb.Table('Conversations')
