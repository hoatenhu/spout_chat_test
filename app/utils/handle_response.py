
from rest_framework.response import Response
from rest_framework import status

def handle_response(data=None, message=None, status_code=status.HTTP_200_OK):
    response_data = {
        "message": message,
        "data": data,
        "code": status_code
    }
    return Response(response_data, status=status_code)
