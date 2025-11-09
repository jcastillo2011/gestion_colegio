#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_base.settings')
django.setup()

from model_students.models import Grade, Admin

def create_initial_data():
    # Crear grados básicos
    grades_data = [
        {'name': 'Primer Grado', 'level': 1, 'description': 'Primer año de educación primaria'},
        {'name': 'Segundo Grado', 'level': 2, 'description': 'Segundo año de educación primaria'},
        {'name': 'Tercer Grado', 'level': 3, 'description': 'Tercer año de educación primaria'},
        {'name': 'Cuarto Grado', 'level': 4, 'description': 'Cuarto año de educación primaria'},
        {'name': 'Quinto Grado', 'level': 5, 'description': 'Quinto año de educación primaria'},
        {'name': 'Sexto Grado', 'level': 6, 'description': 'Sexto año de educación primaria'},
    ]
    
    for grade_data in grades_data:
        grade, created = Grade.objects.get_or_create(
            level=grade_data['level'],
            defaults={
                'name': grade_data['name'],
                'description': grade_data['description']
            }
        )
        if created:
            print(f"Grado creado: {grade.name}")
        else:
            print(f"Grado ya existe: {grade.name}")
    
    # Crear administrador por defecto
    admin, created = Admin.objects.get_or_create(
        username='admin',
        defaults={
            'name': 'Administrador',
            'last_name': 'Sistema',
            'position': 'Administrador General',
            'ci': 'ADMIN001',
            'email': 'admin@thinkit.edu',
            'password': 'admin123'
        }
    )
    
    if created:
        print(f"Administrador creado: {admin.username}")
    else:
        print(f"Administrador ya existe: {admin.username}")

if __name__ == '__main__':
    create_initial_data()
    print("Datos iniciales creados exitosamente!")