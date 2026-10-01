from django.urls import path

from . import views_auth, views_student, views_teacher

urlpatterns = [
    # ---------------- Authentication ----------------
    path('', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),

    # ---------------- Student portal (own data only) ----------------
    path('student/dashboard/', views_student.dashboard_view, name='student_dashboard'),
    path('student/profile/', views_student.profile_view, name='student_profile'),
    path('student/marks/', views_student.marks_view, name='student_marks'),
    path('student/attendance/', views_student.attendance_view, name='student_attendance'),
    path('student/complaints/', views_student.complaints_view, name='student_complaints'),
    path('student/remarks/', views_student.remarks_view, name='student_remarks'),

    # ---------------- Teacher portal ----------------
    path('teacher/dashboard/', views_teacher.dashboard_view, name='teacher_dashboard'),

    path('teacher/students/', views_teacher.student_list_view, name='teacher_student_list'),
    path('teacher/students/add/', views_teacher.student_add_view, name='teacher_student_add'),
    path('teacher/students/<int:pk>/', views_teacher.student_detail_view, name='teacher_student_detail'),
    path('teacher/students/<int:pk>/edit/', views_teacher.student_edit_view, name='teacher_student_edit'),
    path('teacher/students/<int:pk>/delete/', views_teacher.student_delete_view, name='teacher_student_delete'),

    path('teacher/students/<int:pk>/marks/add/', views_teacher.mark_add_view, name='teacher_mark_add'),
    path('teacher/marks/<int:pk>/edit/', views_teacher.mark_edit_view, name='teacher_mark_edit'),
    path('teacher/marks/<int:pk>/delete/', views_teacher.mark_delete_view, name='teacher_mark_delete'),
    path('teacher/marks/', views_teacher.all_marks_view, name='teacher_mark_list'),

    path('teacher/students/<int:pk>/attendance/add/', views_teacher.attendance_add_view, name='teacher_attendance_add'),
    path('teacher/attendance/<int:pk>/edit/', views_teacher.attendance_edit_view, name='teacher_attendance_edit'),
    path('teacher/attendance/<int:pk>/delete/', views_teacher.attendance_delete_view, name='teacher_attendance_delete'),
    path('teacher/attendance/', views_teacher.all_attendance_view, name='teacher_attendance_list'),

    path('teacher/complaints/', views_teacher.complaint_list_view, name='teacher_complaint_list'),
    path('teacher/complaints/<int:pk>/update/', views_teacher.complaint_update_view, name='teacher_complaint_update'),

    path('teacher/students/<int:pk>/remarks/add/', views_teacher.remark_add_view, name='teacher_remark_add'),
    path('teacher/remarks/<int:pk>/edit/', views_teacher.remark_edit_view, name='teacher_remark_edit'),
    path('teacher/remarks/<int:pk>/delete/', views_teacher.remark_delete_view, name='teacher_remark_delete'),
]
