from drf_yasg import openapi

# swagger parameters
token_header = openapi.Parameter(
    'Authorization', 
    openapi.IN_HEADER, 
    description="Bearer token", 
    type=openapi.TYPE_STRING
)