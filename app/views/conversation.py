from django.http import JsonResponse
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from drf_yasg import openapi
from app.utils.handle_response import handle_response
from app.helpers.dynamodb_helpers import get_conversations_table
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all conversations for a specific vendor",
    manual_parameters=[
        openapi.Parameter(
            'vendor_id', 
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            required=True, 
            description="Vendor ID to filter conversations"
        )
    ],
    responses={
        200: openapi.Response(
            description="Conversations retrieved successfully",
            examples={
                "application/json": {
                    "conversations": [
                        {
                            "conversationId": "12345",
                            "vendorId": "vendor123",
                            "customerId": "customer123",
                            "startedAt": "2023-10-01T12:00:00"
                        }
                    ]
                }
            }
        ),
        400: "Bad Request",
        500: "Internal Server Error"
    }
)
@api_view(['GET'])
def get_conversations_by_vendor(request):
    vendor_id = request.GET.get('vendor_id')
    if not vendor_id:
        return handle_response(message='vendor_id is required', status_code=status.HTTP_400_BAD_REQUEST)

    table = get_conversations_table()

    try:
        response = table.scan(
            FilterExpression=Attr('vendor_id').eq(vendor_id)
        )

        conversations = response.get('Items', [])
        return JsonResponse({'conversations': conversations}, status=status.HTTP_200_OK)
    except ClientError as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    operation_description="Assign a user and team to a specific conversation",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID of the conversation"),
            'assigned_user_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID of the user to assign"),
            'assigned_team_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID of the team to assign"),
        },
        required=['conversation_id'],
        description="conversation_id is required and at least one of assigned_user_id or assigned_team_id must be provided"
    ),
    responses={
        200: openapi.Response(
            description="User and team assigned successfully",
            examples={
                "application/json": {
                    "message": "User and team assigned successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "conversation_id is required and at least one of assigned_user_id or assigned_team_id must be provided"
                }
            }
        ),
        500: "Internal Server Error"
    }
)
@api_view(['POST'])
def assign_user_and_team_to_conversation(request):
    conversation_id = request.data.get('conversation_id')
    assigned_user_id = request.data.get('assigned_user_id')
    assigned_team_id = request.data.get('assigned_team_id')

    if not conversation_id or (not assigned_user_id and not assigned_team_id):
        return handle_response(message='conversation_id is required and at least one of assigned_user_id or assigned_team_id must be provided', status_code=status.HTTP_400_BAD_REQUEST)

    table = get_conversations_table()

    try:
        update_expression = []
        expression_attribute_values = {}
        
        if assigned_user_id:
            update_expression.append("assigned_user_id = :u")
            expression_attribute_values[':u'] = assigned_user_id
        if assigned_team_id:
            update_expression.append("assigned_team_id = :t")
            expression_attribute_values[':t'] = assigned_team_id
        
        update_expression_str = "set " + ", ".join(update_expression)

        table.update_item(
            Key={'conversation_id': conversation_id},
            UpdateExpression=update_expression_str,
            ExpressionAttributeValues=expression_attribute_values
        )
        return handle_response(message='User and/or team assigned successfully', status_code=status.HTTP_200_OK)
    except ClientError as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    operation_description="Change assigned user or team for a specific conversation",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID of the conversation"),
            'new_user_id': openapi.Schema(type=openapi.TYPE_STRING, description="New user ID to assign"),
            'new_team_id': openapi.Schema(type=openapi.TYPE_STRING, description="New team ID to assign"),
        },
        required=['conversation_id'],
        description="conversation_id is required, and at least one of new_user_id or new_team_id must be provided"
    ),
    responses={
        200: openapi.Response(
            description="User and/or team assigned successfully",
            examples={
                "application/json": {
                    "message": "User and/or team assigned successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "conversation_id is required and at least one of new_user_id or new_team_id must be provided"
                }
            }
        ),
        500: "Internal Server Error"
    }
)
@api_view(['POST'])
def change_assignment(request):
    conversation_id = request.data.get('conversation_id')
    new_user_id = request.data.get('new_user_id')
    new_team_id = request.data.get('new_team_id')

    if not conversation_id or (not new_user_id and not new_team_id):
        return handle_response(message='conversation_id is required and at least one of new_user_id or new_team_id must be provided', status_code=status.HTTP_400_BAD_REQUEST)

    table = get_conversations_table()

    try:
        update_expression = []
        expression_attribute_values = {}

        if new_user_id:
            update_expression.append("assigned_user_id = :u")
            expression_attribute_values[':u'] = new_user_id
        if new_team_id:
            update_expression.append("assigned_team_id = :t")
            expression_attribute_values[':t'] = new_team_id

        update_expression_str = "set " + ", ".join(update_expression)

        table.update_item(
            Key={'conversation_id': conversation_id},
            UpdateExpression=update_expression_str,
            ExpressionAttributeValues=expression_attribute_values
        )
        return handle_response(message='User and/or team assigned successfully', status_code=status.HTTP_200_OK)
    except ClientError as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    operation_description="Add users to the colab_users array for a specific conversation",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID of the conversation"),
            'user_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of user IDs to add"),
        },
        required=['conversation_id', 'user_ids'],
        description="conversation_id is required and user_ids is a list of user IDs to add"
    ),
    responses={
        200: openapi.Response(
            description="Users added successfully",
            examples={
                "application/json": {
                    "message": "Users added to colab_users successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "conversation_id is required and user_ids must be provided"
                }
            }
        ),
        500: "Internal Server Error"
    }
)
@api_view(['POST'])
def add_users_to_conversation(request):
    conversation_id = request.data.get('conversation_id')
    user_ids = request.data.get('user_ids', [])

    if not conversation_id or not user_ids:
        return handle_response(message='conversation_id is required and user_ids must be provided', status_code=status.HTTP_400_BAD_REQUEST)

    table = get_conversations_table()

    try:
        # Update the colab_users array
        table.update_item(
            Key={'conversation_id': conversation_id},
            UpdateExpression="SET colab_users = list_append(if_not_exists(colab_users, :empty_list), :user_ids)",
            ExpressionAttributeValues={
                ':user_ids': user_ids,
                ':empty_list': []
            }
        )
        return handle_response(message='Users added to colab_users successfully', status_code=status.HTTP_200_OK)
    except ClientError as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@swagger_auto_schema(
    method='post',
    operation_description="Remove users from the colab_users array for a specific conversation",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conversation_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID of the conversation"),
            'user_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of user IDs to remove"),
        },
        required=['conversation_id', 'user_ids'],
        description="conversation_id is required and user_ids is a list of user IDs to remove"
    ),
    responses={
        200: openapi.Response(
            description="Users removed successfully",
            examples={
                "application/json": {
                    "message": "Users removed from colab_users successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "conversation_id is required and user_ids must be provided"
                }
            }
        ),
        500: "Internal Server Error"
    }
)
@api_view(['POST'])
def remove_users_from_conversation(request):
    conversation_id = request.data.get('conversation_id')
    user_ids = request.data.get('user_ids', [])

    if not conversation_id or not user_ids:
        return handle_response(message='conversation_id is required and user_ids must be provided', status_code=status.HTTP_400_BAD_REQUEST)

    table = get_conversations_table()

    try:
        # Get the current colab_users
        response = table.get_item(Key={'conversation_id': conversation_id})
        colab_users = response.get('Item', {}).get('colab_users', [])

        # Remove the specified user_ids
        updated_colab_users = [user for user in colab_users if user not in user_ids]

        # Update the colab_users array
        table.update_item(
            Key={'conversation_id': conversation_id},
            UpdateExpression="SET colab_users = :updated_users",
            ExpressionAttributeValues={
                ':updated_users': updated_colab_users
            }
        )
        return handle_response(message='Users removed from colab_users successfully', status_code=status.HTTP_200_OK)
    except ClientError as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='put',
    operation_description="Set the is_open status for multiple conversations",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conversation_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING, description="ID of the conversation"),
                description="List of conversation IDs to update"
            ),
            'is_open': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="New status to set for the conversations"),
        },
        required=['conversation_ids', 'is_open'],
        description="conversation_ids is required and is_open is a boolean value"
    ),
    responses={
        200: openapi.Response(
            description="Statuses updated successfully",
            examples={
                "application/json": {
                    "message": "Conversation statuses updated successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "conversation_ids and is_open must be provided"
                }
            }
        ),
        500: "Internal Server Error"
    }
)
@api_view(['PUT'])
def set_multiple_conversation_statuses(request):
    conversation_ids = request.data.get('conversation_ids', [])
    is_open = request.data.get('is_open')

    if not conversation_ids or is_open is None:
        return handle_response(message='conversation_ids and is_open must be provided', status_code=status.HTTP_400_BAD_REQUEST)

    table = get_conversations_table()

    try:
        for conversation_id in conversation_ids:
            # Update the is_open field for each conversation
            table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression="SET is_open = :is_open",
                ExpressionAttributeValues={
                    ':is_open': is_open
                }
            )

        return handle_response(message='Conversation statuses updated successfully', status_code=status.HTTP_200_OK)
    except ClientError as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)