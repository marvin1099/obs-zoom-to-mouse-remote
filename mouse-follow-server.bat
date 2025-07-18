@echo off
setlocal

REM Get the folder of this script
set "folder=%~dp0"
set "venv=%folder%venv"

REM Create virtual environment if it doesn't exist
if not exist "%venv%\Scripts\activate.bat" (
    python -m venv "%venv%"
)

REM Activate virtual environment
call "%venv%\Scripts\activate.bat"

REM Install required Python packages
pip install --upgrade pip
pip install pyautogui screeninfo obsws-python

echo ""
REM Run the Python script with all arguments
python "%folder%mouse-follow-server.py" %*

endlocal
