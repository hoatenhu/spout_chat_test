from functools import wraps
from rest_framework.response import Response

# Simple in-memory cache
in_memory_cache = {}

def cache_results(timeout=300):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            query_params = request.GET.dict()
            
            # Dynamically get the view name or use the request path
            view_name = request.resolver_match.view_name  # Get the name of the view
            cache_key = f"{view_name}_{hash(frozenset(query_params.items()))}"

            # Check if there's a cached result for this key
            cached_result = in_memory_cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            # If no cache, call the view and store the result
            response = view_func(request, *args, **kwargs)
            in_memory_cache[cache_key] = response.data
            
            # Set a timer to clear this cache entry after `timeout` seconds
            def clear_cache():
                in_memory_cache.pop(cache_key, None)
            
            from threading import Timer
            Timer(timeout, clear_cache).start()
            
            return response
        return _wrapped_view
    return decorator
