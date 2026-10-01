"""
Role-based access control.

Django's own `login_required` only checks that *someone* is logged
in - it says nothing about *which* role they have. These decorators
add that second check on top, so a logged-in student can never
open a teacher-only view (or vice versa) even by typing the URL
directly into the browser.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def student_required(view_func):
    """
    Only allow a logged-in user who has a Student profile through.
    Anyone else (anonymous, or a teacher) gets a 403 Forbidden.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'student_profile'):
            raise PermissionDenied("This page is only available to students.")
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_required(view_func):
    """
    Only allow a logged-in user who has a Teacher profile through.
    Anyone else (anonymous, or a student) gets a 403 Forbidden.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'teacher_profile'):
            raise PermissionDenied("This page is only available to teachers.")
        return view_func(request, *args, **kwargs)
    return wrapper
