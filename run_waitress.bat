@echo off
setlocal

REM ������ȷ����Ŀ·��
set PROJECT_PATH=F:\python\python_directory\DL5FaultDataLog
set VENV_PATH=%PROJECT_PATH%\.venv
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
set LOG_FILE=%PROJECT_PATH%\service.log

REM ���·���Ƿ����
if not exist "%PROJECT_PATH%" (
    echo ������Ŀ·��������: %PROJECT_PATH%
    pause
    exit /b 1
)

if not exist "%VENV_PATH%" (
    echo �������⻷��·��������: %VENV_PATH%
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo ����Python��ִ���ļ�������: %PYTHON_EXE%
    pause
    exit /b 1
)

REM �л�����ĿĿ¼
cd /d "%PROJECT_PATH%"

REM ��¼������Ϣ
echo [%date% %time%] ��ʼ�������� > "%LOG_FILE%"
echo ��ǰĿ¼: %cd% >> "%LOG_FILE%"
echo Python·��: %PYTHON_EXE% >> "%LOG_FILE%"

REM �������⻷��
call "%VENV_PATH%\Scripts\activate.bat"

REM ���Waitress�Ƿ�װ
echo ���Waitress��װ... >> "%LOG_FILE%"
"%PYTHON_EXE%" -m pip show waitress >> "%LOG_FILE%" 2>&1

REM ��������
echo ����Waitress����... >> "%LOG_FILE%"
"%PYTHON_EXE%" -m waitress --port=8000 DL5FaultDataLog.wsgi:application >> "%LOG_FILE%" 2>&1

REM ��¼������Ϣ
echo [%date% %time%] ����ֹͣ >> "%LOG_FILE%"
endlocal