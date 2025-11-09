from django.shortcuts import render, redirect
from django.contrib import messages
from model_students.models import Student, Teacher, Course, Admin, Grade

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        user_type = request.session.get('user_type')
        if user_type != 'admin':
            messages.error(request, 'Acceso denegado. Solo administradores.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_dashboard(request):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_courses = Course.objects.count()
    total_grades = Grade.objects.count()
    
    recent_students = Student.objects.order_by('-ci')[:5]
    recent_teachers = Teacher.objects.order_by('-ci')[:5]
    
    context = {
        'user_type': 'admin',
        'user_data': admin_data,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_grades': total_grades,
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
    }
    
    return render(request, 'admin/dashboard.html', context)

@admin_required
def manage_grades(request):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            name = request.POST.get('name')
            level = request.POST.get('level')
            description = request.POST.get('description', '')
            
            try:
                Grade.objects.create(name=name, level=level, description=description)
                messages.success(request, f'Grado "{name}" creado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al crear grado: {str(e)}')
        
        elif action == 'delete':
            grade_id = request.POST.get('grade_id')
            try:
                grade = Grade.objects.get(id=grade_id)
                grade.delete()
                messages.success(request, 'Grado eliminado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al eliminar grado: {str(e)}')
    
    grades = Grade.objects.all().order_by('level')
    
    return render(request, 'admin/manage_grades.html', {
        'user_type': 'admin',
        'user_data': admin_data,
        'grades': grades
    })

@admin_required
def manage_courses(request):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            name_course = request.POST.get('name_course')
            description = request.POST.get('description', '')
            grade_id = request.POST.get('grade_id')
            teacher_id = request.POST.get('teacher_id')
            
            try:
                teacher = Teacher.objects.get(ci=teacher_id) if teacher_id else None
                
                Course.objects.create(
                    name_course=name_course,
                    description=description,
                    grade=int(grade_id),
                    teacher=teacher
                )
                messages.success(request, f'Materia "{name_course}" creada exitosamente')
            except Exception as e:
                messages.error(request, f'Error al crear materia: {str(e)}')
        
        elif action == 'delete':
            course_id = request.POST.get('course_id')
            try:
                course = Course.objects.get(id=course_id)
                course.delete()
                messages.success(request, 'Materia eliminada exitosamente')
            except Exception as e:
                messages.error(request, f'Error al eliminar materia: {str(e)}')
    
    courses = Course.objects.all().select_related('teacher')
    grades = Grade.objects.all()
    teachers = Teacher.objects.all()
    
    return render(request, 'admin/manage_courses.html', {
        'user_type': 'admin',
        'user_data': admin_data,
        'courses': courses,
        'grades': grades,
        'teachers': teachers,
    })

@admin_required
def manage_users(request):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_type = request.POST.get('user_type')
        
        if action == 'create':
            username = request.POST.get('username')
            name = request.POST.get('name')
            last_name = request.POST.get('last_name')
            ci = request.POST.get('ci')
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            try:
                if user_type == 'student':
                    grade_id = request.POST.get('grade_id')
                    
                    Student.objects.create(
                        username=username,
                        name=name,
                        last_name=last_name,
                        ci=ci,
                        email=email,
                        password=password,
                        grade=int(grade_id) if grade_id else 1
                    )
                    messages.success(request, f'Estudiante "{name} {last_name}" creado exitosamente')
                
                elif user_type == 'teacher':
                    Teacher.objects.create(
                        username=username,
                        name=name,
                        last_name=last_name,
                        ci=ci,
                        email=email,
                        password=password
                    )
                    messages.success(request, f'Profesor "{name} {last_name}" creado exitosamente')
                
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
        
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            try:
                if user_type == 'student':
                    Student.objects.get(ci=user_id).delete()
                elif user_type == 'teacher':
                    Teacher.objects.get(ci=user_id).delete()
                messages.success(request, 'Usuario eliminado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al eliminar usuario: {str(e)}')
    
    students = Student.objects.all()
    teachers = Teacher.objects.all()
    grades = Grade.objects.all()
    
    return render(request, 'admin/manage_users.html', {
        'user_type': 'admin',
        'user_data': admin_data,
        'students': students,
        'teachers': teachers,
        'grades': grades
    })