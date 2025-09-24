# lessons/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

from django.db.models import Sum, F, Count, ExpressionWrapper, FloatField
from decimal import Decimal, InvalidOperation
import os

from .models import (
    Teacher,
    Timetable,
    LessonRecord,
    Week,
    ClassGroup,
    Subject,
    Student,
    StudentPayment,
)


TERM_FEE = 1500

def home(request):
    return render(request, "lessons/home.html")


def debug_load_timetables(request):
    return JsonResponse({
        "timetables": [
            {"id": 1, "text": "Dummy Timetable A"},
            {"id": 2, "text": "Dummy Timetable B"},
            {"id": 3, "text": "Dummy Timetable C"},
        ]
    })


def debug_load_timetables(request):
    return JsonResponse({
        "timetables": [
            {"id": 1, "text": "Dummy Timetable A"},
            {"id": 2, "text": "Dummy Timetable B"},
            {"id": 3, "text": "Dummy Timetable C"},
        ]
    })


# ---------- AJAX: timetables by teacher + week (used in admin JS) ----------

@login_required
def get_timetables(request):
    teacher_id = request.GET.get("teacher")
    week_id = request.GET.get("week")

    qs = Timetable.objects.none()
    if teacher_id:
        qs = Timetable.objects.filter(teacher_id=teacher_id)
        if week_id:
            used_ids = LessonRecord.objects.filter(
                week_id=week_id,
                timetable__in=qs
            ).values_list("timetable_id", flat=True)
            qs = qs.exclude(id__in=used_ids)

    data = [
        {
            "id": t.id,
            "display": f"{t.subject} - {t.day} {t.start_time.strftime('%H:%M')} "
                       f"({', '.join(c.name for c in t.class_groups.all())})"
        }
        for t in qs
    ]
    return JsonResponse({"timetables": data})

# ---------- Teacher dashboard ----------
@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('home')

    context = {"teacher": teacher}
    

    # Filters from GET parameters
    selected_week = request.GET.get("week")
    selected_class = request.GET.get("class_group")
    selected_subject = request.GET.get("subject")

    # Base queryset for lessons of this teacher
    lessons = LessonRecord.objects.filter(timetable__teacher=teacher)

    if selected_week:
        lessons = lessons.filter(week_id=selected_week)
    if selected_class:
        lessons = lessons.filter(timetable__class_groups__id=selected_class)
    if selected_subject:
        lessons = lessons.filter(timetable__subject__id=selected_subject)

    # Statistics
    total_lessons = lessons.count()
    attended = lessons.filter(status__iexact="Attended").count()
    not_attended = lessons.filter(status__iexact="Not Attended").count()
    pending = lessons.filter(status__iexact="Pending").count()

    paid = lessons.filter(payment_status__iexact="Paid").count()
    unpaid = lessons.filter(payment_status__iexact="Unpaid").count()

    total_paid_amount = lessons.filter(payment_status__iexact="Paid").aggregate(
        Sum("amount")
    )["amount__sum"] or 0

    total_unpaid_amount = lessons.filter(payment_status__iexact="Unpaid").aggregate(
        Sum("amount")
    )["amount__sum"] or 0

    # Lists for filters
    weeks = Week.objects.all()
    classes = ClassGroup.objects.all()
    subjects = Subject.objects.all()
    timetables = Timetable.objects.filter(teacher=teacher)
    other_teachers = Teacher.objects.exclude(id=teacher.id)

    context = {
        "teacher": teacher,
        "lessons": lessons,
        "weeks": weeks,
        "classes": classes,
        "subjects": subjects,
        "timetables": timetables,
        "other_teachers": other_teachers,
        "selected_week": selected_week,
        "selected_class": selected_class,
        "selected_subject": selected_subject,
        "total_lessons": total_lessons,
        "attended": attended,
        "not_attended": not_attended,
        "pending": pending,
        "paid": paid,
        "unpaid": unpaid,
        "total_paid_amount": total_paid_amount,
        "total_unpaid_amount": total_unpaid_amount,
    }

    return render(request, "lessons/teacher_dashboard.html", context)

