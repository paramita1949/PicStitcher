@echo off
echo Building Image Processor V1.4...

python -m nuitka ^
--standalone ^
--enable-plugin=tk-inter ^
--enable-plugin=numpy ^
--windows-icon-from-ico=icon.ico ^
--include-data-files=icon.ico=icon.ico ^
--include-data-files=config.json=config.json ^
--include-module=PIL ^
--include-module=numpy ^
--include-module=tkinter ^
--include-module=tkinter.colorchooser ^
--include-module=json ^
--include-module=pathlib ^
--include-module=threading ^
--include-module=re ^
--follow-imports ^
--show-progress ^
--disable-console ^
--output-dir=build ^
main.py

echo.
echo Build completed!
echo Executable: build\main.dist\main.exe
echo Icon file: build\main.dist\icon.ico
pause
