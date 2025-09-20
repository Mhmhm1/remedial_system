from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models




# ----------------------------
# Subject model
# ----------------------------
class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ----------------------------
# ClassGroup model
# ----------------------------
class ClassGroup(models.Model):
    name = models.CharField(max_length=50)  # Form 1, Form 2, etc.

    def __str__(self):
        return self.name


# ----------------------------
# Teacher model
# ----------------------------
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, blank=True)
    class_groups = models.ManyToManyField(ClassGroup, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# ----------------------------
# Timetable model
# ----------------------------
class Timetable(models.Model):
    DAYS = [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
    ]

    subject_fk = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_groups = models.ManyToManyField(ClassGroup)
    day = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

   def __str__(self):
    if self.subject_fk:
        return f"{self.subject_fk.name} - {self.get_day_display()} {self.start_time.strftime('%H:%M')}"
    return f"Unnamed - {self.get_day_display()} {self.start_time.strftime('%H:%M')}"

# ----------------------------
# Week model
# ----------------------------
class Week(models.Model):
    number = models.PositiveIntegerField()  # Week 1, Week 2...
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Week {self.number} ({self.start_date} - {self.end_date})"


# ----------------------------
# LessonRecord model
class LessonRecord(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    week = models.ForeignKey(Week, on_delete=models.CASCADE)

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="lesson_records"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Attended", "Attended"),
            ("Not Attended", "Not Attended"),
        ],
        default="Pending"
    )

    # ✅ Add these back
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("Unpaid", "Unpaid"),
            ("Paid", "Paid"),
        ],
        default="Unpaid"
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.teacher} - {self.timetable} ({self.week})"
# ----------------------------
# lessons/models.py


class LessonRecord(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="created_lessons")

    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Attended", "Attended"),
            ("Not Attended", "Not Attended"),
        ],
        default="Pending"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("Unpaid", "Unpaid"),
            ("Paid", "Paid"),
        ],
        default="Unpaid"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=400)

    def save(self, *args, **kwargs):
        if self.amount is None:  # only replace if it's not set
            self.amount = 400
        super().save(*args, **kwargs)
