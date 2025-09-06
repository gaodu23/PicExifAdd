# GPS照片批处理工具 - 标准EXIF版本

## 简介
批量为照片添加GPS地理位置信息的工具，使用标准EXIF方法，支持多种图片格式。

## 核心功能
- 📍 批量添加GPS坐标到照片EXIF（标准EXIF方法）
- 📊 支持CSV格式的GPS数据导入
- 🖼️ 支持JPG、JPEG、TIFF等常见图片格式
- ⚙️ 支持相机畸变参数和焦距处理
- 🖥️ 图形界面操作，简单易用
- � GUI界面和命令行模式双模式

## 快速开始

### 1. 一键启动（推荐）
直接双击 `run_gui.bat` 启动GUI程序

### 2. 手动安装依赖（可选）
```cmd
install_deps.bat
```

### 3. 直接使用Python运行
```cmd
python main.py
```

## 特点说明
- ✅ **标准EXIF处理** - 使用标准EXIF方法，兼容性更好
- ✅ **无XMP依赖** - 避免复杂的XMP库安装问题
- ✅ **自动安装依赖** - 启动时自动检查和安装必要依赖
- ✅ **稳定可靠** - 专注核心功能，减少错误

## 文件说明
- `main.py` - 主程序入口
- `gps_photo_gui.py` - GUI图形界面
- `batch_add_gps_info.py` - 批处理核心逻辑
- `run_gui.bat` - 一键启动脚本
- `requirements.txt` - Python依赖列表（精简版）
- `cameraInfo/` - 相机畸变参数文件

## 系统要求
- Python 3.7+
- Windows/Linux/macOS

## 核心依赖（精简）
- pandas>=2.0.0 - 数据处理
- Pillow>=9.0.0 - 图像处理
- piexif>=1.1.3 - EXIF数据操作
- tkinter - GUI框架（Python内置）

---
**版本**: 标准EXIF版本 | **更新时间**: 2025年8月24日 | **状态**: ✅ GUI正常运行
