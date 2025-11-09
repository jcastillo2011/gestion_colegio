from django.shortcuts import render, redirect
from django.contrib import messages
from model_students.models import Student, Teacher, Course, Admin, Grade
from utils.logger import log_user_activity

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
    
    log_user_activity(request, 'VIEW', 'Accedió al dashboard de administrador')
    
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
    
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a gestión de grados')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            name = request.POST.get('name')
            level = request.POST.get('level')
            description = request.POST.get('description', '')
            
            try:
                Grade.objects.create(name=name, level=level, description=description)
                log_user_activity(request, 'CREATE', f'Creó grado: {name}')
                messages.success(request, f'Grado "{name}" creado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al crear grado: {str(e)}')
        
        elif action == 'update':
            grade_id = request.POST.get('grade_id')
            name = request.POST.get('name')
            level = request.POST.get('level')
            description = request.POST.get('description', '')
            
            try:
                grade = Grade.objects.get(id=grade_id)
                old_name = grade.name
                grade.name = name
                grade.level = level
                grade.description = description
                grade.save()
                
                log_user_activity(request, 'UPDATE', f'Actualizó grado: {old_name} → {name}')
                messages.success(request, f'Grado "{name}" actualizado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al actualizar grado: {str(e)}')
        
        elif action == 'delete':
            grade_id = request.POST.get('grade_id')
            try:
                grade = Grade.objects.get(id=grade_id)
                grade_name = grade.name
                grade.delete()
                log_user_activity(request, 'DELETE', f'Eliminó grado: {grade_name}')
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
    
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a gestión de materias')
    
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
                
                log_user_activity(request, 'CREATE', f'Creó materia: {name_course}')
                messages.success(request, f'Materia "{name_course}" creada exitosamente')
            except Exception as e:
                messages.error(request, f'Error al crear materia: {str(e)}')
        
        elif action == 'update':
            course_id = request.POST.get('course_id')
            name_course = request.POST.get('name_course')
            description = request.POST.get('description', '')
            grade_id = request.POST.get('grade_id')
            teacher_id = request.POST.get('teacher_id')
            
            try:
                course = Course.objects.get(id=course_id)
                old_name = course.name_course
                course.name_course = name_course
                course.description = description
                course.grade = int(grade_id)
                course.teacher = Teacher.objects.get(ci=teacher_id) if teacher_id else None
                course.save()
                
                log_user_activity(request, 'UPDATE', f'Actualizó materia: {old_name} → {name_course}')
                messages.success(request, f'Materia "{name_course}" actualizada exitosamente')
            except Exception as e:
                messages.error(request, f'Error al actualizar materia: {str(e)}')
        
        elif action == 'delete':
            course_id = request.POST.get('course_id')
            try:
                course = Course.objects.get(id=course_id)
                course_name = course.name_course
                course.delete()
                
                log_user_activity(request, 'DELETE', f'Eliminó materia: {course_name}')
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
def system_logs(request):
    from model_students.models import SystemLog
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    log_user_activity(request, 'VIEW', 'Accedió a logs del sistema')
    
    # Filtros
    user_type_filter = request.GET.get('user_type', '')
    action_filter = request.GET.get('action', '')
    
    logs = SystemLog.objects.all()
    
    if user_type_filter:
        logs = logs.filter(user_type=user_type_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    logs = logs.order_by('-timestamp')[:100]  # Últimos 100 logs
    
    return render(request, 'admin/system_logs.html', {
        'user_type': 'admin',
        'user_data': admin_data,
        'logs': logs,
        'user_type_filter': user_type_filter,
        'action_filter': action_filter,
    })

@admin_required
def manage_users(request):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a gestión de usuarios')
    
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
                    log_user_activity(request, 'CREATE', f'Creó estudiante: {name} {last_name}')
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
                    
                    log_user_activity(request, 'CREATE', f'Creó profesor: {name} {last_name}')
                    messages.success(request, f'Profesor "{name} {last_name}" creado exitosamente')
                
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
        
        elif action == 'update':
            user_id = request.POST.get('user_id')
            username = request.POST.get('username')
            name = request.POST.get('name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            
            try:
                if user_type == 'student':
                    student = Student.objects.get(ci=user_id)
                    old_name = f'{student.name} {student.last_name}'
                    student.username = username
                    student.name = name
                    student.last_name = last_name
                    student.email = email
                    if request.POST.get('grade_id'):
                        student.grade = int(request.POST.get('grade_id'))
                    student.save()
                    
                    log_user_activity(request, 'UPDATE', f'Actualizó estudiante: {old_name} → {name} {last_name}')
                    
                elif user_type == 'teacher':
                    teacher = Teacher.objects.get(ci=user_id)
                    old_name = f'{teacher.name} {teacher.last_name}'
                    teacher.username = username
                    teacher.name = name
                    teacher.last_name = last_name
                    teacher.email = email
                    teacher.save()
                    
                    log_user_activity(request, 'UPDATE', f'Actualizó profesor: {old_name} → {name} {last_name}')
                    
                messages.success(request, 'Usuario actualizado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al actualizar usuario: {str(e)}')
        
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            try:
                if user_type == 'student':
                    student = Student.objects.get(ci=user_id)
                    student_name = f'{student.name} {student.last_name}'
                    student.delete()
                    
                    log_user_activity(request, 'DELETE', f'Eliminó estudiante: {student_name}')
                    
                elif user_type == 'teacher':
                    teacher = Teacher.objects.get(ci=user_id)
                    teacher_name = f'{teacher.name} {teacher.last_name}'
                    teacher.delete()
                    
                    log_user_activity(request, 'DELETE', f'Eliminó profesor: {teacher_name}')
                    
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