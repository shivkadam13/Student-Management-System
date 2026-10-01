from django.contrib import admin

from .models import Attendance, Complaint, Course, Mark, Remark, Student, Teacher


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 1


class MarkInline(admin.TabularInline):
    model = Mark
    extra = 1


class ComplaintInline(admin.TabularInline):
    model = Complaint
    extra = 0
    readonly_fields = ('created_at',)


class RemarkInline(admin.TabularInline):
    model = Remark
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name')
    search_fields = ('course_code', 'course_name')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'employee_id', 'department', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'roll_number', 'email', 'phone_number', 'course', 'date_of_birth')
    list_filter = ('course',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'roll_number')
    inlines = [AttendanceInline, MarkInline, ComplaintInline, RemarkInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__roll_number')


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_name', 'marks_obtained', 'total_marks', 'recorded_by')
    list_filter = ('subject_name',)
    search_fields = ('student__user__first_name', 'student__user__last_name', 'subject_name')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'status', 'handled_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__user__first_name', 'student__user__last_name', 'subject')


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'created_at')
    search_fields = ('student__user__first_name', 'student__user__last_name')
