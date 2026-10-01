# Student Management System — Role-Based Portal (Django + PostgreSQL + Bootstrap)

A role-based Student Management System with separate **Student** and
**Teacher** portals, built on Django's own authentication system.

- **Login page** (the site's landing page) with two tabs: *Student Login*
  and *Teacher Login*.
- **Students** can only view their own profile, marks, attendance,
  complaints, and teacher remarks — and can file a new complaint. They
  cannot edit marks/attendance/remarks, and cannot see any other
  student's data, even by editing the URL.
- **Teachers** can view/search/filter all students, add new students,
  add/edit/delete marks and attendance, view and respond to complaints,
  and add/edit/delete remarks.
- Bootstrap 5 layout with a working light/dark mode toggle.

---

## 1. Folder structure

```
student_management/
├── manage.py
├── requirements.txt
├── .env.example
│
├── static/students/
│   ├── style.css                 Small custom layer on top of Bootstrap
│   └── theme.js                  Light/dark toggle (data-bs-theme)
│
├── student_management/           <- PROJECT package
│   ├── settings.py                LOGIN_URL / LOGOUT_REDIRECT_URL added
│   └── urls.py
│
└── students/                      <- APP package (all the logic)
    ├── models.py                  Student, Teacher, Course, Attendance, Mark, Complaint, Remark
    ├── forms.py                   Login, student-account, marks, attendance, complaint, remark forms
    ├── decorators.py              @student_required / @teacher_required
    ├── views_auth.py              login_view (2 tabs), logout_view
    ├── views_student.py           Read-only "my own data" views + file-a-complaint
    ├── views_teacher.py           Full CRUD for students/marks/attendance/complaints/remarks
    ├── urls.py
    ├── admin.py
    ├── tests.py                   19 tests covering auth + role access + CRUD
    ├── migrations/
    └── templates/students/
        ├── base.html               Bootstrap layout, role-aware navbar
        ├── login.html              Student/Teacher tabs
        ├── student/                dashboard, profile, marks, attendance, complaints, remarks
        └── teacher/                dashboard, student_list/detail/form, mark & attendance forms,
                                     complaint list/update, remark form, confirm-delete pages
```

---

## 2. How the role system works

There's still only **one** Django `User` model (with the normal
`username`/`password`) — roles come from which *profile* is attached to
that user:

- A `Student` row with `student.user = <User>` → that user is a student.
- A `Teacher` row with `teacher.user = <User>` → that user is a teacher.

`students/decorators.py` defines:

```python
@student_required   # 403s anyone without a Student profile
@teacher_required    # 403s anyone without a Teacher profile
```

Every view in `views_student.py` and `views_teacher.py` is wrapped in one
of these, on top of Django's own `login_required`. Critically, every
"my own data" view in `views_student.py` reads `request.user.student_profile`
directly — **there is no `<pk>` in any student-facing URL** — so there is
no ID for a student to tamper with in the address bar in the first place.

The login page (`/`) has two tabs that both post to the same view but
with a hidden `role` field. After Django authenticates the username/password,
the view double-checks that the account actually has the matching profile
(e.g. a student's credentials used on the *Teacher* tab are rejected with
"This account isn't a teacher account") before logging them in and
redirecting to the right dashboard.

---

## 3. Setup

### PostgreSQL

Same as before — create a database + user, then copy `.env.example` to
`.env` and fill in the values:

```bash
cp .env.example .env
```

### Install & run

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations   # no-op if you're using the included migration
python manage.py migrate
python manage.py createsuperuser  # for /admin/ — this account has neither
                                   # a Student nor Teacher profile, it's purely
                                   # for managing the database via /admin/
