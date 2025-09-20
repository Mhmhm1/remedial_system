# lessons/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings
import os
from django.http import JsonResponse
from .models import Teacher, Timetable, LessonRecord, Week, ClassGroup, Subject
from django.http import JsonResponse
from .models import Timetable
from django.http import JsonResponse

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
        return redirect('some_error_page')  # Or use a template showing a friendly message


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
    timetables = []

    if teacher_id:
        timetables = Timetable.objects.filter(teacher_id=teacher_id)

    data = [
        {
            "id": t.id,
            "text": f"{t.subject.name} - {t.day} {t.start_time.strftime('%H:%M')} "
                    f"({', '.join([c.name for c in t.class_groups.all()])})"
        }
        for t in timetables
    ]
    return JsonResponse(data, safe=False)
