from django.utils.html import format_html
from .models import FaultRecord, SecondaryCategory, ThirdCategory, System
from django.contrib import admin


class SecondaryInline(admin.TabularInline):
    model = SecondaryCategory
    extra = 1


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    inlines = [SecondaryInline]


class ThirdInline(admin.TabularInline):
    model = ThirdCategory
    extra = 1


@admin.register(SecondaryCategory)
class SecondaryAdmin(admin.ModelAdmin):
    inlines = [ThirdInline]


@admin.register(FaultRecord)
class FaultRecordAdmin(admin.ModelAdmin):
    # 列表页显示字段（关键信息）
    list_display = (
        'date',
        'train_number',
        'fault_type',
        'status',
        'technician',
        'registrar'
    )

    # 搜索字段（支持多字段联合搜索）
    search_fields = (
        'train_number',
        'phenomenon',
        'location',
        'technician',
        'registrar'
    )

    # 强大的过滤面板
    list_filter = (
        'status',
        'date',
        'train_number',
        'fault_type',
        ('category', admin.RelatedOnlyFieldListFilter),
        'part_replaced',
        'is_valid'
    )

    # 分页设置（每页显示数量）
    list_per_page = 25

    # 日期层级导航
    date_hierarchy = 'date'

    # 表单页字段分组（逻辑清晰）
    fieldsets = (
        ('基础信息', {
            'fields': (
                ('date', 'time'),
                'train_number',
                'source',
                'fault_type',
                'phenomenon',
                'location',
                'status',
                'technician'
            )
        }),
        ('处理信息', {
            'fields': (
                'cause',
                ('reporter', 'receiver'),
                'progress',
                'expected_date',
                'solution'
            )
        }),
        ('备件更换', {
            'fields': (
                'part_replaced',
                ('part_name', 'part_quantity'),
                'materials',
                'tools'
            ),
            'classes': ('collapse',)
        }),
        ('时间记录', {
            'fields': (
                ('location_time', 'replacement_time'),
                'legacy_date'
            )
        }),
        ('登记信息', {
            'fields': (
                ('registrar', 'registration_time'),
                'is_valid'
            )
        }),
        ('多媒体', {
            'fields': (
                'image_count',
                'image_paths'
            )
        }),
        ('审计信息', {
            'fields': (
                ('modified_by', 'modified_at'),
            ),
            'classes': ('collapse',)
        }),
    )

    # 只读字段（自动生成/修改的字段）
    readonly_fields = (
        'registration_time',
        'modified_at',
        'image_count'
    )

    # 自定义列表状态颜色
    def colored_status(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'resolved': 'green'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    colored_status.short_description = '状态'

    # 覆盖默认的__str__显示
    def __str__(self):
        return f"{self.date} {self.train_number}"


# 可选：添加全局管理配置
admin.site.site_header = "故障管理系统后台"
admin.site.site_title = "故障管理"
admin.site.index_title = "数据管理仪表板"
