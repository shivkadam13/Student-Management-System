from django.contrib import messages
from django.shortcuts import redirect, render

from .decorators import student_required
from .forms import ComplaintForm
from .models import Complaint

# ------------------------------------------------------------------
# Every view below reads `request.user.student_profile` - there is
# NO <pk> anywhere in these URLs. That's deliberate: a student can't
# be shown someone else's data by editing the address bar, because
# there is no student ID in the URL for them to edit in the first
# place. Combined with @student_required (which 403s anyone without
# a Student profile), this is what satisfies "students can only see
# their own records, even if they change the URL".
# ------------------------------------------------------------------


@student_required
def dashboard_view(request):
    student = request.user.student_profile
    context = {
        'student': student,
        'attendance_percentage': student.attendance_percentage,
        'recent_marks': student.marks.all()[:5],
        'pending_complaints_count': student.complaints.filter(status=Complaint.PENDING).count(),
        'recent_remarks': student.remarks.all()[:3],
    }
    return render(request, 'students/student/dashboard.html', context)


@student_required
def profile_view(request):
    return render(request, 'students/student/profile.html', {'student': request.user.student_profile})


@student_required
def marks_view(request):
    marks = request.user.student_profile.marks.all()
    return render(request, 'students/student/marks.html', {'marks': marks})


@student_required
def attendance_view(request):
    student = request.user.student_profile
    records = student.attendance_records.all()
    context = {
        'records': records,
        'attendance_percentage': student.attendance_percentage,
    }
    return render(request, 'students/student/attendance.html', context)


@student_required
def complaints_view(request):
    student = request.user.student_profile

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = student
            complaint.save()
            messages.success(request, "Your complaint has been submitted.")
            return redirect('student_complaints')
        messages.error(request, "Please fix the errors below.")
    else:
        form = ComplaintForm()

    context = {
        'complaints': student.complaints.all(),
        'form': form,
    }
    return render(request, 'students/student/complaints.html', context)


@student_required
def remarks_view(request):
    remarks = request.user.student_profile.remarks.all()
    return render(request, 'students/student/remarks.html', {'remarks': remarks})
