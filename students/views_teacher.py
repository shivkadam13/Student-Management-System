from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .decorators import teacher_required
from .forms import (
    AttendanceForm,
    ComplaintUpdateForm,
    MarkForm,
    RemarkForm,
    StudentCredentialsForm,
    StudentProfileForm,
    StudentUserDetailsForm,
)
from .models import Attendance, Complaint, Course, Mark, Remark, Student


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@teacher_required
def dashboard_view(request):
    context = {
        'student_count': Student.objects.count(),
        'course_count': Course.objects.count(),
        'pending_complaints_count': Complaint.objects.filter(status=Complaint.PENDING).count(),
        'recent_marks': Mark.objects.select_related('student', 'student__user')[:5],
        'recent_remarks': Remark.objects.select_related('student', 'student__user')[:5],
    }
    return render(request, 'students/teacher/dashboard.html', context)


# ------------------------------------------------------------------
# Student list / search / filter
# ------------------------------------------------------------------

@teacher_required
def student_list_view(request):
    query = request.GET.get('q', '').strip()
    roll_number = request.GET.get('roll', '').strip()
    course_id = request.GET.get('course', '')

    students = Student.objects.select_related('user', 'course').all()

    if query:
        students = students.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
        )
    if roll_number:
        students = students.filter(roll_number__icontains=roll_number)
    if course_id:
        students = students.filter(course_id=course_id)

    context = {
        'students': students,
        'courses': Course.objects.all(),
        'query': query,
        'roll_number': roll_number,
        'selected_course_id': course_id,
    }
    return render(request, 'students/teacher/student_list.html', context)


@teacher_required
def student_detail_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    context = {
        'student': student,
        'attendance_records': student.attendance_records.all(),
        'marks': student.marks.all(),
        'complaints': student.complaints.all(),
        'remarks': student.remarks.all(),
    }
    return render(request, 'students/teacher/student_detail.html', context)


# ------------------------------------------------------------------
# Add / edit / delete a student (creates/updates the linked User too)
# ------------------------------------------------------------------

