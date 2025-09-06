#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPS照片批量添加工具 - 桌面版
支持从CSV文件读取GPS信息并批量添加到JPG照片的EXIF数据中
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import csv
import time
from batch_add_gps_info import process_images_from_csv, detect_csv_format
import pandas as pd

# 尝试导入OPT文件转换模块
try:
    from opt_converter import parse_opt_file, test_opt_conversion, get_available_opt_files
    OPT_CONVERTER_AVAILABLE = True
except ImportError:
    OPT_CONVERTER_AVAILABLE = False
    print("警告: 未找到opt_converter.py，无法使用相机畸变参数转换功能")

class CSVColumnMappingDialog:
    """CSV列映射对话框"""
    def __init__(self, parent, csv_file):
        self.parent = parent
        self.csv_file = csv_file
        self.result = None
        self.columns = []
        
        # 读取CSV文件获取列信息
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                first_row = next(reader)
                # 检查是否有表头
                if any(keyword in first_row[0].lower() for keyword in 
                       ['文件名', 'filename', '纬度', '经度', 'latitude', 'longitude']):
                    self.columns = first_row
                    self.has_header = True
                else:
                    # 如果没有表头，生成列号
                    self.columns = [f"列{i+1}" for i in range(len(first_row))]
                    self.has_header = False
        except Exception as e:
            messagebox.showerror("错误", f"无法读取CSV文件: {e}")
            return
        
        self.setup_dialog()
    
    def setup_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("CSV列映射设置")
        self.dialog.geometry("800x700")  # 增大窗口以容纳预览内容
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="请选择CSV文件中各字段对应的列：", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 文件信息
        info_text = f"文件: {os.path.basename(self.csv_file)}\n"
        info_text += f"格式: {'有表头' if self.has_header else '无表头'}\n"
        info_text += f"列数: {len(self.columns)}"
        
        info_label = ttk.Label(main_frame, text=info_text, foreground="gray")
        info_label.pack(pady=(0, 10))
        
        # 列选择区域
        mapping_frame = ttk.LabelFrame(main_frame, text="字段映射", padding=10)
        mapping_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文件名列选择
        ttk.Label(mapping_frame, text="文件名列:", width=15).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.filename_var = tk.StringVar()
        self.filename_combo = ttk.Combobox(mapping_frame, textvariable=self.filename_var, 
                                          values=self.columns, state="readonly", width=25)
        self.filename_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 纬度列选择
        ttk.Label(mapping_frame, text="纬度列:", width=15).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.latitude_var = tk.StringVar()
        self.latitude_combo = ttk.Combobox(mapping_frame, textvariable=self.latitude_var, 
                                          values=self.columns, state="readonly", width=25)
        self.latitude_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 经度列选择
        ttk.Label(mapping_frame, text="经度列:", width=15).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.longitude_var = tk.StringVar()
        self.longitude_combo = ttk.Combobox(mapping_frame, textvariable=self.longitude_var, 
                                           values=self.columns, state="readonly", width=25)
        self.longitude_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 海拔列选择
        ttk.Label(mapping_frame, text="海拔列:", width=15).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.altitude_var = tk.StringVar()
        self.altitude_combo = ttk.Combobox(mapping_frame, textvariable=self.altitude_var, 
                                          values=["不使用"] + self.columns, state="readonly", width=25)
        self.altitude_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 预览区域
        preview_label_frame = ttk.LabelFrame(main_frame, text="CSV数据预览 (前10行)", padding=10)
        preview_label_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 10))
        
        # 创建表格来显示CSV数据
        self.create_preview_table(preview_label_frame)
        
        # 自动检测和设置默认值
        self.auto_detect_columns()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="确定", command=self.on_ok).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=self.on_cancel).pack(side=tk.RIGHT)
        
        # 等待对话框关闭
        self.dialog.wait_window()
    
    def create_preview_table(self, parent_frame):
        """创建CSV数据预览表格"""
        # 创建Treeview来显示表格数据
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建表格
        self.preview_tree = ttk.Treeview(tree_frame, 
                                        yscrollcommand=v_scrollbar.set,
                                        xscrollcommand=h_scrollbar.set,
                                        height=8)  # 减小高度以适合在同一页显示
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        v_scrollbar.config(command=self.preview_tree.yview)
        h_scrollbar.config(command=self.preview_tree.xview)
        
        # 设置列
        if self.has_header:
            # 有表头：使用实际列名
            self.preview_tree["columns"] = self.columns
            self.preview_tree["show"] = "tree headings"
            
            # 设置第一列（行号）
            self.preview_tree.heading("#0", text="行号", anchor="w")
            self.preview_tree.column("#0", width=50, anchor="w")
            
            # 设置其他列
            for col in self.columns:
                self.preview_tree.heading(col, text=col, anchor="w")
                self.preview_tree.column(col, width=120, anchor="w")
        else:
            # 无表头：使用列号
            column_names = [f"列{i+1}" for i in range(len(self.columns))]
            self.preview_tree["columns"] = column_names
            self.preview_tree["show"] = "tree headings"
            
            # 设置第一列（行号）
            self.preview_tree.heading("#0", text="行号", anchor="w")
            self.preview_tree.column("#0", width=50, anchor="w")
            
            # 设置其他列
            for i, col_name in enumerate(column_names):
                self.preview_tree.heading(col_name, text=col_name, anchor="w")
                self.preview_tree.column(col_name, width=120, anchor="w")
        
        # 读取并显示CSV数据
        self.load_csv_data()
    
    def load_csv_data(self):
        """加载并显示CSV数据"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # 如果有表头，跳过第一行（已用作列标题）
                data_rows = rows[1:] if self.has_header else rows
                
                # 只显示前10行数据
                display_rows = data_rows[:10]
                
                for i, row in enumerate(display_rows):
                    # 确保行数据长度与列数匹配
                    while len(row) < len(self.columns):
                        row.append("")  # 补充空值
                    
                    # 只取前len(self.columns)个值
                    row_data = row[:len(self.columns)]
                    
                    # 插入数据到表格
                    self.preview_tree.insert("", "end", text=str(i+1), values=row_data)
                    
        except Exception as e:
            # 如果读取失败，显示错误信息
            error_msg = f"读取CSV文件失败: {str(e)}"
            self.preview_tree.insert("", "end", text="错误", values=[error_msg] + [""] * (len(self.columns)-1))
    
    def auto_detect_columns(self):
        """自动检测列"""
        for i, col in enumerate(self.columns):
            col_lower = col.lower()
            
            # 文件名列检测
            if any(keyword in col_lower for keyword in ['文件名', 'filename', 'file', 'name']):
                self.filename_combo.current(i)
            
            # 纬度列检测  
            elif any(keyword in col_lower for keyword in ['纬度', 'latitude', 'lat']):
                self.latitude_combo.current(i)
            
            # 经度列检测
            elif any(keyword in col_lower for keyword in ['经度', 'longitude', 'lng', 'lon']):
                self.longitude_combo.current(i)
            
            # 海拔列检测
            elif any(keyword in col_lower for keyword in ['海拔', 'altitude', 'alt', '高度', 'height']):
                self.altitude_combo.current(i + 1)  # +1因为有"不使用"选项
    
    def on_ok(self):
        """确定按钮"""
        if not self.filename_var.get() or not self.latitude_var.get() or not self.longitude_var.get():
            messagebox.showwarning("警告", "文件名、纬度和经度列为必选项！")
            return
        
        # 检查是否有重复选择
        selected = [self.filename_var.get(), self.latitude_var.get(), self.longitude_var.get()]
        if self.altitude_var.get() and self.altitude_var.get() != "不使用":
            selected.append(self.altitude_var.get())
        
        if len(selected) != len(set(selected)):
            messagebox.showwarning("警告", "不能选择相同的列！")
            return
        
        self.result = {
            'filename': self.filename_var.get(),
            'latitude': self.latitude_var.get(), 
            'longitude': self.longitude_var.get(),
            'altitude': self.altitude_var.get() if self.altitude_var.get() != "不使用" else None,
            'has_header': self.has_header
        }
        self.dialog.destroy()
    
    def on_cancel(self):
        """取消按钮"""
        self.result = None
        self.dialog.destroy()

class GPSPhotoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS照片批量添加工具")
        self.root.geometry("1000x800")  # 增加窗口高度和宽度
        self.root.resizable(True, True)
        self.root.configure(bg="#F8F9FA")
        
        # 尝试设置图标
        try:
            self.root.iconbitmap("icon.ico")  # 如果有图标文件的话
        except:
            pass  # 没有图标则忽略
        
        # 变量初始化
        self.csv_path = tk.StringVar()
        self.image_folder = tk.StringVar()
        self.opt_file_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.processing = False
        self.should_stop = False
        
        # CSV列映射
        self.csv_column_mapping = {
            'filename': None,
            'latitude': None, 
            'longitude': None,
            'altitude': None
        }
        
        # 默认加载cameraInfo/default.opt
        default_opt = os.path.join("cameraInfo", "default.opt")
        if os.path.exists(default_opt):
            self.opt_file_path.set(default_opt)
        
        # 设置样式和UI
        self.setup_styles()
        self.setup_ui()
    
    def setup_styles(self):
        """设置自定义样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主题颜色
        primary_color = "#3498DB"  # 蓝色
        secondary_color = "#7F8C8D"  # 灰色
        accent_color = "#2ECC71"  # 绿色
        danger_color = "#E74C3C"  # 红色
        
        # 基本按钮样式
        style.configure("TButton", padding=6, relief="flat",
                        background="#FFFFFF", foreground="#212529",
                       font=("Segoe UI", 9))
        
        # 主要按钮（蓝色）
        style.configure("Primary.TButton",
                        background=primary_color, foreground="white",
                       padding=(10, 5), font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton",
                 background=[("active", "#2980B9")],
                 relief=[("pressed", "sunken")])
        
        # 次要按钮（灰色）
        style.configure("Secondary.TButton",
                        background=secondary_color, foreground="white",
                       padding=(10, 5))
        style.map("Secondary.TButton",
                 background=[("active", "#6D7B7C")],
                 relief=[("pressed", "sunken")])
         
        # 取消按钮（红色）
        style.configure("Danger.TButton",
                        background=danger_color, foreground="white",
                       padding=(10, 5), font=("Segoe UI", 9, "bold"))
        style.map("Danger.TButton",
                 background=[("active", "#C0392B")],
                 relief=[("pressed", "sunken")])
        
        # 强调按钮（绿色）
        style.configure("Accent.TButton",
                        background=accent_color, foreground="white")
        style.map("Accent.TButton",
                 background=[("active", "#27AE60")],
                 relief=[("pressed", "sunken")])
         
        # 进度条样式
        style.configure("TProgressbar", thickness=10,
                        troughcolor="#F0F0F0", background=primary_color)
               
        # 标签框架样式
        style.configure("TLabelframe", background="#FFFFFF",
                        bordercolor="#DDDDDD", borderwidth=1)
        style.configure("TLabelframe.Label", foreground="#2C3E50",
                        background="#FFFFFF", font=("Segoe UI", 9, "bold"))

    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题和图标
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="航片GPS批量添加工具--LHC",
                                font=('Arial', 18, 'bold'), foreground="#2C3E50")
        title_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 文件选择区域框架
        files_frame = ttk.LabelFrame(main_frame, text="文件选择", padding=(15, 10))
        files_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        files_frame.columnconfigure(1, weight=1)
        
        # 相机参数文件选择
        ttk.Label(files_frame, text="相机参数文件:").grid(row=0, column=0, sticky=tk.W, pady=8)
        opt_entry = ttk.Entry(files_frame, textvariable=self.opt_file_path, width=50)
        opt_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=8)
        ttk.Button(files_frame, text="浏览", style="Accent.TButton", command=self.select_opt_file).grid(row=0, column=2, pady=8, padx=5)
        
        # CSV文件选择
        ttk.Label(files_frame, text="CSV文件:").grid(row=1, column=0, sticky=tk.W, pady=8)
        ttk.Entry(files_frame, textvariable=self.csv_path, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=8)
        ttk.Button(files_frame, text="浏览", style="Accent.TButton", command=self.select_csv_file).grid(row=1, column=2, pady=8, padx=5)
        
        # 图片文件夹选择
        ttk.Label(files_frame, text="航片文件夹:").grid(row=2, column=0, sticky=tk.W, pady=8)
        ttk.Entry(files_frame, textvariable=self.image_folder, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=8)
        ttk.Button(files_frame, text="浏览", style="Accent.TButton", command=self.select_image_folder).grid(row=2, column=2, pady=8, padx=5)
        
        # 导出位置选择
        ttk.Label(files_frame, text="导出位置:").grid(row=3, column=0, sticky=tk.W, pady=8)
        ttk.Entry(files_frame, textvariable=self.output_folder, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=8)
        ttk.Button(files_frame, text="浏览", style="Accent.TButton", command=self.select_output_folder).grid(row=3, column=2, pady=8, padx=5)
        
        # 文件信息显示区域
        info_frame = ttk.LabelFrame(main_frame, text="处理日志", padding=(15, 10))
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # 创建文本区域
        self.info_text = scrolledtext.ScrolledText(info_frame, height=12, width=80, font=("Consolas", 9))
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.info_text.config(background="#F8F9FA", foreground="#212529")
        
        # 确保滚动文本组件已经初始化
        self.root.update()
        
        # 配置日志文本标签
        self.info_text.tag_configure("success", foreground="#27AE60")  # 绿色
        self.info_text.tag_configure("error", foreground="#E74C3C")  # 红色
        self.info_text.tag_configure("warning", foreground="#F39C12")  # 橙色
        self.info_text.tag_configure("info", foreground="#3498DB")  # 蓝色
        self.info_text.tag_configure("separator", foreground="#7F8C8D")  # 灰色
        
        # 控制区域框架
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)
        
        # 预览按钮
        self.preview_button = ttk.Button(controls_frame, text="预览文件",
                                        style="Secondary.TButton",
                                        command=self.preview_files)
        self.preview_button.grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        
        # 处理按钮
        self.process_button = ttk.Button(controls_frame, text="开始处理",
                                        style="Primary.TButton",
                                        command=self.toggle_processing)
        self.process_button.grid(row=0, column=1, padx=10, pady=10)
        
        # 清空按钮
        ttk.Button(controls_frame, text="清空日志",
                  style="Secondary.TButton",
                  command=self.clear_log).grid(row=0, column=2, padx=10, pady=10, sticky=tk.W)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', style="TProgressbar")
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(5, 5), padx=5)
        
        # 进度标签
        self.progress_label = ttk.Label(progress_frame, text="0 / 0", font=("Arial", 9))
        self.progress_label.grid(row=1, column=0, pady=(0, 5))
        
        # 状态栏
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪", foreground="green", padding=(5, 3))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
    
    def select_csv_file(self):
        """选择CSV文件"""
        filename = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if filename:
            # 打开列映射对话框
            dialog = CSVColumnMappingDialog(self.root, filename)
            if dialog.result:
                self.csv_path.set(filename)
                self.csv_column_mapping = dialog.result
                self.log(f"✅ 已选择CSV文件: {os.path.basename(filename)}")
                self.log(f"   文件名列: {dialog.result['filename']}")
                self.log(f"   纬度列: {dialog.result['latitude']}")
                self.log(f"   经度列: {dialog.result['longitude']}")
                if dialog.result['altitude']:
                    self.log(f"   海拔列: {dialog.result['altitude']}")
                else:
                    self.log(f"   海拔列: 不使用")
            else:
                self.log("❌ 未完成CSV列映射设置")
        
    def select_image_folder(self):
        """选择图片文件夹"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.image_folder.set(folder)
            self.log(f"✅ 已选择图片文件夹: {os.path.basename(folder)}")

    def select_opt_file(self):
        """选择OPT文件"""
        filename = filedialog.askopenfilename(
            title="选择相机参数文件",
            filetypes=[("OPT文件", "*.opt"), ("所有文件", "*.*")],
            initialdir="cameraInfo"
        )
        if filename:
            self.opt_file_path.set(filename)
            self.log(f"✅ 已选择相机参数文件: {os.path.basename(filename)}")
            self.show_opt_info(filename)
            
    def select_output_folder(self):
        """选择导出位置文件夹"""
        folder = filedialog.askdirectory(title="选择导出位置")
        if folder:
            self.output_folder.set(folder)
            self.log(f"✅ 已选择导出位置: {os.path.basename(folder)}")
            
            # 如果文件夹不存在则创建
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                    self.log(f"✅ 已创建导出文件夹: {os.path.basename(folder)}")
                except Exception as e:
                    self.log(f"❌ 创建导出文件夹失败: {e}")

    def show_opt_info(self, opt_file):
        """显示OPT文件信息"""
        if not OPT_CONVERTER_AVAILABLE:
            self.log("无法显示OPT文件信息: 未找到opt_converter模块")
            return
        
        # 确保info_text已经初始化
        if not hasattr(self, 'info_text') or not self.info_text:
            return
        
        try:
            opt_data = parse_opt_file(opt_file)
            if not opt_data:
                self.log(f"无法解析OPT文件: {opt_file}")
                return
            
            self.log("=" * 50)
            self.log(f"相机参数信息 ({os.path.basename(opt_file)}):")
            
            # 显示基本信息
            if 'Exif' in opt_data:
                make = opt_data['Exif'].get('Make', 'Unknown')
                model = opt_data['Exif'].get('Model', 'Unknown')
                self.log(f"相机: {make} {model}")
            
            # 显示分辨率和焦距
            width = opt_data.get('Width', 0)
            height = opt_data.get('Height', 0)
            focal_length = opt_data.get('FocalLength', 0)
            sensor_size = opt_data.get('SensorSize', 0)
            self.log(f"传感器尺寸: {sensor_size}mm")
            self.log(f"分辨率: {width} x {height}")
            self.log(f"焦距: {focal_length:.2f}mm")
            
            # 计算35mm等效焦距
            if sensor_size > 0:
                equiv_focal = focal_length * (35.0 / sensor_size)
                self.log(f"35mm等效焦距: {equiv_focal:.2f}mm")
            
            # 显示畸变参数
            if 'Distortion' in opt_data:
                self.log(f"畸变参数:")
                k1 = opt_data['Distortion'].get('K1', 0)
                k2 = opt_data['Distortion'].get('K2', 0)
                k3 = opt_data['Distortion'].get('K3', 0)
                p1 = opt_data['Distortion'].get('P1', 0)
                p2 = opt_data['Distortion'].get('P2', 0)
                self.log(f"  K1={k1:.8f}, K2={k2:.8f}, K3={k3:.8f}")
                self.log(f"  P1={p1:.8f}, P2={p2:.8f}")
            
            self.log("=" * 50)
        except Exception as e:
            self.log(f"读取OPT文件失败: {e}")
        
    def process_images_with_mapping(self):
        """使用自定义列映射处理图片"""
        if not self.csv_path.get() or not self.image_folder.get():
            messagebox.showerror("错误", "请先选择CSV文件和图片文件夹！")
            return
        
        if not self.csv_column_mapping.get('filename'):
            messagebox.showerror("错误", "请先设置CSV列映射！")
            return
        
        def process_task():
            try:
                self.log("=" * 50)
                self.log("开始处理图片...")
                self.status_label.config(text="处理中...", foreground="orange")
                self.progress.config(value=0)
                
                # 读取CSV文件
                df = pd.read_csv(self.csv_path.get(), encoding='utf-8-sig')
                
                # 如果没有表头，使用列号
                if not self.csv_column_mapping['has_header']:
                    column_count = len(df.columns)
                    df.columns = [f"列{i+1}" for i in range(column_count)]
                
                total_rows = len(df)
                success_count = 0
                failed_count = 0
                
                for index, row in df.iterrows():
                    if self.should_stop:
                        self.log("处理已停止")
                        break
                    
                    try:
                        # 根据用户映射提取数据
                        filename = str(row[self.csv_column_mapping['filename']]).strip()
                        latitude = float(row[self.csv_column_mapping['latitude']])
                        longitude = float(row[self.csv_column_mapping['longitude']])
                        
                        # 海拔是可选的
                        altitude = 0
                        if self.csv_column_mapping['altitude']:
                            try:
                                altitude = float(row[self.csv_column_mapping['altitude']])
                            except:
                                altitude = 0
                        
                        if not filename:
                            self.log(f"第{index+1}行: 文件名为空，跳过")
                            continue
                        
                        # 构建图片路径
                        image_path = os.path.join(self.image_folder.get(), filename)
                        if not os.path.isfile(image_path):
                            if not image_path.lower().endswith(('.jpg', '.jpeg')):
                                image_path = f"{image_path}.jpg"
                            
                            if not os.path.isfile(image_path):
                                self.log(f"第{index+1}行: 文件不存在: {filename}")
                                failed_count += 1
                                continue
                        
                        # 处理图像
                        self.log(f"第{index+1}行: 处理 {filename} ({latitude:.6f}, {longitude:.6f})")
                        
                        # 确定输出路径
                        output_path = None
                        if self.output_folder.get():
                            output_path = os.path.join(self.output_folder.get(), filename)
                        
                        # 导入处理函数
                        from batch_add_gps_info import set_gps_location
                        
                        if set_gps_location(image_path, latitude, longitude, altitude, 0, 0, 0, 
                                           None, self.opt_file_path.get() if self.opt_file_path.get() else None, 
                                           output_path):
                            success_count += 1
                            if output_path:
                                self.log(f"  ✅ 成功 (已保存至: {os.path.basename(self.output_folder.get())})")
                            else:
                                self.log(f"  ✅ 成功")
                        else:
                            failed_count += 1
                            self.log(f"  ❌ 失败")
                        
                        # 更新进度
                        progress = (index + 1) / total_rows * 100
                        self.progress.config(value=progress)
                        self.root.update()
                        
                    except Exception as e:
                        failed_count += 1
                        self.log(f"第{index+1}行: 错误 - {str(e)}")
                
                self.log("=" * 50)
                self.log(f"处理完成: 成功={success_count}, 失败={failed_count}")
                self.status_label.config(text=f"完成: 成功{success_count}个, 失败{failed_count}个", 
                                       foreground="green" if failed_count == 0 else "orange")
                
            except Exception as e:
                self.log(f"❌ 处理失败: {str(e)}")
                self.status_label.config(text="处理失败", foreground="red")
            
            finally:
                self.processing = False
                self.process_button.config(text="开始处理")
        
        # 启动处理线程
        self.processing = True
        self.should_stop = False
        self.process_button.config(text="停止处理")
        thread = threading.Thread(target=process_task)
        thread.daemon = True
        thread.start()
    
    def log(self, message):
        """添加日志消息"""
        # 确保info_text已经初始化
        if hasattr(self, 'info_text') and self.info_text:
            # 根据消息类型设置不同颜色
            tag = None
            
            if isinstance(message, str):
                if message.startswith("✅") or "成功" in message:
                    tag = "success"
                elif message.startswith("❌") or "失败" in message or "错误" in message:
                    tag = "error"
                elif message.startswith("⚠️") or "警告" in message:
                    tag = "warning"
                elif message.startswith("=") or message.startswith("-"):
                    tag = "separator"
                elif "开始" in message:
                    tag = "info"
            
            # 插入文本
            self.info_text.insert(tk.END, message + "\n", tag if tag else "")
            # 插入文本
            self.info_text.insert(tk.END, message + "\n", tag if tag else "")
            self.info_text.see(tk.END)
            
            try:
                self.root.update()
            except:
                pass  # 防止界面更新时出错
    
    def clear_log(self):
        """清空日志"""
        if hasattr(self, 'info_text') and self.info_text:
            self.info_text.delete(1.0, tk.END)
    
    def update_status(self, message, color="black"):
        """更新状态栏"""
        self.status_label.config(text=message, foreground=color)
        try:
            self.root.update()
        except:
            pass  # 防止界面更新时出错
    
    def preview_files(self):
        """预览文件信息"""
        csv_file = self.csv_path.get()
        image_dir = self.image_folder.get()
        
        if not csv_file or not image_dir:
            messagebox.showwarning("警告", "请先选择CSV文件和图片文件夹")
            return
        
        if not os.path.exists(csv_file):
            messagebox.showerror("错误", "CSV文件不存在")
            return
        
        if not os.path.exists(image_dir):
            messagebox.showerror("错误", "图片文件夹不存在")
            return
        
        try:
            self.log("=" * 50)
            self.log("开始预览文件信息...")
            
            # 检测CSV格式
            csv_format = detect_csv_format(csv_file)
            self.log(f"CSV格式: {csv_format}")
            
            # 读取CSV文件
            df = pd.read_csv(csv_file, header=None if csv_format == 'no_header' else 0)
            csv_count = len(df)
            self.log(f"CSV文件记录数: {csv_count}")
            
            # 显示前5行CSV数据
            self.log("CSV数据预览 (前5行):")
            for i, row in df.head().iterrows():
                if csv_format == 'no_header':
                    # 无表头格式：显示完整数据包括姿态角
                    filename = row[0] if len(row) > 0 else "N/A"
                    timestamp = row[1] if len(row) > 1 else "N/A"
                    longitude = row[2] if len(row) > 2 else "N/A"
                    latitude = row[3] if len(row) > 3 else "N/A"
                    altitude = row[4] if len(row) > 4 else "N/A"
                    pitch = row[5] if len(row) > 5 else "N/A"
                    roll = row[6] if len(row) > 6 else "N/A"
                    yaw = row[7] if len(row) > 7 else "N/A"
                    
                    self.log(f"  {i+1}: {filename} | {timestamp}")
                    self.log(f"     经度:{longitude} 纬度:{latitude} 高度:{altitude}")
                    self.log(f"     Pitch:{pitch} Roll:{roll} Yaw:{yaw}")
                else:
                    # 有表头格式：显示完整数据
                    filename = row.iloc[0] if len(row) > 0 else "N/A"
                    timestamp = row.iloc[1] if len(row) > 1 else "N/A"
                    longitude = row.iloc[2] if len(row) > 2 else "N/A"
                    latitude = row.iloc[3] if len(row) > 3 else "N/A"
                    altitude = row.iloc[4] if len(row) > 4 else "N/A"
                    pitch = row.iloc[5] if len(row) > 5 else "N/A"
                    roll = row.iloc[6] if len(row) > 6 else "N/A"
                    yaw = row.iloc[7] if len(row) > 7 else "N/A"
                    
                    self.log(f"  {i+1}: {filename} | {timestamp}")
                    self.log(f"     经度:{longitude} 纬度:{latitude} 高度:{altitude}")
                    self.log(f"     Pitch:{pitch} Roll:{roll} Yaw:{yaw}")
            
            # 统计图片文件
            image_files = [f for f in os.listdir(image_dir)
                           if f.lower().endswith(('.jpg', '.jpeg'))]
            image_count = len(image_files)
            self.log(f"图片文件数量: {image_count}")
            
            # 匹配分析
            if csv_format == 'no_header':
                csv_files = df[0].tolist()  # 第一列是文件名
            else:
                csv_files = df.iloc[:, 0].tolist()  # 第一列是文件名
            
            matched = []
            unmatched_csv = []
            unmatched_images = []
            
            for csv_file_name in csv_files:
                if csv_file_name in image_files:
                    matched.append(csv_file_name)
                else:
                    unmatched_csv.append(csv_file_name)
                
            for image_file in image_files:
                if image_file not in csv_files:
                    unmatched_images.append(image_file)
            
            # 显示匹配结果
            self.log(f"\n匹配结果:")
            if len(matched) == csv_count == image_count:
                self.log(f"✅ 完美匹配: {len(matched)} 个文件")
                self.update_status("文件匹配完美", "green")
            else:
                self.log(f"⚠️  匹配文件: {len(matched)} 个")
                if unmatched_csv:
                    self.log(f"❌ CSV中无对应图片: {len(unmatched_csv)} 个")
                if unmatched_images:
                    self.log(f"❌ 图片无对应CSV: {len(unmatched_images)} 个")
                self.update_status("文件匹配不完整", "orange")
            
            self.log("预览完成")
        
        except Exception as e:
            error_msg = f"预览失败: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("错误", error_msg)
            self.update_status("预览失败", "red")

    def toggle_processing(self):
        """切换处理状态：开始/停止处理"""
        if self.processing:
            # 正在处理，点击按钮表示停止
            self.stop_processing()
        else:
            # 未在处理，开始新的处理
            self.start_processing()

    def stop_processing(self):
        """停止正在进行的处理"""
        # 设置停止标志（在线程中检测该标志）
        self.should_stop = True
        self.process_button.config(text="正在停止...", state="disabled")
        self.log("正在停止处理，请等待当前操作完成...")
        
    def start_processing(self):
        """开始处理（在新线程中运行）"""
        if self.processing:
            return
        
        # 检查是否已设置列映射
        if not self.csv_column_mapping.get('filename'):
            messagebox.showwarning("警告", "请先选择CSV文件并设置列映射")
            return
        
        csv_file = self.csv_path.get()
        image_dir = self.image_folder.get()
        
        if not csv_file or not image_dir:
            messagebox.showwarning("警告", "请先选择CSV文件和图片文件夹")
            return
        
        # 使用自定义列映射处理
        self.process_images_with_mapping()

def main():
    """主函数"""
    try:
        print("启动应用程序...")
        root = tk.Tk()
        
        # 设置窗口样式和位置
        root.configure(bg="#F8F9FA")  # 设置背景色
        
        # 让窗口在屏幕中央显示
        window_width = 1000
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        print("创建应用实例...")
        # 创建应用实例
        app = GPSPhotoApp(root)
        
        # 界面初始化完成后显示默认OPT文件信息
        if app.opt_file_path.get():
            root.after(500, lambda: app.show_opt_info(app.opt_file_path.get()))
        
        # 显示欢迎信息
        app.log("=" * 50)
        app.log("欢迎使用GPS照片批量添加工具")
        app.log("使用步骤:")
        app.log("1. 选择相机参数文件 (.opt)")
        app.log("2. 选择CSV数据文件")
        app.log("3. 选择原始图片文件夹")
        app.log("4. 选择处理后照片的导出位置")
        app.log("5. 点击'预览文件'检查数据匹配")
        app.log("6. 点击'开始处理'进行批量处理")
        app.log("=" * 50)
        
        print("启动主循环...")
        root.mainloop()
        return 0
    except Exception as e:
        import traceback
        print(f"程序启动时发生错误: {e}")
        print("错误详情:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
