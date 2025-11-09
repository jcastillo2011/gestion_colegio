from model_students.models import SystemLog

def log_user_activity(request, action, description):
    """Registra la actividad del usuario en el sistema"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Solo registrar si hay usuario logueado
    if not user_type or not user_id:
        return
    
    # Obtener nombre del usuario
    if user_type == 'student':
        from model_students.models import Student
        try:
            user = Student.objects.get(ci=user_id)
            user_name = f"{user.name} {user.last_name}"
        except:
            user_name = "Usuario desconocido"
    elif user_type == 'teacher':
        from model_students.models import Teacher
        try:
            user = Teacher.objects.get(ci=user_id)
            user_name = f"{user.name} {user.last_name}"
        except:
            user_name = "Usuario desconocido"
    elif user_type == 'admin':
        from model_students.models import Admin
        try:
            user = Admin.objects.get(ci=user_id)
            user_name = f"{user.name} {user.last_name}"
        except:
            user_name = "Usuario desconocido"
    else:
        user_name = "Usuario desconocido"
    
    # Obtener IP
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    # Crear log
    try:
        SystemLog.objects.create(
            user_type=user_type,
            user_id=str(user_id),
            user_name=user_name,
            action=action,
            description=description,
            ip_address=ip_address or '127.0.0.1'
        )
    except Exception as e:
        print(f'Error al crear log: {e}')