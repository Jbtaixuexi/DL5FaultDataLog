from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _


class CustomUserAdmin(UserAdmin):
    # 列表视图显示的字段
    list_display = ('username', 'level', 'is_staff', 'date_joined')

    # 添加用户表单字段
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'level'),
        }),
    )

    # 编辑用户表单字段
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('权限'), {
            'fields': ('level', 'is_active', 'is_staff', 'is_superuser'),
        }),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )

    # 搜索和筛选选项
    search_fields = ('username',)
    ordering = ('-date_joined',)
    filter_horizontal = ()


admin.site.register(CustomUser, CustomUserAdmin)