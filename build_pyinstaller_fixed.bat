@echo off
echo Building with PyInstaller...

pyinstaller ^
--onefile ^
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
--name "ImageProcessorV1.4" ^
--distpath dist ^
main.py

echo.
echo Build completed!
echo Executable: dist\ImageProcessorV1.4.exe
pause