@teacher_required
def student_add_view(request):
    if request.method == 'POST':
        credentials_form = StudentCredentialsForm(request.POST)
        user_form = StudentUserDetailsForm(request.POST)
        profile_form = StudentProfileForm(request.POST)

        if credentials_form.is_valid() and user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.username = credentials_form.cleaned_data['username']
            user.set_password(credentials_form.cleaned_data['password1'])
            user.save()

            student = profile_form.save(commit=False)
            student.user = user
            student.save()

            messages.success(request, f"Student account created for {student.full_name}.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        credentials_form = StudentCredentialsForm()
        user_form = StudentUserDetailsForm()
        profile_form = StudentProfileForm()

    context = {
        'credentials_form': credentials_form,
        'user_form': user_form,
        'profile_form': profile_form,
        'heading': 'Add a New Student',
        'is_create': True,
    }
    return render(request, 'students/teacher/student_form.html', context)


@teacher_required
def student_edit_view(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        user_form = StudentUserDetailsForm(request.POST, instance=student.user)
        profile_form = StudentProfileForm(request.POST, instance=student)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Student details updated.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        user_form = StudentUserDetailsForm(instance=student.user)
        profile_form = StudentProfileForm(instance=student)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'heading': f'Edit {student.full_name}',
        'is_create': False,
        'student': student,
    }
    return render(request, 'students/teacher/student_form.html', context)


@teacher_required
def student_delete_view(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        user = student.user
        name = student.full_name
        student.delete()
        user.delete()  # also removes their ability to log in
        messages.success(request, f"{name} has been deleted.")
        return redirect('teacher_student_list')

    return render(request, 'students/teacher/student_confirm_delete.html', {'student': student})


# ------------------------------------------------------------------
# Marks
# ------------------------------------------------------------------

@teacher_required
def mark_add_view(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = MarkForm(request.POST)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.student = student
            mark.recorded_by = request.user.teacher_profile
            mark.save()
            messages.success(request, "Marks added.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = MarkForm()

    context = {'form': form, 'student': student, 'heading': f'Add Marks — {student.full_name}'}
    return render(request, 'students/teacher/mark_form.html', context)


@teacher_required
def mark_edit_view(request, pk):
    mark = get_object_or_404(Mark, pk=pk)
    student = mark.student

    if request.method == 'POST':
        form = MarkForm(request.POST, instance=mark)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks updated.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = MarkForm(instance=mark)

    context = {'form': form, 'student': student, 'heading': f'Edit Marks — {student.full_name}'}
    return render(request, 'students/teacher/mark_form.html', context)


@teacher_required
def mark_delete_view(request, pk):
    mark = get_object_or_404(Mark, pk=pk)
    student = mark.student

    if request.method == 'POST':
        mark.delete()
        messages.success(request, "Marks deleted.")
        return redirect('teacher_student_detail', pk=student.pk)

    context = {
        'heading': 'Delete Marks',
        'description': f"Delete the {mark.subject_name} marks for {student.full_name}? This cannot be undone.",
        'cancel_url': reverse('teacher_student_detail', args=[student.pk]),
    }
    return render(request, 'students/teacher/confirm_delete.html', context)


# ------------------------------------------------------------------
# Attendance
# ------------------------------------------------------------------

@teacher_required
def attendance_add_view(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = AttendanceForm(request.POST, student=student)
        if form.is_valid():
            record = form.save(commit=False)
            record.student = student
            record.marked_by = request.user.teacher_profile
            record.save()
            messages.success(request, "Attendance recorded.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = AttendanceForm(student=student)

    context = {'form': form, 'student': student, 'heading': f'Add Attendance — {student.full_name}'}
    return render(request, 'students/teacher/attendance_form.html', context)


@teacher_required
def attendance_edit_view(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    student = record.student

    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=record, student=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance updated.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = AttendanceForm(instance=record, student=student)

    context = {'form': form, 'student': student, 'heading': f'Edit Attendance — {student.full_name}'}
    return render(request, 'students/teacher/attendance_form.html', context)


@teacher_required
def attendance_delete_view(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    student = record.student

    if request.method == 'POST':
        record.delete()
        messages.success(request, "Attendance record deleted.")
        return redirect('teacher_student_detail', pk=student.pk)

    context = {
        'heading': 'Delete Attendance Record',
        'description': f"Delete the {record.date} attendance record for {student.full_name}? This cannot be undone.",
        'cancel_url': reverse('teacher_student_detail', args=[student.pk]),
    }
    return render(request, 'students/teacher/confirm_delete.html', context)


@teacher_required
def all_attendance_view(request):
    records = Attendance.objects.select_related('student', 'student__user')
    return render(request, 'students/teacher/attendance_list.html', {'records': records})


@teacher_required
def all_marks_view(request):
    records = Mark.objects.select_related('student', 'student__user')
    return render(request, 'students/teacher/mark_list.html', {'records': records})


# ------------------------------------------------------------------
# Complaints
# ------------------------------------------------------------------

@teacher_required
def complaint_list_view(request):
    status_filter = request.GET.get('status', '')
    complaints = Complaint.objects.select_related('student', 'student__user')
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'status_choices': Complaint.STATUS_CHOICES,
    }
    return render(request, 'students/teacher/complaint_list.html', context)


@teacher_required
def complaint_update_view(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.handled_by = request.user.teacher_profile
            updated.save()
            messages.success(request, "Complaint updated.")
            return redirect('teacher_complaint_list')
        messages.error(request, "Please fix the errors below.")
    else:
        form = ComplaintUpdateForm(instance=complaint)

    return render(request, 'students/teacher/complaint_update.html', {'form': form, 'complaint': complaint})


# ------------------------------------------------------------------
# Remarks
# ------------------------------------------------------------------

@teacher_required
def remark_add_view(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = RemarkForm(request.POST)
        if form.is_valid():
            remark = form.save(commit=False)
            remark.student = student
            remark.teacher = request.user.teacher_profile
            remark.save()
            messages.success(request, "Remark added.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = RemarkForm()

    context = {'form': form, 'student': student, 'heading': f'Add Remark — {student.full_name}'}
    return render(request, 'students/teacher/remark_form.html', context)


@teacher_required
def remark_edit_view(request, pk):
    remark = get_object_or_404(Remark, pk=pk)
    student = remark.student

    if request.method == 'POST':
        form = RemarkForm(request.POST, instance=remark)
        if form.is_valid():
            form.save()
            messages.success(request, "Remark updated.")
            return redirect('teacher_student_detail', pk=student.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = RemarkForm(instance=remark)

    context = {'form': form, 'student': student, 'heading': f'Edit Remark — {student.full_name}'}
    return render(request, 'students/teacher/remark_form.html', context)


@teacher_required
def remark_delete_view(request, pk):
    remark = get_object_or_404(Remark, pk=pk)
    student = remark.student

    if request.method == 'POST':
        remark.delete()
        messages.success(request, "Remark deleted.")
        return redirect('teacher_student_detail', pk=student.pk)

    context = {
        'heading': 'Delete Remark',
        'description': f"Delete this remark for {student.full_name}? This cannot be undone.",
        'cancel_url': reverse('teacher_student_detail', args=[student.pk]),
    }
    return render(request, 'students/teacher/confirm_delete.html', context)
