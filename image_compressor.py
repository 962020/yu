#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片超级压缩工具
功能：压缩图片并交互式生成前端HTML文件展示压缩结果
"""

import os
import sys
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps
import time
from datetime import datetime
import webbrowser
import threading
import queue

def compress_image(image_path, output_path=None, quality=85, max_width=None, max_height=None, convert_to_jpg=False, target_size_kb=None):
    """
    压缩单个图片
    
    参数:
        image_path: 原始图片路径
        output_path: 输出图片路径，如果为None则在原始文件名后添加_compressed
        quality: 压缩质量 (0-100)
        max_width: 最大宽度，None表示不限制
        max_height: 最大高度，None表示不限制
        convert_to_jpg: 是否转换为JPG格式
    
    返回:
        (压缩后路径, 压缩率, 原始大小KB, 压缩后大小KB)
    """
    try:
        # 获取原始文件大小
        original_size = os.path.getsize(image_path) / 1024  # KB
        
        # 打开图片
        img = Image.open(image_path)
        
        # 调整图片大小
        if max_width or max_height:
            img.thumbnail((max_width or img.width, max_height or img.height), Image.LANCZOS)
        
        # 确定输出路径
        if not output_path:
            name, ext = os.path.splitext(image_path)
            output_path = f"{name}_compressed{'.jpg' if convert_to_jpg else ext}"
        
        # 处理透明度
        if img.mode == 'RGBA' and (convert_to_jpg or output_path.lower().endswith('.jpg')):
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            # 粘贴图片到背景上
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = background
        
        # 如果指定了目标大小，使用二分法找到合适的质量
        if target_size_kb and target_size_kb < original_size:
            # 确定文件格式
            if convert_to_jpg or output_path.lower().endswith('.jpg'):
                format_type = 'JPEG'
            elif output_path.lower().endswith('.png'):
                format_type = 'PNG'
            elif output_path.lower().endswith('.webp'):
                format_type = 'WEBP'
            else:
                format_type = img.format
            
            # 二分查找合适的质量
            low, high = 1, 100
            best_quality = quality
            best_size = float('inf')
            
            # 最多尝试10次
            for _ in range(10):
                current_quality = (low + high) // 2
                
                # 保存图片
                if format_type == 'JPEG':
                    img.save(output_path, 'JPEG', quality=current_quality, optimize=True, progressive=True)
                elif format_type == 'PNG':
                    img.save(output_path, 'PNG', quality=current_quality, optimize=True)
                elif format_type == 'WEBP':
                    img.save(output_path, 'WEBP', quality=current_quality, method=6)
                else:
                    img.save(output_path, quality=current_quality, optimize=True)
                
                # 检查大小
                current_size = os.path.getsize(output_path) / 1024
                
                # 更新最佳结果
                if abs(current_size - target_size_kb) < abs(best_size - target_size_kb):
                    best_size = current_size
                    best_quality = current_quality
                
                # 如果已经满足目标大小，退出循环
                if current_size <= target_size_kb:
                    break
                
                # 调整二分范围
                high = current_quality - 1
            
            # 如果仍然太大，尝试进一步降低质量
            if best_size > target_size_kb:
                # 最后尝试更低质量
                img.save(output_path, format_type, quality=1, optimize=True)
                current_size = os.path.getsize(output_path) / 1024
                if current_size > target_size_kb:
                    # 如果还是太大，尝试降低尺寸
                    scale_factor = (target_size_kb / current_size) ** 0.5
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    if new_width > 100 and new_height > 100:  # 确保图片不会太小
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                        img.save(output_path, format_type, quality=1, optimize=True)
        else:
            # 常规压缩，使用指定质量
            if convert_to_jpg or output_path.lower().endswith('.jpg'):
                img.save(output_path, 'JPEG', quality=quality, optimize=True, progressive=True)
            elif output_path.lower().endswith('.png'):
                img.save(output_path, 'PNG', quality=quality, optimize=True)
            elif output_path.lower().endswith('.webp'):
                img.save(output_path, 'WEBP', quality=quality, method=6)
            else:
                img.save(output_path, quality=quality, optimize=True)
        
        # 获取压缩后文件大小
        compressed_size = os.path.getsize(output_path) / 1024  # KB
        
        # 计算压缩率
        compression_rate = 100 - (compressed_size / original_size * 100)
        
        return output_path, compression_rate, original_size, compressed_size
    
    except Exception as e:
        print(f"压缩图片时出错: {e}")
        return None, None, None, None

def batch_compress_images(image_paths, output_dir=None, quality=85, max_width=None, max_height=None, convert_to_jpg=False, target_size_kb=None):
    """
    批量压缩图片
    
    参数:
        image_paths: 图片路径列表
        output_dir: 输出目录
        quality: 压缩质量
        max_width: 最大宽度
        max_height: 最大高度
        convert_to_jpg: 是否转换为JPG
    
    返回:
        压缩结果列表 [(原始路径, 压缩后路径, 压缩率, 原始大小, 压缩后大小)]
    """
    results = []
    
    for image_path in image_paths:
        # 确定输出路径
        if output_dir:
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_compressed{'.jpg' if convert_to_jpg else ext}")
        else:
            output_path = None
        
        # 压缩图片
        comp_path, rate, orig_size, comp_size = compress_image(
            image_path, output_path, quality, max_width, max_height, convert_to_jpg, target_size_kb
        )
        
        if comp_path:
            results.append((image_path, comp_path, rate, orig_size, comp_size))
    
    return results



class ImageCompressorApp:
    """
    图片压缩工具的GUI应用
    """
    def __init__(self, root):
        self.root = root
        self.root.title("图片超级压缩工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置主窗口的minsize
        self.root.minsize(600, 500)
        
        # 设置中文字体
        self.style = ttk.Style()
        self.style.configure("TLabel", font=('SimHei', 10))
        self.style.configure("TButton", font=('SimHei', 10))
        self.style.configure("TCheckbutton", font=('SimHei', 10))
        
        # 存储选择的图片路径
        self.image_paths = []
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """
        创建用户界面
        """
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图片选择区域
        select_frame = ttk.LabelFrame(main_frame, text="选择图片", padding="15")
        select_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(select_frame, text="选择单个图片", command=self.select_single_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(select_frame, text="选择多个图片", command=self.select_multiple_images).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(select_frame, text="选择文件夹", command=self.select_directory).pack(side=tk.LEFT)
        
        # 选择的图片列表
        list_frame = ttk.LabelFrame(main_frame, text="已选择的图片", padding="15")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 列表视图
        columns = ("name", "path", "size")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.tree.heading("name", text="文件名")
        self.tree.heading("path", text="路径")
        self.tree.heading("size", text="大小")
        
        # 设置列宽，使用stretch参数允许列拉伸
        self.tree.column("name", width=150, stretch=True)
        self.tree.column("path", width=350, stretch=True, minwidth=200)
        self.tree.column("size", width=100, stretch=False)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 移除按钮
        ttk.Button(list_frame, text="移除选中图片", command=self.remove_selected_images).pack(side=tk.RIGHT, pady=(10, 0))
        ttk.Button(list_frame, text="清空列表", command=self.clear_image_list).pack(side=tk.RIGHT, pady=(10, 0), padx=(0, 10))
        
        # 压缩设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="压缩设置", padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 质量设置
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10), expand=False)
        
        ttk.Label(quality_frame, text="压缩质量: ").pack(side=tk.LEFT)
        self.quality_var = tk.IntVar(value=85)
        ttk.Scale(quality_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.quality_var, 
                 command=lambda x: self.quality_label.config(text=f"{self.quality_var.get()}%")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self.quality_label = ttk.Label(quality_frame, text=f"{self.quality_var.get()}%")
        self.quality_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 尺寸设置
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(fill=tk.X, pady=(0, 10), expand=False)
        
        ttk.Label(size_frame, text="最大宽度 (像素): ").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="")
        ttk.Entry(size_frame, textvariable=self.width_var, width=10).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(size_frame, text="最大高度 (像素): ").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="")
        ttk.Entry(size_frame, textvariable=self.height_var, width=10).pack(side=tk.LEFT)
        
        # 目标大小设置
        target_frame = ttk.LabelFrame(main_frame, text="目标大小设置（可选）", padding="15")
        target_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.use_target_size_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(target_frame, text="使用目标文件大小", variable=self.use_target_size_var, 
                       command=self.toggle_target_size).pack(anchor=tk.W, pady=(0, 10))
        
        target_input_frame = ttk.Frame(target_frame)
        target_input_frame.pack(fill=tk.X)
        
        ttk.Label(target_input_frame, text="目标大小: ").pack(side=tk.LEFT)
        self.target_size_var = tk.StringVar(value="")
        self.target_size_entry = ttk.Entry(target_input_frame, textvariable=self.target_size_var, width=10)
        self.target_size_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.target_unit_var = tk.StringVar(value="KB")
        ttk.Combobox(target_input_frame, textvariable=self.target_unit_var, values=["KB", "MB"], width=5).pack(side=tk.LEFT)
        
        # 初始禁用目标大小输入
        self.target_size_entry.config(state="disabled")
        
        # 配置列权重，使表格列能够自适应窗口大小
        self.tree.grid_columnconfigure(0, weight=1)
        self.tree.grid_columnconfigure(1, weight=3)  # 路径列权重更大
        self.tree.grid_columnconfigure(2, weight=0)
        
        # 格式固定为JPG
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=(0, 10), expand=False)
        
        self.convert_jpg_var = tk.BooleanVar(value=True)  # 固定为True
        ttk.Label(format_frame, text="格式固定为JPG").pack(side=tk.LEFT)
        
        # 输出设置
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="15")
        output_frame.pack(fill=tk.X, pady=(0, 15), expand=False)
        
        ttk.Label(output_frame, text="输出目录: ").pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar(value="./")
        ttk.Entry(output_frame, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        ttk.Button(output_frame, text="浏览", command=self.select_output_directory).pack(side=tk.LEFT)
        

        
        # 执行按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="开始压缩", command=self.start_compression, style="Accent.TButton").pack(side=tk.RIGHT)
        
        # 配置强调按钮样式
        self.style.configure("Accent.TButton", font=('SimHei', 12, 'bold'))
        
        # 初始化目标大小控件状态
        self.toggle_target_size()
    
    def select_single_image(self):
        """
        选择单个图片
        """
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("JPEG图片", "*.jpg *.jpeg"),
                ("PNG图片", "*.png"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path and file_path not in self.image_paths:
            self.image_paths.append(file_path)
            self.update_image_list()
    
    def select_multiple_images(self):
        """
        选择多个图片
        """
        file_paths = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("JPEG图片", "*.jpg *.jpeg"),
                ("PNG图片", "*.png"),
                ("所有文件", "*.*")
            ]
        )
        
        for file_path in file_paths:
            if file_path not in self.image_paths:
                self.image_paths.append(file_path)
        
        if file_paths:
            self.update_image_list()
    
    def select_directory(self):
        """
        选择文件夹中的所有图片
        """
        directory = filedialog.askdirectory(title="选择图片文件夹")
        
        if directory:
            # 支持的图片扩展名
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            
            # 获取文件夹中的所有图片文件
            new_image_paths = []
            for root, _, files in os.walk(directory):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in image_extensions:
                        file_path = os.path.join(root, file)
                        if file_path not in self.image_paths:
                            new_image_paths.append(file_path)
            
            # 更新图片列表
            self.image_paths.extend(new_image_paths)
            if new_image_paths:
                self.update_image_list()
                messagebox.showinfo("成功", f"已添加 {len(new_image_paths)} 张图片")
    
    def update_image_list(self):
        """
        更新图片列表视图
        """
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加图片
        for file_path in self.image_paths:
            filename = os.path.basename(file_path)
            size_kb = os.path.getsize(file_path) / 1024
            self.tree.insert("", tk.END, values=(filename, file_path, f"{size_kb:.2f} KB"))
    
    def remove_selected_images(self):
        """
        移除选中的图片
        """
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要移除的图片")
            return
        
        # 获取要移除的路径
        to_remove = []
        for item in selected_items:
            path = self.tree.item(item, "values")[1]
            to_remove.append(path)
        
        # 移除图片
        for path in to_remove:
            if path in self.image_paths:
                self.image_paths.remove(path)
        
        # 更新列表
        self.update_image_list()
    
    def clear_image_list(self):
        """
        清空图片列表
        """
        if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
            self.image_paths.clear()
            self.update_image_list()
    
    def select_output_directory(self):
        """
        选择输出目录
        """
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
    
    def toggle_target_size(self):
        """
        切换目标大小输入框的启用状态
        """
        if self.use_target_size_var.get():
            self.target_size_entry.config(state="normal")
        else:
            self.target_size_entry.config(state="disabled")
    
    def start_compression(self):
        """
        开始压缩图片
        """
        # 检查是否选择了图片
        if not self.image_paths:
            messagebox.showinfo("提示", "请先选择要压缩的图片")
            return
        
        # 获取压缩设置
        quality = self.quality_var.get()
        
        # 获取尺寸设置
        try:
            max_width = int(self.width_var.get()) if self.width_var.get().strip() else None
        except ValueError:
            messagebox.showerror("错误", "最大宽度必须是数字")
            return
        
        try:
            max_height = int(self.height_var.get()) if self.height_var.get().strip() else None
        except ValueError:
            messagebox.showerror("错误", "最大高度必须是数字")
            return
        
        # 获取目标大小设置
        target_size_kb = None
        if self.use_target_size_var.get():
            if self.target_size_var.get().strip():
                try:
                    target_size = float(self.target_size_var.get())
                    unit = self.target_unit_var.get()
                    # 转换为KB
                    if unit == "MB":
                        target_size_kb = target_size * 1024
                    else:
                        target_size_kb = target_size
                except ValueError:
                    messagebox.showerror("错误", "目标大小必须是数字")
                    return
        
        convert_to_jpg = True  # 固定转换为JPG格式
        output_dir = self.output_dir_var.get()

        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"创建输出目录失败: {e}")
                return
        
        # 显示进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("压缩进度")
        progress_window.geometry("400x120")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        # 确保进度窗口在屏幕中央
        progress_window.update_idletasks()
        width = progress_window.winfo_width()
        height = progress_window.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        progress_window.geometry(f"{width}x{height}+{x}+{y}")
        
        ttk.Label(progress_window, text="正在压缩图片，请稍候...").pack(pady=(20, 10))
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(self.image_paths))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(progress_window, text="准备开始...")
        status_label.pack(pady=5)
        
        # 确保进度窗口显示
        progress_window.update()
        
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        # 定义压缩线程函数
        def compression_thread():
            results = []
            error = None
            try:
                for i, image_path in enumerate(self.image_paths):
                    # 更新状态
                    filename = os.path.basename(image_path)
                    result_queue.put(('status', f"压缩 {i+1}/{len(self.image_paths)}: {filename}"))
                    result_queue.put(('progress', i + 1))
                    
                    # 压缩图片
                    comp_path, rate, orig_size, comp_size = compress_image(
                        image_path, output_path=os.path.join(output_dir, os.path.basename(image_path) + "_compressed" + 
                                                            (".jpg" if convert_to_jpg else os.path.splitext(image_path)[1])),
                        quality=quality, max_width=max_width, max_height=max_height, convert_to_jpg=convert_to_jpg,
                        target_size_kb=target_size_kb
                    )
                    
                    if comp_path:
                        results.append((image_path, comp_path, rate, orig_size, comp_size))
                
                # 发送结果
                result_queue.put(('results', results, output_dir))
                
            except Exception as e:
                error = str(e)
                result_queue.put(('error', error))
            finally:
                result_queue.put(('done',))
        
        # 开始压缩线程
        thread = threading.Thread(target=compression_thread)
        thread.daemon = True
        thread.start()
        
        # 定义更新进度的函数
        def update_progress():
            try:
                # 检查队列中是否有消息
                while not result_queue.empty():
                    message = result_queue.get_nowait()
                    
                    if message[0] == 'status':
                        status_label.config(text=message[1])
                    elif message[0] == 'progress':
                        progress_var.set(message[1])
                    elif message[0] == 'error':
                        progress_window.destroy()
                        messagebox.showerror("错误", f"压缩过程中出错: {message[1]}")
                        return
                    elif message[0] == 'results':
                        results, out_dir = message[1], message[2]
                        progress_window.destroy()
                        
                        # 显示完成消息
                        messagebox.showinfo("完成", f"成功压缩 {len(results)} 张图片！")
                        return
                    elif message[0] == 'done':
                        progress_window.destroy()
                        return
                
                # 更新界面
                progress_window.update()
                
                # 继续检查队列，直到线程完成
                if thread.is_alive():
                    progress_window.after(100, update_progress)  # 每100毫秒检查一次
                else:
                    # 确保所有消息都被处理
                    update_progress()
                    
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("错误", f"更新进度时出错: {e}")
        
        # 开始更新进度
        update_progress()

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='图片超级压缩工具')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--input', '-i', help='输入图片路径或目录')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--quality', '-q', type=int, default=85, help='压缩质量 (0-100)')
    parser.add_argument('--width', '-w', type=int, help='最大宽度')
    parser.add_argument('--height', '-H', type=int, help='最大高度')
    # 格式固定为JPG，不再提供选项

    parser.add_argument('--target-size', type=float, help='目标文件大小')
    parser.add_argument('--target-unit', choices=['KB', 'MB'], default='KB', help='目标文件大小单位')
    
    args = parser.parse_args()
    
    # 如果是命令行模式
    if args.cli:
        if not args.input:
            parser.error('命令行模式需要指定输入文件或目录')
        
        # 获取图片列表
        image_paths = []
        if os.path.isdir(args.input):
            # 支持的图片扩展名
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            
            for root, _, files in os.walk(args.input):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in image_extensions:
                        image_paths.append(os.path.join(root, file))
        else:
            image_paths = [args.input]
        
        if not image_paths:
            print("未找到图片文件")
            return
        
        # 计算目标大小（转换为KB）
        target_size_kb = None
        if args.target_size:
            if args.target_unit == 'MB':
                target_size_kb = args.target_size * 1024
            else:
                target_size_kb = args.target_size
        
        # 压缩图片
        print(f"找到 {len(image_paths)} 张图片，开始压缩...")
        if target_size_kb:
            print(f"目标大小: {args.target_size} {args.target_unit}")
        results = batch_compress_images(
            image_paths, args.output, args.quality, args.width, args.height, True, target_size_kb  # 固定转换为JPG
        )
        
        # 显示结果
        if results:
            print(f"\n成功压缩 {len(results)} 张图片：")
            total_original = sum(r[3] for r in results)
            total_compressed = sum(r[4] for r in results)
            
            for orig, comp, rate, orig_size, comp_size in results:
                print(f"{os.path.basename(orig)}: {orig_size:.2f}KB → {comp_size:.2f}KB ({rate:.2f}% 压缩率)")
            
            print(f"\n总压缩率: {100 - (total_compressed / total_original * 100):.2f}%")
            print(f"节省空间: {(total_original - total_compressed):.2f}KB")
            

        else:
            print("压缩失败")
    
    # GUI模式
    else:
        # 确保中文显示正常
        root = tk.Tk()
        app = ImageCompressorApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()