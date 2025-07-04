from django.urls import path
from . import views

app_name = 'faults'

urlpatterns = [
    path('search_fault_data/', views.search_fault_data, name='search_fault_data'),
]
