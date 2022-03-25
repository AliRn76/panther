@echo off
Rem: Function for create apps
SET path=%~2\%~3
SET app_folder=%~dp0template\app\
ECHO D | C:\Windows\system32\xcopy /s %app_folder% %path%
