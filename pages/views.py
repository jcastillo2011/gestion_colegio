from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from model_students.models import Student, Teacher, Evaluation, Course, Punctuation, Admin
from utils.logger import log_user_activity

def home(request):
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a página de inicio')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_type = request.POST['user_type']
        
        if user_type == 'student':
            try:
                student = Student.objects.get(username=username, password=password)
                request.session['user_type'] = 'student'
                request.session['user_id'] = student.ci
                return redirect('dashboard')
            except Student.DoesNotExist:
                messages.error(request, 'Credenciales de estudiante incorrectas')
        
        elif user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(username=username, password=password)
                request.session['user_type'] = 'teacher'
                request.session['user_id'] = teacher.ci
                return redirect('dashboard')
            except Teacher.DoesNotExist:
                messages.error(request, 'Credenciales de profesor incorrectas')
        
        elif user_type == 'admin':
            try:
                admin = Admin.objects.get(username=username, password=password)
                request.session['user_type'] = 'admin'
                request.session['user_id'] = admin.ci
                return redirect('admin_dashboard')
            except Admin.DoesNotExist:
                messages.error(request, 'Credenciales de administrador incorrectas')
        
        else:
            messages.error(request, 'Selecciona un tipo de usuario válido')
    
    return render(request, 'registration/login.html')

def register(request):
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a registro de usuario')
    
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        ci = request.POST['ci']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'registration/register.html')
        
        # Determinar tipo de usuario automáticamente por email
        is_teacher = email.endswith('@profesor.edu') or email.endswith('@teacher.edu') or 'profesor' in email.lower()
        
        try:
            if is_teacher:
                Teacher.objects.create(
                    username=username,
                    name=username,
                    last_name='',
                    ci=ci,
                    email=email,
                    password=password
                )
                messages.success(request, 'Profesor registrado exitosamente')
            else:
                Student.objects.create(
                    username=username,
                    name=username,
                    last_name='',
                    ci=ci,
                    email=email,
                    password=password
                )
                messages.success(request, 'Estudiante registrado exitosamente')
            return redirect('home')
        except:
            messages.error(request, 'Error al registrar usuario. Verifique que el email y cédula no estén en uso')
    
    return render(request, 'registration/register.html')