python manage.py runserver
```

Open **http://127.0.0.1:8000/** — you'll land on the login page.

### Run the test suite

```bash
python manage.py test students
```

This runs 19 tests covering: role-based redirects on login, students
being blocked from every teacher URL (and vice versa), a student's
dashboard only ever showing their own marks, and the teacher-side CRUD
for students/marks/attendance/complaints/remarks.

---

## 4. Creating a teacher account and a student account for testing

Accounts aren't self-service by design (per the requirements) — they're
created by an admin/teacher. Two ways to do it:

### Option A — Django admin (easiest)

1. `python manage.py createsuperuser`, then log into `/admin/`.
2. Under **Users**, click **Add User** and set a username + password
   for the teacher (e.g. `teacher1`). Save, then optionally fill in
   their first/last name and email on the next screen.
3. Under **Teachers**, click **Add Teacher**, pick that `User` from the
   dropdown, fill in the employee ID/department, and save.
4. Repeat steps 2–3 under **Users** / **Students** for the student
   account, picking a `Course` and roll number for them.

### Option B — Django shell (fast, scriptable)

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from students.models import Teacher, Student, Course

course = Course.objects.create(course_name="Computer Science", course_code="CS101")

# One teacher
t_user = User.objects.create_user(username="teacher1", password="TeachPass123", first_name="Jane", last_name="Doe", email="jane@example.com")
Teacher.objects.create(user=t_user, employee_id="EMP001", department="Computer Science")

# One student
s_user = User.objects.create_user(username="student1", password="StudentPass123", first_name="Alex", last_name="Kim", email="alex@example.com")
Student.objects.create(user=s_user, roll_number="STU2026001", course=course)
```

Now log in at `/` — `teacher1` / `TeachPass123` on the **Teacher Login**
tab, and `student1` / `StudentPass123` on the **Student Login** tab.

### Option C — from the Teacher portal itself

Once you have one teacher account (via A or B above), log in as that
teacher and use **Students → Add Student** in the UI — it creates the
student's `User` login and `Student` profile in the same form.

---

## 5. Sample test data

To populate enough data to see every dashboard card and page working
(attendance percentage, marks, complaints, remarks), run this in
`python manage.py shell` after creating the accounts above:

```python
import datetime
from students.models import Attendance, Mark, Complaint, Remark, Student, Teacher

student = Student.objects.get(roll_number="STU2026001")
teacher = Teacher.objects.get(employee_id="EMP001")

# Attendance - a mix of present/absent
for i, status in enumerate(["Present", "Present", "Absent", "Present", "Present"]):
    Attendance.objects.create(student=student, date=datetime.date(2026, 9, 1 + i), status=status, marked_by=teacher)

# Marks
Mark.objects.create(student=student, subject_name="Mathematics", marks_obtained=82, total_marks=100, recorded_by=teacher)
Mark.objects.create(student=student, subject_name="Physics", marks_obtained=74, total_marks=100, recorded_by=teacher)

# A complaint (student would normally file this themselves via the portal)
Complaint.objects.create(student=student, subject="Library access", description="Can't access the library after 6pm.")

# A remark from the teacher
Remark.objects.create(student=student, teacher=teacher, remark_text="Consistently submits assignments early.")
```

Then log in as `student1` to see the dashboard cards populated, or as
`teacher1` and open **Students → Alex Kim** to see everything on one page.

---

## 6. Manual test checklist

1. Log in on the **Student** tab with the teacher's credentials → rejected
   with "This account isn't a student account."
2. Log in as the student → redirected to `/student/dashboard/`, see the
   attendance %, latest marks, pending complaints, and recent remarks cards.
3. While logged in as the student, manually type `/teacher/dashboard/`
   into the address bar → **403 Forbidden**.
4. File a complaint from `/student/complaints/` → it appears in the list
   with a "Pending" badge; confirm there's no way to change its status
   from the student side.
5. Log out, log in as the **teacher** → land on `/teacher/dashboard/`.
6. Go to **Students**, search by name, then by roll number, then filter
   by course — each narrows the table.
7. Open the student's detail page → add a mark, add an attendance
   record, add a remark — confirm each appears immediately and the
   attendance percentage badge updates.
8. Try adding attendance for a date that already has a record for that
   student → friendly "already exists" error, not a crash.
9. Go to **Complaints**, open the one filed above, set status to
   *Resolved* and write a response → log back in as the student and
   confirm the response and new status are visible on `/student/complaints/`.
10. Toggle light/dark mode (icon in the navbar, top right) → refresh the
    page → theme persists.

---

## 7. Notes

- `DEBUG = True` is fine for learning/local use; set it to `False`
  (and configure `ALLOWED_HOSTS`) before any real deployment.
- Deleting a `Student` also deletes their `User` (so their login stops
  working) via `on_delete=models.CASCADE` on `Student.user`, and the
  view additionally deletes the `User` row explicitly for clarity.
- `Attendance.marked_by` and `Mark.recorded_by` use `on_delete=models.SET_NULL`
  — deleting a `Teacher` account doesn't delete the records they created,
  it just clears who created them.
