# accounts/validators.py
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import MinimumLengthValidator


class CustomMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as e:
            raise ValidationError("密码长度至少需要8位") from e


class CustomNumericValidator:
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError("密码不能全是数字")

    def get_help_text(self):
        return "您的密码不能全部由数字组成"
