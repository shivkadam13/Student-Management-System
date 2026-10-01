from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import StyledAuthenticationForm


def _redirect_for_role(user):
    """Send a just-logged-in user to the dashboard that matches their role."""
    if hasattr(user, 'teacher_profile'):
        return redirect('teacher_dashboard')
    if hasattr(user, 'student_profile'):
        return redirect('student_dashboard')
    # A superuser created via createsuperuser has neither profile -
    # send them to the admin site instead of a dashboard that doesn't exist.
    return redirect('/admin/')


def login_view(request):
    """
    The site's landing page. Shows two tabs - Student Login and
    Teacher Login - backed by the SAME Django authentication, but
    each tab double-checks that the account being used actually
    has the matching profile, so a student can't accidentally (or
    deliberately) log in through the teacher tab and vice versa.
    """
    if request.user.is_authenticated:
        return _redirect_for_role(request.user)

    student_form = StyledAuthenticationForm(prefix='student')
    teacher_form = StyledAuthenticationForm(prefix='teacher')
    active_tab = 'student'

    if request.method == 'POST':
        role = request.POST.get('role')
        active_tab = role if role in ('student', 'teacher') else 'student'

        if role == 'student':
            student_form = StyledAuthenticationForm(request, data=request.POST, prefix='student')
            if student_form.is_valid():
                user = student_form.get_user()
                if hasattr(user, 'student_profile'):
                    login(request, user)
                    return redirect('student_dashboard')
                student_form.add_error(None, "This account isn't a student account. Try the Teacher Login tab.")

        elif role == 'teacher':
            teacher_form = StyledAuthenticationForm(request, data=request.POST, prefix='teacher')
            if teacher_form.is_valid():
                user = teacher_form.get_user()
                if hasattr(user, 'teacher_profile'):
                    login(request, user)
                    return redirect('teacher_dashboard')
                teacher_form.add_error(None, "This account isn't a teacher account. Try the Student Login tab.")

    return render(request, 'students/login.html', {
        'student_form': student_form,
        'teacher_form': teacher_form,
        'active_tab': active_tab,
    })


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('login')
