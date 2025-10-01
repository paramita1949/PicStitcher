@echo off
echo ========================================
echo Building PicStitcher with PyInstaller
echo ========================================
echo.

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Starting build process...
echo.

REM 使用 PyInstaller 打包（非单文件模式）
pyinstaller ^
--windowed ^
--icon=icon.ico ^
--add-data "icon.ico;." ^
--hidden-import=PIL ^
--hidden-import=numpy ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
--hidden-import=tkinter.filedialog ^
--hidden-import=tkinter.messagebox ^
--hidden-import=tkinter.colorchooser ^
--name "PicStitcher" ^
--distpath dist-pyinstaller ^
main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output directory: dist-pyinstaller\PicStitcher
echo Executable: dist-pyinstaller\PicStitcher\PicStitcher.exe
echo.
echo You can now run the program from:
echo   dist-pyinstaller\PicStitcher\PicStitcher.exe
echo.

pause