# ---------- Update profile picture ----------
@login_required
def update_profile_picture(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == "POST":
        if request.FILES.get('profile_picture'):
            if teacher.profile_picture:
                old_path = os.path.join(settings.MEDIA_ROOT, teacher.profile_picture.name)
                if os.path.exists(old_path):
                    os.remove(old_path)
            teacher.profile_picture = request.FILES['profile_picture']
            teacher.save()
        elif 'delete_picture' in request.POST:
            if teacher.profile_picture:
                old_path = os.path.join(settings.MEDIA_ROOT, teacher.profile_picture.name)
                if os.path.exists(old_path):
                    os.remove(old_path)
            teacher.profile_picture = None
            teacher.save()
    return redirect('teacher_dashboard')


# ---------- Mark attended (teacher) ----------
@login_required
def mark_attended(request, lesson_id):
    lesson = get_object_or_404(LessonRecord, id=lesson_id)
    teacher = get_object_or_404(Teacher, user=request.user)
    if lesson.timetable.teacher != teacher and lesson.swapped_with != teacher:
        return JsonResponse({'error': 'Not allowed'}, status=403)
    lesson.status = "Pending"
    lesson.created_by = teacher
    lesson.save()
    return redirect("teacher_dashboard")


# ---------- Teacher add lesson ----------
from .forms import TeacherLessonForm

@login_required
def add_lesson_teacher(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == "POST":
        form = TeacherLessonForm(request.POST, teacher=teacher)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.created_by = teacher
            lesson.status = "Pending"
            lesson.payment_status = "Unpaid"
            # ❌ remove lesson.amount = 0
            exists = LessonRecord.objects.filter(
                timetable=lesson.timetable, week=lesson.week
            ).exists()
            if exists:
                form.add_error(None, "This lesson has already been scheduled for this week.")
                return render(request, "lessons/add_lesson_teacher.html", {"form": form})
            lesson.save()
            return redirect("teacher_dashboard")
    else:
        form = TeacherLessonForm(teacher=teacher)
    return render(request, "lessons/add_lesson_teacher.html", {"form": form})



# ---------- Teacher AJAX to list own timetables ----------
@login_required
def ajax_teacher_subjects(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    timetables = Timetable.objects.filter(teacher=teacher)
    subjects = [
        {
            'id': t.id,
            'subject': t.subject,
            'class_groups': ', '.join([c.name for c in t.class_groups.all()])
        }
        for t in timetables
    ]
    return JsonResponse({'subjects': subjects})
 # ---------- AJAX: load timetables (simple dropdown for admin/teacher) ----------

@login_required
def load_timetables(request):
    teacher_id = request.GET.get("teacher")
    timetables = Timetable.objects.filter(teacher_id=teacher_id) if teacher_id else []

    data = [
        {
            "id": t.id,
            "subject": t.subject_fk.name if t.subject_fk else "Unnamed",
            "day": t.get_day_display(),
            "start_time": t.start_time.strftime("%H:%M"),
            "end_time": t.end_time.strftime("%H:%M"),
        }
        for t in timetables
    ]
    return JsonResponse(data, safe=False)


@login_required
def student_payments(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    if not teacher.is_class_teacher:
        return redirect('teacher_dashboard')

    class_groups = teacher.class_groups.all()
    selected_class_id = request.GET.get("class_group", "")
    students = Student.objects.filter(class_group_id=selected_class_id) if selected_class_id else []

    # Compute statistics
    total_students = students.count()
    total_fee_per_student = Decimal('1500.00')  # assuming each term fee is 1500
    total_paid = sum(s.amount_paid for s in students)
    total_unpaid = total_students * total_fee_per_student - total_paid
    fully_paid = sum(1 for s in students if s.amount_paid >= total_fee_per_student)
    partial_paid = sum(1 for s in students if 0 < s.amount_paid < total_fee_per_student)

    # Record payments
    if request.method == "POST":
        for student in students:
            amount_str = request.POST.get(f"amount_{student.id}")
            if amount_str:
                try:
                    amount = Decimal(amount_str)  # Use Decimal to match amount_paid type
                    if amount > 0:
                        StudentPayment.objects.create(
                            student=student,
                            amount=amount,
                            recorded_by=teacher,
                            term="Term 1"
                        )
                        student.amount_paid = amount  # replace with new value
                         student.save()

                except (InvalidOperation, ValueError):
                    continue
        return redirect(f"{request.path}?class_group={selected_class_id}")

    context = {
        "class_groups": class_groups,
        "students": students,
        "selected_class_id": selected_class_id,
        "total_students": total_students,
        "total_paid": total_paid,
        "total_unpaid": total_unpaid,
        "fully_paid": fully_paid,
        "partial_paid": partial_paid,
        "total_fee_per_student": total_fee_per_student,
    }
    return render(request, "lessons/student_payments.html", context)

    context = {
        "class_groups": class_groups,
        "students": students,
        "selected_class_id": selected_class_id,
        # Statistics
        "total_students": total_students,
        "total_paid": total_paid,
        "total_unpaid": total_unpaid,
        "fully_paid": fully_paid,
        "partial_paid": partial_paid,
        "total_fee_per_student": total_fee_per_student,
    }
    return render(request, "lessons/student_payments.html", context)
@login_required
@csrf_exempt
def add_student_ajax(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        admission_number = request.POST.get("admission_number")
        class_group_id = request.POST.get("class_group")
        class_group = get_object_or_404(ClassGroup, id=class_group_id)

        student = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            admission_number=admission_number,
            class_group=class_group
        )
        return JsonResponse({
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "balance": f"{student.balance:.2f}"
        })


@login_required
@csrf_exempt
def edit_student_ajax(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        student.first_name = request.POST.get("first_name", student.first_name)
        student.last_name = request.POST.get("last_name", student.last_name)
        student.admission_number = request.POST.get("admission_number", student.admission_number)
        student.save()
        return JsonResponse({
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}"
        })


@login_required
@csrf_exempt
def delete_student_ajax(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        student.delete()
        return JsonResponse({"success": True, "id": student_id})
        

@staff_member_required
def admin_payments(request):
    selected_class_id = request.GET.get("class")
    selected_class_obj = None

    # All classes
    class_groups = ClassGroup.objects.all()

    # Student queryset (filtered if a class is chosen)
    students = Student.objects.all()
    if selected_class_id:
        try:
            selected_class_obj = ClassGroup.objects.get(id=selected_class_id)
            students = students.filter(class_group=selected_class_obj)
        except ClassGroup.DoesNotExist:
            selected_class_obj = None  # fallback if invalid ID is passed

    # Global totals
    total_paid = students.aggregate(total=Sum("amount_paid"))["total"] or 0
    total_fees = students.aggregate(total=Sum("term_fee"))["total"] or 0
    total_unpaid = total_fees - total_paid

    # Count statuses
    total_students = students.count()
    fully_paid = students.filter(amount_paid__gte=F("term_fee")).count()
    unpaid = students.filter(amount_paid=0).count()
    partial = total_students - fully_paid - unpaid

    # Per-class stats (for summary table)
    class_stats = class_groups.annotate(
        total_students=Count("students"),
        total_paid=Sum("students__amount_paid"),
        total_fees=Sum("students__term_fee"),
    )

    context = {
        "class_groups": class_groups,
        "students": students,
        "selected_class_id": selected_class_id,
        "selected_class_obj": selected_class_obj,

        # global totals
        "total_students": total_students,
        "total_paid": total_paid,
        "total_fees": total_fees,
        "total_unpaid": total_unpaid,
        "fully_paid": fully_paid,
        "unpaid": unpaid,
        "partial": partial,

        # per-class summary
        "class_stats": class_stats,
    }
    return render(request, "lessons/admin_payments.html", context)
