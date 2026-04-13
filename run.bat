@echo off
start "Backend" cmd /k "%~dp0backend\start.bat"
ping -n 5 127.0.0.1 >nul
start "Frontend" cmd /k "%~dp0frontend\start.bat"
ping -n 6 127.0.0.1 >nul
start http://localhost:5173
