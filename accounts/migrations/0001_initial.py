# Generated by Django 5.2.3 on 2025-06-26 02:02

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(max_length=50, unique=True, verbose_name="用户名"),
                ),
                ("password", models.CharField(max_length=128, verbose_name="密码")),
                (
                    "permission_level",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "一级用户"),
                            (2, "二级用户"),
                            (3, "三级用户"),
                            (4, "四级用户（管理员）"),
                        ],
                        default=1,
                        verbose_name="权限等级",
                    ),
                ),
                (
                    "registration_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="注册时间"
                    ),
                ),
                (
                    "is_approved",
                    models.BooleanField(default=False, verbose_name="是否已审批"),
                ),
                (
                    "approval_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="审批时间"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="是否激活"),
                ),
                (
                    "is_staff",
                    models.BooleanField(default=False, verbose_name="管理后台权限"),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_users",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="审批人员",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "用户",
                "verbose_name_plural": "用户管理",
                "permissions": [("approve_user", "可以审批用户注册")],
            },
        ),
    ]