def dashboard(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Verificar si el usuario está logueado
    if not user_type or not user_id:
        messages.error(request, 'Debes iniciar sesión para acceder al dashboard')
        return redirect('home')
    
    # Redirigir administradores a su dashboard específico
    if user_type == 'admin':
        return redirect('admin_dashboard')
    
    from django.utils import timezone
    
    if user_type == 'student':
        user_data = Student.objects.get(ci=user_id)
        # Solo puntuaciones del estudiante logueado
        evaluations = Punctuation.objects.filter(student=user_data).select_related('evaluation').order_by('-evaluation__date')
        # Calcular evaluaciones aprobadas (score >= 10)
        approved_evaluations = evaluations.filter(score__gte=10).count()
        # Contar materias del grado del estudiante
        courses_count = Course.objects.filter(grade=user_data.grade).count()
        # Próximas evaluaciones (futuras) del grado del estudiante
        upcoming_evaluations = Evaluation.objects.filter(
            course__grade=user_data.grade,
            date__gt=timezone.now()
        ).order_by('date')[:5]
    else:
        user_data = Teacher.objects.get(ci=user_id)
        # Solo evaluaciones de cursos asignados al profesor
        evaluations = Evaluation.objects.filter(course__teacher=user_data).order_by('-date')
        approved_evaluations = 0
        # Contar materias asignadas al profesor
        courses_count = Course.objects.filter(teacher=user_data).count()
        # Calcular total de estudiantes únicos en los grados de las materias del profesor
        teacher_courses = Course.objects.filter(teacher=user_data)
        total_students = Student.objects.filter(grade__in=teacher_courses.values('grade')).distinct().count()
        # Próximas evaluaciones del profesor
        upcoming_evaluations = Evaluation.objects.filter(
            course__teacher=user_data,
            date__gt=timezone.now()
        ).order_by('date')[:5]
    
    context = {
        'user_type': user_type,
        'user_data': user_data,
        'evaluations': evaluations,
        'approved_evaluations': approved_evaluations,
        'courses_count': courses_count,
        'upcoming_evaluations': upcoming_evaluations
    }
    
    # Agregar total_students solo para profesores
    if user_type == 'teacher':
        context['total_students'] = total_students
    
    return render(request, 'dashboard.html', context)

def update_evaluations(request):
    user_type = request.session.get('user_type')
    if not user_type or user_type != 'teacher':
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('home')
    
    if request.method == 'POST':
        updated_count = 0
        for key, value in request.POST.items():
            if key.startswith('score_'):
                eval_id = key.split('_')[1]
                evaluation = Evaluation.objects.get(id=eval_id)
                evaluation.score = value
                evaluation.save()
                updated_count += 1
        
        if updated_count > 0:
            log_user_activity(request, 'UPDATE', f'Actualizó {updated_count} puntuaciones')
        
        messages.success(request, 'Puntuaciones actualizadas correctamente')
    
    return redirect('classroom')

def classroom(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'student':
        user_data = Student.objects.get(ci=user_id)
        log_user_activity(request, 'VIEW', f'Visualizó ranking de estudiantes del grado {user_data.grade}')
        from django.db.models import Avg
        students = Student.objects.filter(grade=user_data.grade).annotate(
            promedio=Avg('punctuation__score')
        ).order_by('-promedio')
        return render(request, 'classroom.html', {
            'user_type': user_type,
            'user_data': user_data,
            'students': students
        })
    else:
        teacher = Teacher.objects.get(ci=user_id)
        
        # Obtener materias del profesor
        teacher_courses = Course.objects.filter(teacher=teacher)
        
        # Estadísticas generales
        from django.db.models import Avg, Count
        total_students = Student.objects.filter(grade__in=teacher_courses.values('grade')).distinct().count()
        total_evaluations = Evaluation.objects.filter(course__teacher=teacher).count()
        
        # Estudiantes por materia con promedios
        courses_data = []
        for course in teacher_courses:
            students = Student.objects.filter(grade=course.grade).annotate(
                promedio=Avg('punctuation__score', filter=models.Q(punctuation__evaluation__course=course))
            ).order_by('name', 'last_name')
            
            # Evaluaciones recientes de la materia
            recent_evaluations = Evaluation.objects.filter(course=course).order_by('-date')[:3]
            
            courses_data.append({
                'course': course,
                'students': students,
                'students_count': students.count(),
                'recent_evaluations': recent_evaluations
            })
        
        # Evaluaciones pendientes de calificar
        from django.utils import timezone
        pending_evaluations = []
        for course in teacher_courses:
            evaluations = Evaluation.objects.filter(course=course)
            for evaluation in evaluations:
                students_count = Student.objects.filter(grade=course.grade).count()
                graded_count = Punctuation.objects.filter(evaluation=evaluation).count()
                if graded_count < students_count:
                    pending_evaluations.append({
                        'evaluation': evaluation,
                        'pending_count': students_count - graded_count,
                        'total_count': students_count
                    })
        
        return render(request, 'classroom.html', {
            'user_type': user_type,
            'user_data': teacher,
            'courses_data': courses_data,
            'total_students': total_students,
            'total_evaluations': total_evaluations,
            'pending_evaluations': pending_evaluations[:5]  # Solo las 5 más recientes
        })

def manage_evaluations(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    if not user_type or user_type != 'teacher':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('home')
    
    teacher = Teacher.objects.get(ci=user_id)
    courses = Course.objects.filter(teacher=teacher)
    evaluations = Evaluation.objects.filter(course__teacher=teacher).order_by('-date')
    
    return render(request, 'manage_evaluations.html', {
        'user_type': user_type,
        'user_data': teacher,
        'teacher': teacher,
        'courses': courses,
        'evaluations': evaluations
    })

def create_evaluation(request):
    # Verificar si el usuario es profesor
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    if not user_type or user_type != 'teacher':
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            teacher = Teacher.objects.get(ci=user_id)
            course_id = request.POST['course_id']
            course = Course.objects.get(id=course_id, teacher=teacher)
            
            # Crear evaluación
            Evaluation.objects.create(
                date=request.POST['date'],
                subject=request.POST['subject'],
                type=request.POST['type'],
                course=course
            )
            messages.success(request, f'Evaluación creada para la materia {course.name_course}')
        except Exception as e:
            messages.error(request, f'Error al crear la evaluación: {str(e)}')
    
    return redirect('manage_evaluations')

def delete_evaluation(request, eval_id):
    # Verificar si el usuario es profesor
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    if not user_type or user_type != 'teacher':
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('home')
    
    try:
        teacher = Teacher.objects.get(ci=user_id)
        evaluation = Evaluation.objects.get(id=eval_id, course__teacher=teacher)
        evaluation.delete()
        messages.success(request, 'Evaluación eliminada exitosamente')
    except:
        messages.error(request, 'Error al eliminar la evaluación')
    
    return redirect('manage_evaluations')

def profile(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if not user_type or not user_id:
        return redirect('home')
    
    if user_type == 'student':
        user_data = Student.objects.get(ci=user_id)
    else:
        user_data = Teacher.objects.get(ci=user_id)
    
    return render(request, 'profile.html', {
        'user_type': user_type,
        'user_data': user_data
    })


    
def my_subjects(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Solo estudiantes pueden acceder
    if user_type != 'student':
        messages.error(request, 'Acceso denied')
        return redirect('dashboard')
    
    user_data = Student.objects.get(ci=user_id)
    
    log_user_activity(request, 'VIEW', f'Visualizó lista de materias del grado {user_data.grade}')
    
    # Obtener todas las materias del grado del estudiante
    all_courses = Course.objects.filter(grade=user_data.grade)
    
    # Obtener puntuaciones del estudiante
    punctuations = Punctuation.objects.filter(student=user_data).select_related('evaluation__course')
    
    # Inicializar datos de materias
    subjects_data = {}
    total_score = 0
    total_count = 0
    
    # Crear entrada para todas las materias del grado
    for course in all_courses:
        subjects_data[course.name_course] = {
            'course': course,
            'scores': [],
            'evaluations': [],
            'average': 0
        }
    
    # Agregar puntuaciones existentes
    for punctuation in punctuations:
        course_name = punctuation.evaluation.course.name_course
        if course_name in subjects_data:
            subjects_data[course_name]['scores'].append(float(punctuation.score))
            subjects_data[course_name]['evaluations'].append(punctuation.evaluation)
            total_score += float(punctuation.score)
            total_count += 1
            # Debug: imprimir información
            print(f"Materia: {course_name}, Nota: {punctuation.score}, Evaluación: {punctuation.evaluation.subject}")
    
    # Calcular promedios
    for subject in subjects_data.values():
        if subject['scores']:
            subject['average'] = sum(subject['scores']) / len(subject['scores'])
    
    overall_average = total_score / total_count if total_count > 0 else 0
    
    return render(request, 'my_subjects.html', {
        'user_type': user_type,
        'user_data': user_data,
        'subjects_data': subjects_data,
        'overall_average': overall_average
    })

def subject_detail(request, subject_name):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type != 'student':
        messages.error(request, 'Acceso denegado')
        return redirect('dashboard')
    
    user_data = Student.objects.get(ci=user_id)
    
    # Obtener el curso específico
    try:
        course = Course.objects.get(name_course=subject_name, grade=user_data.grade)
    except Course.DoesNotExist:
        messages.error(request, 'Materia no encontrada')
        return redirect('my_subjects')
    
    # Obtener puntuaciones del estudiante para esta materia
    punctuations = Punctuation.objects.filter(
        student=user_data,
        evaluation__course=course
    ).select_related('evaluation').order_by('evaluation__date')
    
    log_user_activity(request, 'VIEW', f'Visualizó calificaciones de materia: {subject_name}')
    
    # Calcular promedio
    scores = [float(p.score) for p in punctuations]
    average = sum(scores) / len(scores) if scores else 0
    
    return render(request, 'subject_detail.html', {
        'user_type': user_type,
        'user_data': user_data,
        'subject_name': subject_name,
        'course': course,
        'punctuations': punctuations,
        'average': average
    })

def grade_evaluation(request, eval_id):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type != 'teacher':
        messages.error(request, 'Acceso denegado')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(ci=user_id)
    evaluation = Evaluation.objects.get(id=eval_id, course__teacher=teacher)
    
    # Obtener estudiantes del grado de la materia
    students = Student.objects.filter(grade=evaluation.course.grade).order_by('name', 'last_name')
    
    if request.method == 'POST':
        for student in students:
            score_key = f'score_{student.ci}'
            if score_key in request.POST and request.POST[score_key]:
                score = float(request.POST[score_key])
                # Crear o actualizar puntuación
                punctuation, created = Punctuation.objects.get_or_create(
                    evaluation=evaluation,
                    student=student,
                    defaults={'score': score}
                )
                if not created:
                    punctuation.score = score
                    punctuation.save()
        
        log_user_activity(request, 'UPDATE', f'Registró notas para evaluación: {evaluation.subject}')
        messages.success(request, 'Notas registradas correctamente')
        return redirect('manage_evaluations')
    
    # Obtener puntuaciones existentes y agregar a estudiantes
    punctuations = Punctuation.objects.filter(evaluation=evaluation)
    scores_dict = {p.student.ci: p.score for p in punctuations}
    
    # Agregar score a cada estudiante
    students_with_scores = []
    for student in students:
        student.current_score = scores_dict.get(student.ci, '')
        students_with_scores.append(student)
    
    return render(request, 'grade_evaluation.html', {
        'user_type': user_type,
        'user_data': teacher,
        'evaluation': evaluation,
        'students': students_with_scores
    })

def student_reports(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'admin':
        admin_data = Admin.objects.get(ci=user_id)
        students = Student.objects.all().order_by('name', 'last_name')
        user_data = admin_data
    elif user_type == 'teacher':
        teacher = Teacher.objects.get(ci=user_id)
        teacher_courses = Course.objects.filter(teacher=teacher)
        students = Student.objects.filter(grade__in=teacher_courses.values('grade')).distinct().order_by('name', 'last_name')
        user_data = teacher
    else:
        messages.error(request, 'Acceso denegado')
        return redirect('dashboard')
    
    return render(request, 'student_reports.html', {
        'user_type': user_type,
        'user_data': user_data,
        'students': students
    })

def reset_password(request):
    if request.method == 'GET':
        log_user_activity(request, 'VIEW', 'Accedió a restablecer contraseña')
    
    if request.method == 'POST':
        username = request.POST['username']
        ci = request.POST['ci']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        # Validar que las contraseñas coincidan
        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'reset_password.html')
        
        # Validar longitud mínima
        if len(new_password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'reset_password.html')
        
        # Buscar usuario por username y cédula
        try:
            # Verificar si es estudiante
            student = Student.objects.get(username=username, ci=ci)
            student.password = new_password
            student.save()
            messages.add_message(request, messages.SUCCESS, 'Contraseña restablecida exitosamente')
            return render(request, 'reset_password.html')
        except Student.DoesNotExist:
            try:
                # Verificar si es profesor
                teacher = Teacher.objects.get(username=username, ci=ci)
                teacher.password = new_password
                teacher.save()
                messages.add_message(request, messages.SUCCESS, 'Contraseña restablecida exitosamente')
                return render(request, 'reset_password.html')
            except Teacher.DoesNotExist:
                try:
                    # Verificar si es administrador
                    admin = Admin.objects.get(username=username, ci=ci)
                    admin.password = new_password
                    admin.save()
                    messages.add_message(request, messages.SUCCESS, 'Contraseña restablecida exitosamente')
                    return render(request, 'reset_password.html')
                except Admin.DoesNotExist:
                    messages.error(request, 'Usuario no encontrado. Verifica tu nombre de usuario y cédula')
    
    return render(request, 'reset_password.html')

def generate_student_report(request, student_ci):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type not in ['teacher', 'admin']:
        messages.error(request, 'Acceso denegado')
        return redirect('dashboard')
    
    if user_type == 'admin':
        user_data = Admin.objects.get(ci=user_id)
    else:
        user_data = Teacher.objects.get(ci=user_id)
    
    student = Student.objects.get(ci=student_ci)
    
    # Obtener materias del grado del estudiante
    courses = Course.objects.filter(grade=student.grade)
    
    # Obtener calificaciones del estudiante
    report_data = []
    total_score = 0
    total_count = 0
    
    for course in courses:
        punctuations = Punctuation.objects.filter(
            student=student,
            evaluation__course=course
        ).select_related('evaluation')
        
        scores = [float(p.score) for p in punctuations]
        average = sum(scores) / len(scores) if scores else 0
        
        if scores:
            total_score += average
            total_count += 1
        
        report_data.append({
            'course': course,
            'punctuations': punctuations,
            'average': average,
            'status': 'Aprobado' if average >= 10 else 'Reprobado'
        })
    
    overall_average = total_score / total_count if total_count > 0 else 0
    
    if request.GET.get('pdf'):
        try:
            from django.http import HttpResponse
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.colors import HexColor, black, white
            from reportlab.lib.units import inch
            from datetime import datetime
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="boletin_{student.name}_{student.last_name}.pdf"'
            
            p = canvas.Canvas(response, pagesize=letter)
            width, height = letter
            
            # Colors
            primary_color = HexColor('#667eea')
            secondary_color = HexColor('#764ba2')
            
            # Header background
            p.setFillColor(primary_color)
            p.rect(0, height - 120, width, 120, fill=1, stroke=0)
            
            # Logo placeholder (circle)
            p.setFillColor(white)
            p.circle(80, height - 60, 30, fill=1, stroke=0)
            p.setFillColor(primary_color)
            p.setFont("Helvetica-Bold", 20)
            p.drawString(75, height - 65, "T")
            
            # Institution info
            p.setFillColor(white)
            p.setFont("Helvetica-Bold", 24)
            p.drawString(130, height - 45, "ThinkIt Academy")
            p.setFont("Helvetica", 12)
            p.drawString(130, height - 65, "Sistema de Gestion Academica")
            p.drawString(130, height - 80, "Excelencia en Educacion")
            
            # Document title
            p.setFillColor(black)
            p.setFont("Helvetica-Bold", 20)
            p.drawString(width/2 - 100, height - 150, "BOLETIN DE CALIFICACIONES")
            
            # Student info box
            p.setStrokeColor(primary_color)
            p.setLineWidth(2)
            p.rect(50, height - 250, width - 100, 80, fill=0, stroke=1)
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(70, height - 185, "INFORMACION DEL ESTUDIANTE")
            
            p.setFont("Helvetica", 11)
            p.drawString(70, height - 205, f"Nombre: {student.name} {student.last_name}")
            p.drawString(70, height - 220, f"Cedula: {student.ci}")
            p.drawString(300, height - 205, f"Grado: {student.grade}")
            p.drawString(300, height - 220, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
            p.drawString(300, height - 235, f"Promedio: {overall_average:.2f}")
            
            # Table header
            y = height - 290
            p.setFillColor(primary_color)
            p.rect(50, y - 20, width - 100, 25, fill=1, stroke=0)
            
            p.setFillColor(white)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(70, y - 12, "MATERIA")
            p.drawString(250, y - 12, "PROMEDIO")
            p.drawString(350, y - 12, "ESTADO")
            p.drawString(450, y - 12, "OBSERVACION")
            
            # Table content
            p.setFillColor(black)
            p.setFont("Helvetica", 10)
            y -= 35
            row_count = 0
            
            for data in report_data:
                if data['average'] > 0:
                    # Alternate row colors
                    if row_count % 2 == 0:
                        p.setFillColor(HexColor('#f8f9fa'))
                        p.rect(50, y - 15, width - 100, 20, fill=1, stroke=0)
                    
                    p.setFillColor(black)
                    p.drawString(70, y - 5, str(data['course'].name_course))
                    p.drawString(260, y - 5, f"{data['average']:.2f}")
                    
                    # Color-coded status
                    if data['average'] >= 10:
                        p.setFillColor(HexColor('#28a745'))
                    else:
                        p.setFillColor(HexColor('#dc3545'))
                    p.drawString(360, y - 5, str(data['status']))
                    
                    # Observation
                    p.setFillColor(black)
                    obs = "Excelente" if data['average'] >= 15 else "Bueno" if data['average'] >= 12 else "Regular" if data['average'] >= 10 else "Deficiente"
                    p.drawString(460, y - 5, obs)
                    
                    y -= 20
                    row_count += 1
            
            # Footer
            p.setFillColor(primary_color)
            p.rect(0, 0, width, 50, fill=1, stroke=0)
            p.setFillColor(white)
            p.setFont("Helvetica", 8)
            p.drawString(width/2 - 120, 25, "ThinkIt Academy - Sistema de Gestion Academica")
            p.drawString(width/2 - 140, 15, "www.thinkit.edu | contacto@thinkit.edu | Tel: (555) 123-4567")
            
            p.showPage()
            p.save()
            return response
        except Exception as e:
            messages.error(request, f'Error al generar PDF: {str(e)}')
            return redirect('student_reports')
    
    return render(request, 'student_report_detail.html', {
        'user_type': user_type,
        'user_data': user_data,
        'student': student,
        'report_data': report_data,
        'overall_average': overall_average
    })

def teacher_subjects(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Solo profesores pueden acceder
    if user_type != 'teacher':
        messages.error(request, 'Acceso denegado')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(ci=user_id)
    
    # Obtener materias asignadas al profesor
    courses = Course.objects.filter(teacher=teacher).order_by('grade', 'name_course')
    
    # Obtener estadísticas por materia
    subjects_data = []
    for course in courses:
        # Contar estudiantes del grado
        students_count = Student.objects.filter(grade=course.grade).count()
        
        # Contar evaluaciones de la materia
        evaluations_count = Evaluation.objects.filter(course=course).count()
        
        # Calcular promedio general de la materia
        from django.db.models import Avg
        avg_score = Punctuation.objects.filter(
            evaluation__course=course
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        # Próxima evaluación
        from django.utils import timezone
        next_evaluation = Evaluation.objects.filter(
            course=course,
            date__gt=timezone.now()
        ).order_by('date').first()
        
        subjects_data.append({
            'course': course,
            'students_count': students_count,
            'evaluations_count': evaluations_count,
            'average_score': round(avg_score, 2),
            'next_evaluation': next_evaluation
        })
    
    return render(request, 'teacher_subjects.html', {
        'user_type': user_type,
        'user_data': teacher,
        'subjects_data': subjects_data,
        'total_courses': len(subjects_data)
    })

def edit_profile(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if not user_type or not user_id:
        return redirect('home')
    
    if user_type == 'student':
        user_data = Student.objects.get(ci=user_id)
    else:
        user_data = Teacher.objects.get(ci=user_id)
    
    if request.method == 'POST':
        try:
            user_data.name = request.POST.get('name', user_data.name)
            user_data.last_name = request.POST.get('last_name', user_data.last_name)
            user_data.email = request.POST.get('email', user_data.email)
            
            if 'profile_photo' in request.FILES:
                user_data.profile_photo = request.FILES['profile_photo']
            
            user_data.save()
            messages.success(request, 'Perfil actualizado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
    
    return render(request, 'edit_profile.html', {
        'user_type': user_type,
        'user_data': user_data
    })

def logout_view(request):
    request.session.flush()
    return redirect('home') 

# ============ VISTAS DE ADMINISTRADOR ============

def admin_required(view_func):
    """Decorador para verificar que el usuario sea administrador"""
    def wrapper(request, *args, **kwargs):
        user_type = request.session.get('user_type')
        if user_type != 'admin':
            messages.error(request, 'Acceso denegado. Solo administradores.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_dashboard(request):
    from model_students.models import Grade
    admin_id = request.session.get('user_id')
    admin_data = Admin.objects.get(ci=admin_id)
    
    # Estadísticas generales
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_courses = Course.objects.count()
    total_grades = Grade.objects.count()
    
    # Datos recientes
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
    from model_students.models import Grade
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
    from model_students.models import Grade
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
                grade = Grade.objects.get(id=grade_id)
                teacher = Teacher.objects.get(ci=teacher_id) if teacher_id else None
                
                Course.objects.create(
                    name_course=name_course,
                    description=description,
                    grade=grade,
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
        
        elif action == 'assign_students':
            course_id = request.POST.get('course_id')
            student_ids = request.POST.getlist('student_ids')
            
            try:
                course = Course.objects.get(id=course_id)
                students = Student.objects.filter(ci__in=student_ids)
                course.students.set(students)
                messages.success(request, f'Estudiantes asignados a {course.name_course}')
            except Exception as e:
                messages.error(request, f'Error al asignar estudiantes: {str(e)}')
    
    courses = Course.objects.all().select_related('teacher')
    grades = Grade.objects.all()
    teachers = Teacher.objects.all()
    students = Student.objects.all()
    
    return render(request, 'admin/manage_courses.html', {
        'user_type': 'admin',
        'user_data': admin_data,
        'courses': courses,
        'grades': grades,
        'teachers': teachers,
        'students': students
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
                    from model_students.models import Grade
                    grade_id = request.POST.get('grade_id')
                    grade = Grade.objects.get(id=grade_id) if grade_id else None
                    
                    Student.objects.create(
                        username=username,
                        name=name,
                        last_name=last_name,
                        ci=ci,
                        email=email,
                        password=password,
                        grade=grade
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
    
    from model_students.models import Grade
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