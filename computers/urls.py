# app/urls.py
from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('chatbot/', views.chatbot, name='chatbot'),
]