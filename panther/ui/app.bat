@echo off
Rem: Function for create apps
SET path=%~1\%~2
SET app_folder=%~dp0template\app\
ECHO D | C:\Windows\system32\xcopy /s %app_folder% %path%
