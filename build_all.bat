@echo off
echo ========================================
echo Building PicStitcher with Both Methods
echo ========================================
echo.
echo This script will build the project using:
echo   1. PyInstaller (Standalone mode)
echo   2. Nuitka (Standalone mode)
echo.

REM 检查依赖
echo Checking dependencies...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

python -c "import nuitka" 2>nul
if errorlevel 1 (
    echo Installing Nuitka...
    pip install nuitka ordered-set zstandard
)

echo.
echo ========================================
echo Step 1: Building with PyInstaller
echo ========================================
echo.

call build_pyinstaller_fixed.bat

if errorlevel 1 (
    echo PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Building with Nuitka
echo ========================================
echo.

call build_nuitka.bat

if errorlevel 1 (
    echo Nuitka build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo All Builds Completed Successfully!
echo ========================================
echo.
echo PyInstaller output:
echo   dist-pyinstaller\PicStitcher\PicStitcher.exe
echo.
echo Nuitka output:
echo   build\main.dist\PicStitcher.exe
echo.

pause

