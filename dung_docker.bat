@echo off
chcp 65001 >nul
title Định giá nhà đất - tắt Docker
cd /d "%~dp0"
docker compose down
echo Đã tắt ứng dụng.
ping -n 3 127.0.0.1 >nul
