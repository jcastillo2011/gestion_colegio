from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from model_students.models import Student, Teacher, Course, Admin, Grade
from utils.logger import log_user_activity
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import datetime
import os
import shutil
from django.conf import settings

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
                # Validar duplicados
                if Grade.objects.filter(name=name).exists():
                    messages.error(request, f'Ya existe un grado con el nombre "{name}"')
                elif Grade.objects.filter(level=level).exists():
                    messages.error(request, f'Ya existe un grado con el nivel {level}')
                else:
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
                
                # Validar duplicados excluyendo el registro actual
                if Grade.objects.filter(name=name).exclude(id=grade_id).exists():
                    messages.error(request, f'Ya existe un grado con el nombre "{name}"')
                elif Grade.objects.filter(level=level).exclude(id=grade_id).exists():
                    messages.error(request, f'Ya existe un grado con el nivel {level}')
                else:
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
                # Validar duplicados
                if Course.objects.filter(name_course=name_course, grade=int(grade_id)).exists():
                    messages.error(request, f'Ya existe la materia "{name_course}" en el grado {grade_id}')
                else:
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
                
                # Validar duplicados excluyendo el registro actual
                if Course.objects.filter(name_course=name_course, grade=int(grade_id)).exclude(id=course_id).exists():
                    messages.error(request, f'Ya existe la materia "{name_course}" en el grado {grade_id}')
                else:
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
                # Validar duplicados globales
                if (Student.objects.filter(ci=ci).exists() or 
                    Teacher.objects.filter(ci=ci).exists() or 
                    Admin.objects.filter(ci=ci).exists()):
                    messages.error(request, f'Ya existe un usuario con la cédula {ci}')
                elif (Student.objects.filter(username=username).exists() or 
                      Teacher.objects.filter(username=username).exists() or 
                      Admin.objects.filter(username=username).exists()):
                    messages.error(request, f'Ya existe un usuario con el nombre de usuario "{username}"')
                elif (Student.objects.filter(email=email).exists() or 
                      Teacher.objects.filter(email=email).exists() or 
                      Admin.objects.filter(email=email).exists()):
                    messages.error(request, f'Ya existe un usuario con el email {email}')
                else:
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
                # Validar duplicados excluyendo el usuario actual
                username_exists = (Student.objects.filter(username=username).exclude(ci=user_id).exists() or 
                                 Teacher.objects.filter(username=username).exclude(ci=user_id).exists() or 
                                 Admin.objects.filter(username=username).exclude(ci=user_id).exists())
                
                email_exists = (Student.objects.filter(email=email).exclude(ci=user_id).exists() or 
                              Teacher.objects.filter(email=email).exclude(ci=user_id).exists() or 
                              Admin.objects.filter(email=email).exclude(ci=user_id).exists())
                
                if username_exists:
                    messages.error(request, f'Ya existe un usuario con el nombre de usuario "{username}"')
                elif email_exists:
                    messages.error(request, f'Ya existe un usuario con el email {email}')
                else:
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

@admin_required
def course_students(request, course_id):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    try:
        course = Course.objects.get(id=course_id)
        students = Student.objects.filter(grade=course.grade)
        
        # Filtros
        search_name = request.GET.get('search_name', '')
        search_ci = request.GET.get('search_ci', '')
        
        if search_name:
            students = students.filter(name__icontains=search_name) | students.filter(last_name__icontains=search_name)
        if search_ci:
            students = students.filter(ci__icontains=search_ci)
            
        students = students.order_by('name', 'last_name')
        
        log_user_activity(request, 'VIEW', f'Consultó estudiantes de la materia: {course.name_course}')
        
        context = {
            'user_type': 'admin',
            'user_data': admin_data,
            'course': course,
            'students': students,
            'search_name': search_name,
            'search_ci': search_ci,
        }
        
        return render(request, 'admin/course_students.html', context)
        
    except Course.DoesNotExist:
        messages.error(request, 'La materia no existe')
        return redirect('manage_courses')

