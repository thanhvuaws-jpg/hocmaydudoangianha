@echo off
chcp 65001 >nul
title Giải nén dữ liệu thô
cd /d "%~dp0"
if exist "data\raw\nguon1_vietnam_real_estate_2025.csv" (
  echo Dữ liệu thô đã có sẵn trong data\raw.
  pause
  exit /b 0
)
if not exist "goi\du_lieu_tho.zip.001" (
  echo Không tìm thấy goi\du_lieu_tho.zip.001. Hãy tải đầy đủ repo về.
  pause
  exit /b 1
)
if not exist "data\raw" mkdir "data\raw"
echo Đang ghép và giải nén 6 tệp dữ liệu thô (khoảng 1,2 GB)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ra=[IO.File]::Create('%TEMP%\du_lieu_tho.zip'); Get-ChildItem 'goi\du_lieu_tho.zip.*' | Sort-Object Name | ForEach-Object { $v=[IO.File]::OpenRead($_.FullName); $v.CopyTo($ra); $v.Close() }; $ra.Close()"
tar -xf "%TEMP%\du_lieu_tho.zip" -C "data\raw"
if errorlevel 1 (
  echo Giải nén dữ liệu thất bại.
  pause
  exit /b 1
)
del "%TEMP%\du_lieu_tho.zip"
echo Xong. Dữ liệu nằm trong data\raw, có thể chạy lần lượt các notebook 01 đến 08.
pause
