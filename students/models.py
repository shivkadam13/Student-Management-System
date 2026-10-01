from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Course(models.Model):
    """
    A course that students can be enrolled in, e.g. 'Computer Science'.

    One Course can have MANY Students (see the ForeignKey on Student
    below) - that's the "one course, many students" relationship.
    """
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="A short unique code, e.g. 'CS101'.",
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['course_name']

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Teacher(models.Model):
    """
    A teacher's profile. Linked one-to-one with a Django ``User`` -
    the User holds the login credentials (username/password), this
    model holds everything that's specific to being a teacher.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="A short unique staff ID, e.g. 'EMP001'.",
    )
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        name = self.user.get_full_name()
        return name if name else self.user.username


class Student(models.Model):
    """
    A student's profile. Linked one-to-one with a Django ``User`` -
    the User holds the login credentials, this model holds
    everything that's specific to being a student (course, roll
    number, and every academic record hangs off this via FKs below).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
    )
    roll_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="A unique roll number / student ID, e.g. 'STU2026001'.",
    )
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # on_delete=models.CASCADE means: if a Course is ever deleted,
    # all Students enrolled in it are deleted too. This keeps the
    # database consistent (no "orphan" students pointing at a course
    # that no longer exists).
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='students',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['roll_number']

    def __str__(self):
        return f"{self.full_name} ({self.roll_number})"

    @property
    def full_name(self):
        name = self.user.get_full_name()
        return name if name else self.user.username

    @property
    def email(self):
        return self.user.email

    def clean(self):
        # Model-level validation that runs no matter how the object
        # is saved (admin, forms, shell, etc.) - a nice safety net on
        # top of the form validation in forms.py.
        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError({'date_of_birth': "Date of birth cannot be in the future."})

    @property
    def attendance_percentage(self):
        """Present records / total records, rounded to 1 decimal. Used on the dashboard cards."""
        total = self.attendance_records.count()
        if total == 0:
            return None
        present = self.attendance_records.filter(status=Attendance.PRESENT).count()
        return round((present / total) * 100, 1)


class Attendance(models.Model):
    """One attendance record for one student on one date."""

    PRESENT = 'Present'
    ABSENT = 'Absent'

    STATUS_CHOICES = [
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PRESENT)

    # Which teacher marked it - optional, purely for an audit trail.
    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_marked',
    )

    class Meta:
        ordering = ['-date']
        # A student can only have ONE attendance record per date -
        # this stops accidental duplicate entries at the database
        # level (on top of the friendlier check in forms.py).
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"


class Mark(models.Model):
    """One subject's marks for one student."""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='marks',
    )
    subject_name = models.CharField(max_length=100)
    marks_obtained = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField(default=100)

    # Which teacher entered it - optional, purely for an audit trail.
    recorded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marks_recorded',
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.subject_name}: {self.marks_obtained}/{self.total_marks}"

    @property
    def percentage(self):
        """Used in templates as {{ mark.percentage }} - handy for display."""
        if self.total_marks == 0:
            return 0
        return round((self.marks_obtained / self.total_marks) * 100, 1)

    def clean(self):
        if self.marks_obtained is not None and self.total_marks is not None:
            if self.marks_obtained > self.total_marks:
                raise ValidationError({'marks_obtained': "Marks obtained cannot be greater than total marks."})


class Complaint(models.Model):
    """
    A complaint filed by a student. Students can only create and
    view their own complaints (see views_student.py) - only a
    teacher can change the status or add a response.
    """

    PENDING = 'Pending'
    IN_PROGRESS = 'In Progress'
    RESOLVED = 'Resolved'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (RESOLVED, 'Resolved'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='complaints',
    )
    subject = models.CharField(max_length=150)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING)
    teacher_response = models.TextField(blank=True)

    # Which teacher last actioned this complaint - optional.
    handled_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_complaints',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.subject} ({self.status})"


class Remark(models.Model):
    """A short note a teacher leaves on a student's record (e.g. praise, a concern, a reminder)."""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='remarks',
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        related_name='remarks_given',
    )
    remark_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.created_at:%Y-%m-%d}"
