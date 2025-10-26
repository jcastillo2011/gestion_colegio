from django.contrib import admin
from .models import Student, Teacher, Course, Evaluation
# Register your models here.

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name_student', 'ci', 'email')
    search_fields = ('name_student', 'email', 'ci')

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name_teacher', 'ci', 'email')
    search_fields = ('name_teacher', 'email', 'ci')

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name_course', 'teacher')
    search_fields = ('name_course', 'teacher__name_teacher')

class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('date', 'subject', 'type', 'score', 'course', 'student')
    search_fields = ('subject', 'type', 'course__name_course', 'student__name_student')

admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Evaluation, EvaluationAdmin)