from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    path('faults/', include('faults.urls')),

    # 根路径重定向：已登录跳转到故障查询，未登录跳转到登录页
    path('', login_required(RedirectView.as_view(pattern_name='faults:search_fault_data', permanent=False))),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
