@echo off
powershell -NoProfile -Sta -ExecutionPolicy Bypass -Command "& '%~dp0run.ps1' %*"
