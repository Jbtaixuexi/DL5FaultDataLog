from django.urls import path
from . import views

app_name = 'faults'

urlpatterns = [
    path('search_fault_data/', views.search_fault_data, name='search_fault_data'),
    path('add_fault_data/accepted_list/', views.accepter_list, name='accepted_list'),
    path('add_fault_data/', views.add_fault_data, name='add_fault_data'),
    path('notify_accepted/', views.notify_accepted, name='notify_accepted'),
    path('getVehicles/', views.vehicle_list, name='vehicle_list'),
    path('get-systems/', views.get_systems, name='get_systems'),
    path('get-all-categories/', views.get_all_categories, name='get_all_categories'),

    path('delete_faults/', views.delete_faults, name='delete_faults'),

]
