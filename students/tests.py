import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Attendance, Complaint, Course, Mark, Remark, Student, Teacher


class RoleBasedAccessTests(TestCase):
    """
    The heart of this app's security model: a student can never reach
    a teacher-only page, and vice versa - not even by guessing a URL.
    """

    def setUp(self):
        self.course = Course.objects.create(course_name="Computer Science", course_code="CS101")

        self.teacher_user = User.objects.create_user(username="mrsmith", password="teacherpass123")
        self.teacher = Teacher.objects.create(user=self.teacher_user, employee_id="EMP001")

        self.student_user = User.objects.create_user(username="alice", password="studentpass123")
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="STU001",
            course=self.course,
            date_of_birth=datetime.date(2005, 1, 1),
        )

        # A second student, used to prove student #1 can't see their data.
        self.other_student_user = User.objects.create_user(username="bob", password="studentpass123")
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            roll_number="STU002",
            course=self.course,
        )

    def test_student_login_redirects_to_student_dashboard(self):
        response = self.client.post(reverse('login'), {
            'role': 'student',
            'student-username': 'alice',
            'student-password': 'studentpass123',
        })
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_teacher_login_redirects_to_teacher_dashboard(self):
        response = self.client.post(reverse('login'), {
            'role': 'teacher',
            'teacher-username': 'mrsmith',
            'teacher-password': 'teacherpass123',
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_student_cannot_log_in_through_teacher_tab(self):
        response = self.client.post(reverse('login'), {
            'role': 'teacher',
            'teacher-username': 'alice',
            'teacher-password': 'studentpass123',
        })
        self.assertEqual(response.status_code, 200)  # re-rendered with an error, no redirect
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('student_dashboard')}")

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.login(username='alice', password='studentpass123')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_teacher_student_list(self):
        self.client.login(username='alice', password='studentpass123')
        response = self.client.get(reverse('teacher_student_list'))
        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_access_student_dashboard(self):
        self.client.login(username='mrsmith', password='teacherpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_student_dashboard_only_shows_own_data(self):
        Mark.objects.create(student=self.student, subject_name="Math", marks_obtained=90, total_marks=100)
        Mark.objects.create(student=self.other_student, subject_name="Science", marks_obtained=40, total_marks=100)

        self.client.login(username='alice', password='studentpass123')
        response = self.client.get(reverse('student_marks'))

        self.assertContains(response, "Math")
        self.assertNotContains(response, "Science")

    def test_student_cannot_edit_another_students_data_via_teacher_url(self):
        # Even though the URL takes a <pk>, this whole path is
        # gated by @teacher_required, so a student hitting it
        # (with ANY pk, including their own) is blocked outright.
        self.client.login(username='alice', password='studentpass123')
        response = self.client.get(reverse('teacher_mark_add', args=[self.other_student.pk]))
        self.assertEqual(response.status_code, 403)

    def test_logout_requires_post(self):
        self.client.login(username='alice', password='studentpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)  # GET not allowed
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class TeacherWorkflowTests(TestCase):
    """Exercises the CRUD a teacher is meant to be able to do."""

    def setUp(self):
        self.course = Course.objects.create(course_name="Commerce", course_code="COM101")
        self.teacher_user = User.objects.create_user(username="mrsmith", password="teacherpass123")
        self.teacher = Teacher.objects.create(user=self.teacher_user, employee_id="EMP001")

        self.student_user = User.objects.create_user(username="alice", password="studentpass123")
        self.student = Student.objects.create(user=self.student_user, roll_number="STU001", course=self.course)

        self.client.login(username='mrsmith', password='teacherpass123')

    def test_teacher_can_add_a_student(self):
        response = self.client.post(reverse('teacher_student_add'), {
            'username': 'charlie',
            'password1': 'somepass123',
            'password2': 'somepass123',
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'email': 'charlie@example.com',
            'roll_number': 'STU003',
            'phone_number': '',
            'date_of_birth': '',
            'course': self.course.pk,
        })
        self.assertEqual(Student.objects.filter(roll_number='STU003').count(), 1)
        new_user = User.objects.get(username='charlie')
        self.assertTrue(new_user.check_password('somepass123'))

    def test_teacher_can_add_marks_for_a_student(self):
        response = self.client.post(reverse('teacher_mark_add', args=[self.student.pk]), {
            'subject_name': 'English',
            'marks_obtained': 88,
            'total_marks': 100,
        })
        self.assertEqual(Mark.objects.filter(student=self.student, subject_name='English').count(), 1)

    def test_teacher_can_add_and_edit_attendance(self):
        self.client.post(reverse('teacher_attendance_add', args=[self.student.pk]), {
            'date': '2026-09-01',
            'status': 'Present',
        })
        record = Attendance.objects.get(student=self.student, date='2026-09-01')
        self.assertEqual(record.status, 'Present')

        self.client.post(reverse('teacher_attendance_edit', args=[record.pk]), {
            'date': '2026-09-01',
            'status': 'Absent',
        })
        record.refresh_from_db()
        self.assertEqual(record.status, 'Absent')

    def test_duplicate_attendance_date_is_rejected(self):
        Attendance.objects.create(student=self.student, date=datetime.date(2026, 9, 1), status='Present')
        response = self.client.post(reverse('teacher_attendance_add', args=[self.student.pk]), {
            'date': '2026-09-01',
            'status': 'Absent',
        })
        self.assertEqual(Attendance.objects.filter(student=self.student).count(), 1)

    def test_teacher_can_update_a_complaint(self):
        complaint = Complaint.objects.create(student=self.student, subject="Noisy classroom", description="Too loud")
        self.client.post(reverse('teacher_complaint_update', args=[complaint.pk]), {
            'status': Complaint.RESOLVED,
            'teacher_response': 'Addressed with the class.',
        })
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.RESOLVED)
        self.assertEqual(complaint.handled_by, self.teacher)

    def test_teacher_can_add_a_remark(self):
        self.client.post(reverse('teacher_remark_add', args=[self.student.pk]), {
            'remark_text': 'Excellent participation this week.',
        })
        self.assertEqual(Remark.objects.filter(student=self.student).count(), 1)

    def test_teacher_can_search_students_by_roll_number(self):
        response = self.client.get(reverse('teacher_student_list'), {'roll': 'STU001'})
        self.assertContains(response, 'STU001')


class StudentSelfServiceTests(TestCase):
    """A student filing their own complaint - the one 'write' action students are allowed."""

    def setUp(self):
        self.course = Course.objects.create(course_name="Arts", course_code="ART101")
        self.student_user = User.objects.create_user(username="alice", password="studentpass123")
        self.student = Student.objects.create(user=self.student_user, roll_number="STU001", course=self.course)
        self.client.login(username='alice', password='studentpass123')

    def test_student_can_file_a_complaint(self):
        self.client.post(reverse('student_complaints'), {
            'subject': 'Broken projector',
            'description': 'The projector in room 4 has not worked all week.',
        })
        self.assertEqual(Complaint.objects.filter(student=self.student).count(), 1)

    def test_student_cannot_edit_complaint_status(self):
        # Nothing in the student portal even accepts a status field -
        # ComplaintForm only exposes subject/description.
        complaint = Complaint.objects.create(student=self.student, subject="Test", description="Test")
        self.client.post(reverse('student_complaints'), {
            'subject': 'Test',
            'description': 'Test',
            'status': Complaint.RESOLVED,  # attempted, should be ignored
        })
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.PENDING)
