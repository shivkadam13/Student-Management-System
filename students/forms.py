from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Attendance, Complaint, Mark, Remark, Student


# ----------------------------------------------------------------------
# A tiny helper so every text/number/date/select input gets Bootstrap's
# "form-control" (or "form-select") class without repeating it on every
# single widget below.
# ----------------------------------------------------------------------
def _bootstrapify(fields):
    for field in fields.values():
        widget = field.widget
        css_class = 'form-select' if isinstance(widget, forms.Select) else 'form-control'
        existing = widget.attrs.get('class', '')
        widget.attrs['class'] = f"{existing} {css_class}".strip()


# ----------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------

class StyledAuthenticationForm(AuthenticationForm):
    """Django's built-in login form, just styled for Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })


# ----------------------------------------------------------------------
# Teacher-side: creating / editing a student
# ----------------------------------------------------------------------

class StudentCredentialsForm(forms.Form):
    """
    Only used when a teacher creates a brand-new student account.
    Collects the login username + password - kept separate from
    StudentProfileForm because these fields live on Django's User
    model, not on Student, and only make sense at creation time
    (editing a student later doesn't touch their password here).
    """
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        if password1 and len(password1) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")
        return cleaned_data


class StudentUserDetailsForm(forms.ModelForm):
    """The parts of a student's account that live on Django's User model."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        _bootstrapify(self.fields)


class StudentProfileForm(forms.ModelForm):
    """The parts of a student's account that live on the Student model."""

    class Meta:
        model = Student
        fields = ['roll_number', 'phone_number', 'date_of_birth', 'course']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number', '').strip()
        if not roll_number:
            raise forms.ValidationError("Please enter a roll number.")
        qs = Student.objects.filter(roll_number__iexact=roll_number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("That roll number is already in use.")
        return roll_number

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            return phone
        digits_only = phone.lstrip('+')
        if not digits_only.isdigit():
            raise forms.ValidationError("Phone number should contain digits only (an optional '+' at the start is fine).")
        if not (7 <= len(digits_only) <= 15):
            raise forms.ValidationError("Phone number should be between 7 and 15 digits long.")
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob


# ----------------------------------------------------------------------
# Teacher-side: marks & attendance
# ----------------------------------------------------------------------

class MarkForm(forms.ModelForm):
    """Used by a teacher to add or edit one subject's marks for a student."""

    class Meta:
        model = Mark
        fields = ['subject_name', 'marks_obtained', 'total_marks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_subject_name(self):
        subject_name = self.cleaned_data.get('subject_name', '').strip()
        if not subject_name:
            raise forms.ValidationError("Please enter a subject name.")
        return subject_name

    def clean(self):
        cleaned_data = super().clean()
        marks_obtained = cleaned_data.get('marks_obtained')
        total_marks = cleaned_data.get('total_marks')
        if marks_obtained is not None and total_marks is not None:
            if marks_obtained > total_marks:
                raise forms.ValidationError("Marks obtained cannot be greater than total marks.")
        return cleaned_data


class AttendanceForm(forms.ModelForm):
    """
    Used by a teacher to add or edit one attendance record. The
    `student` is NOT one of the form's fields - the view sets it
    directly (see views_teacher.py) so a record can only ever be
    attached to the student whose page the teacher is on.
    """

    class Meta:
        model = Attendance
        fields = ['date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, student=None, **kwargs):
        # Passed in from the view so clean() below can check for a
        # duplicate date for THIS student specifically.
        self.student = student
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.localdate():
            raise forms.ValidationError("Attendance date cannot be in the future.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        if self.student and date:
            existing = Attendance.objects.filter(student=self.student, date=date)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    "An attendance record already exists for this student on this date."
                )
        return cleaned_data


# ----------------------------------------------------------------------
# Complaints & remarks
# ----------------------------------------------------------------------

class ComplaintForm(forms.ModelForm):
    """Used by a STUDENT to file a new complaint. Once submitted, only a teacher can update it."""

    class Meta:
        model = Complaint
        fields = ['subject', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject:
            raise forms.ValidationError("Please enter a subject for your complaint.")
        return subject

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise forms.ValidationError("Please describe your complaint.")
        return description


class ComplaintUpdateForm(forms.ModelForm):
    """Used by a TEACHER to change a complaint's status and/or write a response."""

    class Meta:
        model = Complaint
        fields = ['status', 'teacher_response']
        widgets = {
            'teacher_response': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)


class RemarkForm(forms.ModelForm):
    """Used by a TEACHER to leave a remark on a student's record."""

    class Meta:
        model = Remark
        fields = ['remark_text']
        widgets = {
            'remark_text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_remark_text(self):
        text = self.cleaned_data.get('remark_text', '').strip()
        if not text:
            raise forms.ValidationError("Please write a remark before saving.")
        return text
