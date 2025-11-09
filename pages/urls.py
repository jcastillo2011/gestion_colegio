from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('classroom/', views.classroom, name='classroom'),
    path('manage-evaluations/', views.manage_evaluations, name='manage_evaluations'),
    path('create-evaluation/', views.create_evaluation, name='create_evaluation'),
    path('grade-evaluation/<int:eval_id>/', views.grade_evaluation, name='grade_evaluation'),
    path('delete-evaluation/<int:eval_id>/', views.delete_evaluation, name='delete_evaluation'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('my-subjects/', views.my_subjects, name='my_subjects'),
    path('subject/<str:subject_name>/', views.subject_detail, name='subject_detail'),
    path('teacher-subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('student-reports/', views.student_reports, name='student_reports'),
    path('student-report/<str:student_ci>/', views.generate_student_report, name='generate_student_report'),
    path('update-evaluations/', views.update_evaluations, name='update_evaluations'),
    path('logout/', views.logout_view, name='logout'),
    path('virtual-classroom/<int:course_id>/', views.virtual_classroom, name='virtual_classroom'),
    
    # URLs de Administrador
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('manage-grades/', admin_views.manage_grades, name='manage_grades'),
    path('manage-courses/', admin_views.manage_courses, name='manage_courses'),
    path('manage-users/', admin_views.manage_users, name='manage_users'),
    path('system-logs/', admin_views.system_logs, name='system_logs'),
    path('course-students/<int:course_id>/', admin_views.course_students, name='course_students'),
    path('course-students-pdf/<int:course_id>/', admin_views.course_students_pdf, name='course_students_pdf'),
    path('maintenance/', admin_views.maintenance, name='maintenance'),
]