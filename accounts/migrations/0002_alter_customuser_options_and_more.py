# Generated by Django 5.2.3 on 2025-06-30 08:18

import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="customuser",
            options={"verbose_name": "用户", "verbose_name_plural": "用户"},
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="approval_date",
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="approved_by",
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="is_approved",
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="permission_level",
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="registration_date",
        ),
        migrations.AddField(
            model_name="customuser",
            name="date_joined",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="date joined"
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="level",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "管理员"), (2, "组长"), (3, "记录员"), (4, "游客")],
                default=4,
                help_text="1=管理员, 2=组长, 3=记录员, 4=游客",
                verbose_name="权限等级",
            ),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                verbose_name="active",
            ),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="is_staff",
            field=models.BooleanField(
                default=False,
                help_text="Designates whether the user can log into this admin site.",
                verbose_name="staff status",
            ),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="password",
            field=models.CharField(max_length=128, verbose_name="password"),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="username",
            field=models.CharField(
                error_messages={"unique": "A user with that username already exists."},
                help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                max_length=150,
                unique=True,
                validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                verbose_name="username",
            ),
        ),
    ]
