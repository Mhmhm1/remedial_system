from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    # Teacher views
    path("lesson/add/", views.add_lesson_teacher, name="add_lesson"),
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/update-profile-picture/", views.update_profile_picture, name="update_profile_picture"),
    path("mark_attended/<int:lesson_id>/", views.mark_attended, name="mark_attended"),
    path("student/payments/", views.student_payments, name="student_payments"),

    # AJAX endpoints
    path("ajax/load-timetables/", views.load_timetables, name="ajax_load_timetables"),
    path("ajax/teacher_subjects/", views.ajax_teacher_subjects, name="ajax_teacher_subjects"),
    path("filter_timetables/", views.get_timetables, name="filter_timetables"),
     path('student-payments/', views.student_payments, name='student_payments'),
    path('add-student-ajax/', views.add_student_ajax, name='add_student_ajax'),
    path('edit-student-ajax/<int:student_id>/', views.edit_student_ajax, name='edit_student_ajax'),
    path('delete-student-ajax/<int:student_id>/', views.delete_student_ajax, name='delete_student_ajax'),
    path('admin-payments/', views.admin_payments_dashboard, name='admin_payments'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
