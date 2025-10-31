from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-evaluations/', views.update_evaluations, name='update_evaluations'),
    path('logout/', views.logout_view, name='logout'),
]