from django.contrib.auth import get_user_model, login, authenticate
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .forms import LoginForm
from django.contrib.auth import logout
from django.contrib import messages
from .forms import RegistrationForm

User = get_user_model()


@require_http_methods(['GET', 'POST'])
def Flogin(request):
    # 已登录用户直接跳转到故障查询页
    if request.user.is_authenticated:
        return redirect('faults:search_fault_data')

    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember', False)

            # 使用Django的authenticate验证用户
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                # 设置session过期时间（记住我：2周，否则浏览器关闭失效）
                if not remember:
                    request.session.set_expiry(0)
                return redirect('faults:search_fault_data')

        # 验证失败时显示错误信息
        return render(request, 'login.html', {
            'form': form,
            'error_message': '用户名或密码不正确'
        })


def flogout(request):
    """用户登出视图"""
    logout(request)
    return redirect('accounts:login')  # 登出后重定向到登录页


def register(request):
    """用户注册视图（仅管理员可用）"""
    # 检查当前用户是否有权限（管理员）
    if not request.user.is_authenticated or request.user.level != 1:
        return redirect('accounts:login')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # 创建用户但不登录
            user = form.save()

            # 显示成功消息
            messages.success(
                request,
                f'成功创建用户: {user.username} ({user.get_level_display()})'
            )

            # 可以选择重定向到用户列表页或保持当前页
            return redirect('accounts:register')  # 留在注册页以便创建更多用户
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})
