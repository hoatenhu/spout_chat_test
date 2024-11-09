import time
from functools import wraps

from django.db import connection, reset_queries

def query_debugger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {len(connection.queries)}")
        print(f"Finished in : {(end - start):.2f}s")
        return result
    return wrapper