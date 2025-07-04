from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(label="用户名")
    password = forms.CharField(label="密码", widget=forms.PasswordInput)
    remember = forms.BooleanField(
        label="记住我",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class RegistrationForm(UserCreationForm):
    level = forms.ChoiceField(
        label='权限等级',
        choices=User.LEVEL_CHOICES,
        initial=4,
        help_text='1=管理员, 2=组长, 3=记录员, 4=游客'
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'level']
