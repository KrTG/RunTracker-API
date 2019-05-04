from django.http.response import HttpResponse
from django.http.response import HttpResponseForbidden
from django.http.response import HttpResponseNotAllowed

from functools import wraps

def login_required(func):
    """
    Decorator for throwing an 403 error when user is not logged in
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:            
            return HttpResponseForbidden("You must be logged in")
        else:
            return func(request, *args, **kwargs)
        
    return wrapper

def require_http_methods(request_method_list):
    """
    Decorator to make a view only accept particular request methods.  Usage::

        @require_http_methods(["GET", "POST"])
        def my_view(request):
            # I can assume now that only GET or POST requests make it this far
            # ...

    Note that request methods should be in uppercase.
    """
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if request.method == "OPTIONS":
                response = HttpResponse()
                response['allow'] = ','.join(request_method_list)
                return response
            if request.method not in request_method_list:              
                return HttpResponseNotAllowed(request_method_list, "Method '{}' not allowed".format(request.method))
            return func(request, *args, **kwargs)
        return inner
    return decorator