@admin_required
def course_students_pdf(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        students = Student.objects.filter(grade=course.grade)
        
        # Aplicar filtros
        search_name = request.GET.get('search_name', '')
        search_ci = request.GET.get('search_ci', '')
        
        if search_name:
            students = students.filter(name__icontains=search_name) | students.filter(last_name__icontains=search_name)
        if search_ci:
            students = students.filter(ci__icontains=search_ci)
            
        students = students.order_by('name', 'last_name')
        
        # Crear PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="estudiantes_{course.name_course}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph(f"<b>Estudiantes de {course.name_course}</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información del curso
        info = Paragraph(f"<b>Grado:</b> {course.grade} | <b>Profesor:</b> {course.teacher or 'Sin asignar'} | <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 20))
        
        # Tabla de estudiantes
        data = [['Nº', 'Nombre Completo', 'Cédula', 'Email']]
        for i, student in enumerate(students, 1):
            data.append([str(i), f"{student.name} {student.last_name}", student.ci, student.email])
        
        table = Table(data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Total de estudiantes
        total = Paragraph(f"<b>Total de estudiantes: {students.count()}</b>", styles['Normal'])
        elements.append(total)
        
        doc.build(elements)
        
        log_user_activity(request, 'EXPORT', f'Exportó PDF de estudiantes de {course.name_course}')
        return response
        
    except Course.DoesNotExist:
        messages.error(request, 'La materia no existe')
        return redirect('manage_courses')

@admin_required
def maintenance(request):
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a mantenimiento del sistema')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'backup':
            backup_path = request.POST.get('backup_path')
            if not backup_path:
                messages.error(request, 'Debe especificar la ruta de respaldo')
            else:
                try:
                    # Verificar que la ruta existe
                    if not os.path.exists(backup_path):
                        messages.error(request, 'La ruta especificada no existe')
                    else:
                        # Crear nombre del archivo de respaldo
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_filename = f'backup_aula_virtual_{timestamp}.db'
                        backup_full_path = os.path.join(backup_path, backup_filename)
                        
                        # Copiar la base de datos
                        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                        shutil.copy2(db_path, backup_full_path)
                        
                        log_user_activity(request, 'BACKUP', f'Respaldó base de datos en: {backup_full_path}')
                        messages.success(request, f'Respaldo creado exitosamente: {backup_filename}')
                        
                except Exception as e:
                    messages.error(request, f'Error al crear respaldo: {str(e)}')
        
        elif action == 'restore':
            restore_file = request.FILES.get('restore_file')
            if not restore_file:
                messages.error(request, 'Debe seleccionar un archivo de respaldo')
            else:
                try:
                    # Verificar extensión del archivo
                    if not restore_file.name.endswith('.db'):
                        messages.error(request, 'El archivo debe tener extensión .db')
                    else:
                        # Crear respaldo de seguridad antes de restaurar
                        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                        backup_current = os.path.join(settings.BASE_DIR, f'db_backup_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
                        shutil.copy2(db_path, backup_current)
                        
                        # Restaurar base de datos
                        with open(db_path, 'wb+') as destination:
                            for chunk in restore_file.chunks():
                                destination.write(chunk)
                        
                        log_user_activity(request, 'RESTORE', f'Restauró base de datos desde: {restore_file.name}')
                        messages.success(request, 'Base de datos restaurada exitosamente. Reinicie el servidor.')
                        
                except Exception as e:
                    messages.error(request, f'Error al restaurar: {str(e)}')
    
    # Obtener información de la base de datos actual
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    db_size = 0
    db_modified = None
    
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
        db_modified = datetime.fromtimestamp(os.path.getmtime(db_path))
    
    context = {
        'user_type': 'admin',
        'user_data': admin_data,
        'db_size': db_size,
        'db_modified': db_modified,
    }
    
    return render(request, 'admin/maintenance.html', context)