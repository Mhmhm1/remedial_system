from django.contrib import admin
from .models import Subject, ClassGroup, Teacher, Timetable, Week, LessonRecord
from django.contrib.admin import AdminSite
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.urls import path
from django.shortcuts import render
from .models import Student, StudentPayment



class MyAdminSite(AdminSite):
    site_header = "Remedial System Admin"     # Top left banner
    site_title = "Remedial Admin Portal"      # Browser tab
    index_title = "Welcome to the Admin Dashboard"  # Dashboard title


# ----------------------------
# Subject Admin
# ----------------------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# ----------------------------
# ClassGroup Admin
# ----------------------------

@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "class_teacher")  # Show class teacher in the list
    search_fields = ("name", "class_teacher__user__username", "class_teacher__user__first_name", "class_teacher__user__last_name")
    change_list_template = "admin/lessons/classgroup/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "payments-dashboard/",
                self.admin_site.admin_view(self.payments_dashboard),
                name="admin_payments"
            ),
        ]
        return custom_urls + urls

    def payments_dashboard(self, request):
        students = Student.objects.all()
        payments = StudentPayment.objects.all()

        return render(request, "admin/lessons/payments_dashboard.html", {
            "students": students,
            "payments": payments,
        })




# ----------------------------
# Teacher Admin
# ----------------------------
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_subjects', 'is_class_teacher')  # show is_class_teacher
    list_editable = ('is_class_teacher',)  # allow inline editing in list view
    filter_horizontal = ('subjects', 'class_groups')
    search_fields = ('user__first_name', 'user__last_name', 'subjects__name', 'class_groups__name')

    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    get_subjects.short_description = 'Subjects'

# ----------------------------
# Timetable Admin
# ----------------------------
@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject_fk', 'teacher', 'day', 'start_time', 'end_time')
    filter_horizontal = ('class_groups',)
    list_filter = ('day', 'teacher',)
    search_fields = ('subject_fk__name', 'teacher__user__first_name', 'teacher__user__last_name', 'class_groups__name')

    def get_classes(self, obj):
        return ", ".join([c.name for c in obj.class_groups.all()])
    get_classes.short_description = 'Classes'


# ----------------------------
# Week Admin
# ----------------------------
@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'start_date', 'end_date', 'created_at')
    search_fields = ('number',)


# ----------------------------
# Custom filter for class in LessonRecord
# ----------------------------
class ClassGroupFilter(admin.SimpleListFilter):
    title = 'Class'
    parameter_name = 'class_group'

    def lookups(self, request, model_admin):
        classes = ClassGroup.objects.all()
        return [(c.id, c.name) for c in classes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(timetable__class_groups__id=self.value())
        return queryset


# ----------------------------
# LessonRecord form
# ----------------------------
class LessonRecordForm(forms.ModelForm):
    class Meta:
        model = LessonRecord
        fields = ['created_by', 'timetable', 'week', 'status', 'payment_status', 'amount']
        labels = {
            'created_by': 'Teacher',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['timetable'].queryset = Timetable.objects.none()

        if 'created_by' in self.data:
            try:
                teacher_id = int(self.data.get('created_by'))
                self.fields['timetable'].queryset = Timetable.objects.filter(teacher_id=teacher_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.timetable:
            self.fields['timetable'].queryset = Timetable.objects.filter(
                teacher=self.instance.timetable.teacher
            )


# ----------------------------
# LessonRecord admin
# ----------------------------
@admin.register(LessonRecord)
class LessonRecordAdmin(admin.ModelAdmin):
    form = LessonRecordForm
    list_display = ('id', 'get_teacher', 'timetable', 'week', 'status', 'payment_status', 'amount')
    list_filter = ('week', 'timetable__teacher', 'status', 'payment_status')

    class Media:
        js = ('lessons/js/lessonrecord.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # pass current user id into the created_by widget
        form.base_fields['created_by'].widget.attrs['data-current-user'] = request.user.id
        return form

    def save_model(self, request, obj, form, change):
        teacher_from_form = form.cleaned_data.get('created_by')
        if teacher_from_form:
            obj.created_by = teacher_from_form
        elif obj.timetable and not obj.created_by:
            obj.created_by = obj.timetable.teacher
        super().save_model(request, obj, form, change)

    def get_teacher(self, obj):
        if obj.created_by:
            return obj.created_by.user.get_full_name()
        elif obj.timetable and obj.timetable.teacher:
            return obj.timetable.teacher.user.get_full_name()
        return ''
    get_teacher.short_description = "Teacher"


# ----------------------------
# Custom Admin Site
# ----------------------------
admin_site = MyAdminSite(name='myadmin')
admin_site.register(Subject, SubjectAdmin)
admin_site.register(ClassGroup, ClassGroupAdmin)
admin_site.register(Teacher, TeacherAdmin)
admin_site.register(Timetable, TimetableAdmin)
admin_site.register(Week, WeekAdmin)
admin_site.register(LessonRecord, LessonRecordAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
