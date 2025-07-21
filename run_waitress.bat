@echo off
setlocal

REM 设置正确的项目路径
set PROJECT_PATH=F:\python\python_directory\DL5FaultDataLog
set VENV_PATH=%PROJECT_PATH%\.venv
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
set LOG_FILE=%PROJECT_PATH%\service.log

REM 检查路径是否存在
if not exist "%PROJECT_PATH%" (
    echo 错误：项目路径不存在: %PROJECT_PATH%
    pause
    exit /b 1
)

if not exist "%VENV_PATH%" (
    echo 错误：虚拟环境路径不存在: %VENV_PATH%
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo 错误：Python可执行文件不存在: %PYTHON_EXE%
    pause
    exit /b 1
)

REM 切换到项目目录
cd /d "%PROJECT_PATH%"

REM 记录启动信息
echo [%date% %time%] 开始启动服务 > "%LOG_FILE%"
echo 当前目录: %cd% >> "%LOG_FILE%"
echo Python路径: %PYTHON_EXE% >> "%LOG_FILE%"

REM 激活虚拟环境
call "%VENV_PATH%\Scripts\activate.bat"

REM 检查Waitress是否安装
echo 检查Waitress安装... >> "%LOG_FILE%"
"%PYTHON_EXE%" -m pip show waitress >> "%LOG_FILE%" 2>&1

REM 启动服务
echo 启动Waitress服务... >> "%LOG_FILE%"
"%PYTHON_EXE%" -m waitress --port=8000 DL5FaultDataLog.wsgi:application >> "%LOG_FILE%" 2>&1

REM 记录结束信息
echo [%date% %time%] 服务停止 >> "%LOG_FILE%"
endlocal