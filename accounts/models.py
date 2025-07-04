from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """自定义用户管理器"""

    def create_user(self, username, password=None, level=4, **extra_fields):
        """创建普通用户"""
        if not username:
            raise ValueError('必须提供用户名')

        user = self.model(
            username=username,
            level=level,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, level=1, **extra_fields):
        """创建管理员用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('管理员必须是职员 (is_staff=True)')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('管理员必须拥有超级权限 (is_superuser=True)')

        return self.create_user(username, password, level, **extra_fields)


class CustomUser(AbstractUser):
    """自定义用户模型"""

    # 权限等级选择
    LEVEL_CHOICES = (
        (1, '管理员'),
        (2, '组长'),
        (3, '记录员'),
        (4, '游客'),
    )

    # 用户权限等级字段
    level = models.PositiveSmallIntegerField(
        _('权限等级'),
        choices=LEVEL_CHOICES,
        default=4,
        help_text=_('1=管理员, 2=组长, 3=记录员, 4=游客')
    )

    # 移除不必要的字段
    first_name = None
    last_name = None
    email = None

    # 使用自定义管理器
    objects = CustomUserManager()

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')

    def __str__(self):
        return f"{self.username} ({self.get_level_display()})"

    # 权限检查方法
    def is_admin(self):
        return self.level == 1

    def is_leader(self):
        return self.level == 2

    def is_recorder(self):
        return self.level == 3

    def is_visitor(self):
        return self.level == 4