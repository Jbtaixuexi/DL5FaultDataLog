from django.urls import path

from accounts import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.Flogin, name='login'),
    path('logout/', views.flogout, name='logout'),
    path('register/', views.register, name='register'),
]
