@echo off
Rem: Function for create project files
SET path=%~1\%~2
SET pro_folder=%~dp0template\project\
ECHO D | C:\Windows\system32\xcopy /s %pro_folder% %path%

