@echo off
echo 正在构建GPS照片工具...

rem 复制修复后的文件
copy /Y gps_photo_gui_fixed.py gps_photo_gui.py

rem 清理旧文件
rmdir /S /Q build
rmdir /S /Q dist
del /Q *.spec

rem 使用PyInstaller构建
pyinstaller --onefile --noconsole --name=GPSPhotoTool main.py

echo.
echo 构建完成!
echo 可执行文件位置: dist\GPSPhotoTool.exe
pause
