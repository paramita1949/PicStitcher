@echo off
echo ========================================
echo Building PicStitcher with Nuitka
echo ========================================
echo.

REM 检查是否安装了 Nuitka
python -c "import nuitka" 2>nul
if errorlevel 1 (
    echo Nuitka not found. Installing...
    pip install nuitka ordered-set zstandard
)

echo.
echo Starting build process...
echo.

REM 使用 Nuitka 编译（非单文件模式）
python -m nuitka ^
--standalone ^
--windows-console-mode=disable ^
--enable-plugin=tk-inter ^
--include-data-file=icon.ico=icon.ico ^
--windows-icon-from-ico=icon.ico ^
--windows-company-name="PicStitcher" ^
--windows-product-name="PicStitcher Plus" ^
--windows-file-version="1.5.0.0" ^
--windows-product-version="1.5.0.0" ^
--windows-file-description="PicStitcher - 图片智能拼接工具" ^
--output-dir=build-nuitka ^
--output-filename=PicStitcher.exe ^
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
echo Output directory: build-nuitka\main.dist
echo Executable: build-nuitka\main.dist\PicStitcher.exe
echo.
echo You can now run the program from:
echo   build-nuitka\main.dist\PicStitcher.exe
echo.

pause

