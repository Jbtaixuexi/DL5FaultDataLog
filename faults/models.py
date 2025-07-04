from django.db import models
from django.utils.translation import gettext_lazy as _


# 新增分类层级模型
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


class FaultRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
    ]

    date = models.DateField(_('日期'))
    time = models.TimeField(_('时间'))
    train_number = models.CharField(_('车号'), max_length=10)
    source = models.CharField(_('故障来源'), max_length=100)
    fault_type = models.CharField(_('故障类型'), max_length=50)
    phenomenon = models.TextField(_('故障现象'))
    location = models.CharField(_('位置'), max_length=200)
    status = models.CharField(_('状态'), max_length=20, choices=STATUS_CHOICES, default='pending')
    technician = models.CharField(_('处理人员'), max_length=100)
    # 替换原来的CharField为外键关联
    system = models.ForeignKey(System, on_delete=models.SET_NULL, verbose_name=_('系统'), null=True, blank=True)
    secondary = models.ForeignKey(SecondaryCategory, on_delete=models.SET_NULL, verbose_name=_('二级分类'), null=True,
                                  blank=True)
    third = models.ForeignKey(ThirdCategory, on_delete=models.SET_NULL, verbose_name=_('三级分类'), null=True,
                              blank=True)
    fourth = models.ForeignKey(FourthCategory, on_delete=models.SET_NULL, verbose_name=_('四级分类'), null=True,
                               blank=True)
    cause = models.TextField(_('故障原因'))
    reporter = models.CharField(_('报告人'), max_length=100)
    receiver = models.CharField(_('接收人'), max_length=100)
    progress = models.TextField(_('处理进度'))
    expected_date = models.DateField(_('预计完成日期'), null=True, blank=True)
    solution = models.TextField(_('解决方案'))

    # 备件更换
    part_replaced = models.BooleanField(_('更换备件'), default=False)
    part_name = models.CharField(_('备件名称'), max_length=100, blank=True, null=True)
    part_quantity = models.IntegerField(_('备件数量'), null=True, blank=True)
    materials = models.CharField(_('使用材料'), max_length=200, blank=True, null=True)
    tools = models.CharField(_('使用工具'), max_length=200, blank=True, null=True)

    location_time = models.IntegerField(_('定位用时(分钟)'), null=True, blank=True)
    replacement_time = models.IntegerField(_('更换用时(分钟)'), null=True, blank=True)
    legacy_date = models.DateField(_('遗留项处理日期'), null=True, blank=True)

    # 登记信息
    registrar = models.CharField(_('登记人'), max_length=100)
    registration_time = models.DateTimeField(_('登记时间'), auto_now_add=True)
    is_valid = models.BooleanField(_('是否有效'), default=True)

    # 图片相关
    image_count = models.PositiveIntegerField(_('图片数量'), default=0)
    image_paths = models.JSONField(_('图片路径'), default=list, blank=True)

    # 修改信息
    modified_by = models.CharField(_('修改人'), max_length=100, blank=True, null=True)
    modified_at = models.DateTimeField(_('修改时间'), auto_now=True)

    class Meta:
        verbose_name = _('故障记录')
        verbose_name_plural = _('故障记录')
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.date} - {self.train_number} - {self.phenomenon[:50]}"
