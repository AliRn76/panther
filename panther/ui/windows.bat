@ECHO off
:make_project
    Rem: Function for create project files
    SET name=%~3
    SET path=%~2\%name%
    SET ui_folder=%~dp0template\project\
    echo D | C:\Windows\system32\xcopy %ui_folder% %path%
EXIT /B 0


:make_apps
    Rem: Function for create apps
    SET path=%~1
    SET app_names=%~2
    SET ui_folder=%~dp0template\app\

EXIT /B 0

IF %1 EQU "p" (
    CALL :make_project
) ELSE (
    CALL :make_project
)
