from django.shortcuts import redirect
from functools import wraps

def hospital_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'HOSPITAL':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
