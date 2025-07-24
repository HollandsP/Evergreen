@echo off
echo Creating CodeProjects.zip with exclusions...

cd /d "C:\Users\holla\OneDrive\Desktop"

REM Use tar to create zip (tar can create zip files on Windows 10+)
tar -a -c -f CodeProjects.zip --exclude=venv --exclude=.venv --exclude=env --exclude=__pycache__ --exclude=node_modules --exclude=.git --exclude=dist --exclude=build --exclude=*.pyc --exclude=.env CodeProjects

echo.
echo Zip file created successfully!
echo Location: C:\Users\holla\OneDrive\Desktop\CodeProjects.zip
pause