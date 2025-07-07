from django.db import models
from django.utils.translation import gettext_lazy as _


# 分类层级模型
class System(models.Model):
    name = models.CharField(_('系统名称'), max_length=100, unique=True)

    class Meta:
        verbose_name = _('一级分类')
        verbose_name_plural = _('一级分类')

    def __str__(self):
        return self.name


class SecondaryCategory(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE, verbose_name=_('所属系统'))
    name = models.CharField(_('二级分类名称'), max_length=100)

    class Meta:
        verbose_name = _('二级分类')
        verbose_name_plural = _('二级分类')
        constraints = [
            models.UniqueConstraint(fields=['system', 'name'], name='unique_secondary_per_system')
        ]

    def __str__(self):
        return f"{self.system} - {self.name}"


class ThirdCategory(models.Model):
    secondary = models.ForeignKey(SecondaryCategory, on_delete=models.CASCADE, verbose_name=_('所属二级分类'))
    name = models.CharField(_('三级分类名称'), max_length=100)

    class Meta:
        verbose_name = _('三级分类')
        verbose_name_plural = _('三级分类')
        constraints = [
            models.UniqueConstraint(fields=['secondary', 'name'], name='unique_third_per_secondary')
        ]

    def __str__(self):
        return f"{self.secondary} - {self.name}"


class FourthCategory(models.Model):
    third = models.ForeignKey(ThirdCategory, on_delete=models.CASCADE, verbose_name=_('所属三级分类'))
    name = models.CharField(_('四级分类名称'), max_length=100)

    class Meta:
        verbose_name = _('四级分类')
        verbose_name_plural = _('四级分类')
        constraints = [
            models.UniqueConstraint(fields=['third', 'name'], name='unique_fourth_per_third')
        ]

    def __str__(self):
        return f"{self.third} - {self.name}"


# 故障数据库
class FaultRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
    ]

    date = models.DateField(_('日期'), db_column='日期')
    time = models.TimeField(_('时间'), db_column='时间')
    train_number = models.CharField(_('车号'), max_length=10, db_column='车号')
    source = models.CharField(_('故障来源'), max_length=100, db_column='故障来源')
    fault_type = models.CharField(_('故障类型'), max_length=50, db_column='故障类型')
    phenomenon = models.TextField(_('故障现象'), db_column='故障现象')
    location = models.CharField(_('位置'), max_length=200, db_column='位置')
    status = models.CharField(_('状态'), max_length=20, choices=STATUS_CHOICES, default='pending', db_column='状态')
    technician = models.CharField(_('跟进技术人员'), max_length=100, db_column='跟进技术人员')
    # 替换原来的CharField为外键关联
    system = models.ForeignKey(System, on_delete=models.SET_NULL, verbose_name=_('故障系统'), null=True, blank=True,
                               db_column='故障系统')
    secondary = models.ForeignKey(SecondaryCategory, on_delete=models.SET_NULL, verbose_name=_('二级分类'), null=True,
                                  blank=True, db_column='二级分类')
    third = models.ForeignKey(ThirdCategory, on_delete=models.SET_NULL, verbose_name=_('三级分类'), null=True,
                              blank=True, db_column='三级分类')
    fourth = models.ForeignKey(FourthCategory, on_delete=models.SET_NULL, verbose_name=_('四级分类'), null=True,
                               blank=True, db_column='四级分类')
    cause = models.TextField(_('故障原因'), db_column='故障原因')
    reporter = models.CharField(_('报告人'), max_length=100, db_column='报告人')
    receiver = models.CharField(_('受理人'), max_length=100, db_column='受理人')
    progress = models.TextField(_('当前进度'), db_column='当前进度')
    expected_date = models.DateField(_('预计处理日期'), null=True, blank=True, db_column='预计处理日期')
    solution = models.TextField(_('处理办法'), db_column='处理办法')

    # 备件更换
    part_replaced = models.BooleanField(_('是否更换备件'), default=False, db_column='是否更换备件')
    part_name = models.CharField(_('备件名称'), max_length=100, blank=True, null=True, db_column='备件名称')
    part_quantity = models.IntegerField(_('备件数量'), null=True, blank=True, db_column='备件数量')
    materials = models.CharField(_('辅料'), max_length=200, blank=True, null=True, db_column='辅料')
    tools = models.CharField(_('工具'), max_length=200, blank=True, null=True, db_column='工具')

    location_time = models.IntegerField(_('故障定位用时(分钟)'), null=True, blank=True, db_column='故障定位用时(分钟)')
    replacement_time = models.IntegerField(_('更换用时(分钟)'), null=True, blank=True, db_column='更换用时(分钟)')
    legacy_date = models.DateField(_('遗留项处理日期'), null=True, blank=True, db_column='遗留项处理日期')

    # 登记信息
    registrar = models.CharField(_('登记人'), max_length=100, db_column='登记人')
    registration_time = models.DateTimeField(_('登记时间'), auto_now_add=True, db_column='登记时间')
    is_valid = models.BooleanField(_('是否有效'), default=True, db_column='是否有效')

    # 图片相关
    image_count = models.PositiveIntegerField(_('图片数量'), default=0, db_column='图片数量')
    image_paths = models.JSONField(_('图片路径'), default=list, blank=True, db_column='图片路径')

    # 修改信息
    modified_by = models.CharField(_('修改人'), max_length=100, blank=True, null=True, db_column='修改人')
    modified_at = models.DateTimeField(_('修改时间'), auto_now=True, db_column='修改时间')

    class Meta:
        verbose_name = _('故障记录')
        verbose_name_plural = _('故障记录')
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.date} - {self.train_number} - {self.phenomenon[:50]}"


# 车辆信息管理
class Vehicle(models.Model):
    plate_number = models.CharField(_('车号'), max_length=20, unique=True, db_column='车号')

    def __str__(self):
        return self.plate_number

    class Meta:
        verbose_name = '车辆'
        verbose_name_plural = '车辆管理'
