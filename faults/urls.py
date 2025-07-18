from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'faults'

urlpatterns = [
    path('search_fault_data/', views.search_fault_data, name='search_fault_data'),
    path('export_fault_records/', views.export_fault_records, name='export_fault_records'),

    # 新增数据
    path('add_fault_data/', views.add_fault_data, name='add_fault_data'),
    # 获取审批人
    path('accepted_list/', views.accepter_list, name='accepted_list'),
    # 通知审批人
    path('notify_accepted/', views.notify_accepted, name='notify_accepted'),
    # 获取车辆信息
    path('getVehicles/', views.vehicle_list, name='vehicle_list'),
    # 获取所有系统和车号
    path('get_systems/', views.get_systems, name='get_systems'),
    # 获取所有分类数据
    path('get_all_categories/', views.get_all_categories, name='get_all_categories'),

    # 删除数据
    path('delete_faults/', views.delete_faults, name='delete_faults'),

    # 修改数据
    path('modify_fault_data.html/', TemplateView.as_view(template_name='modifyFaultData.html')),
    path('update_fault_record/', views.update_fault_record, name='update_fault_record'),
    path('get_fault_record/', views.get_fault_record, name='get_fault_record'),
    path('delete_image/', views.delete_image, name='delete_image'),
]
