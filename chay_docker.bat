@echo off
chcp 65001 >nul
title Định giá nhà đất - Docker
cd /d "%~dp0"

if exist "models\xgb.json" if exist "models\lightgbm.txt" if exist "models\catboost.cbm" goto co_mo_hinh
if not exist "goi\mo_hinh.zip.001" (
  echo Thiếu mô hình trong thư mục models và không tìm thấy goi\mo_hinh.zip.001. Hãy tải đầy đủ repo về.
  pause
  exit /b 1
)
echo Lần đầu chạy: đang ghép và giải nén mô hình (khoảng 550 MB, mất vài chục giây)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ra=[IO.File]::Create('%TEMP%\mo_hinh.zip'); Get-ChildItem 'goi\mo_hinh.zip.*' | Sort-Object Name | ForEach-Object { $v=[IO.File]::OpenRead($_.FullName); $v.CopyTo($ra); $v.Close() }; $ra.Close()"
tar -xf "%TEMP%\mo_hinh.zip" -C models
if errorlevel 1 (
  echo Giải nén mô hình thất bại.
  pause
  exit /b 1
)
del "%TEMP%\mo_hinh.zip"
echo Đã giải nén mô hình vào thư mục models.
:co_mo_hinh

where docker >nul 2>&1
if errorlevel 1 (
  echo Chưa cài Docker Desktop. Tải tại https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

docker info >nul 2>&1
if not errorlevel 1 goto docker_san_sang
echo Đang khởi động Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a dem=0
:cho_docker
ping -n 4 127.0.0.1 >nul
docker info >nul 2>&1
if not errorlevel 1 goto docker_san_sang
set /a dem+=1
if %dem% geq 60 (
  echo Docker chưa sẵn sàng sau 3 phút. Hãy mở Docker Desktop thủ công rồi chạy lại file này.
  pause
  exit /b 1
)
goto cho_docker

:docker_san_sang
set "LENH=docker compose up -d"
if /i "%~1"=="build" set "LENH=docker compose up -d --build"
docker image inspect du-doan-gia-nha:1.0 >nul 2>&1
if errorlevel 1 set "LENH=docker compose up -d --build"
echo Đang chạy: %LENH%
%LENH%
if errorlevel 1 (
  echo Không khởi động được container. Kiểm tra cổng 8000 có đang bị chương trình khác dùng không.
  pause
  exit /b 1
)

echo Đang chờ ứng dụng nạp mô hình...
set /a dem=0
:cho_app
ping -n 3 127.0.0.1 >nul
curl -sf -o nul http://localhost:8000/api/suc-khoe
if not errorlevel 1 goto mo_trinh_duyet
set /a dem+=1
if %dem% geq 90 (
  echo Ứng dụng chưa phản hồi sau 3 phút. Xem log bằng lệnh: docker compose logs
  pause
  exit /b 1
)
goto cho_app

:mo_trinh_duyet
start "" http://localhost:8000
echo.
echo Ứng dụng đang chạy tại http://localhost:8000  (tài liệu API: http://localhost:8000/docs)
echo Chạy dung_docker.bat để tắt. Chạy "chay_docker.bat build" để build lại sau khi sửa code.
echo.
pause
