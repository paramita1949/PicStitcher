import os
import re
import json  # 新增
from pathlib import Path
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

def extract_info(filename):
    """从文件名中提取歌曲编号、歌名和页码"""
    # 使用 pathlib 获取文件名（无扩展名）
    file_stem = Path(filename).stem
    
    # 原有的正则表达式模式
    pattern1 = r'第(\d+)首\s+(.+?)(\d+)$'
    match = re.match(pattern1, file_stem)
    if match:
        song_number = match.group(1)
        song_name = match.group(2).strip()
        page_number = int(match.group(3))
        return song_number, song_name, page_number
    
    # 新增的正则表达式模式，匹配"001.圣哉三一歌1"这样的格式
    pattern2 = r'(\d+)\.(.+?)(\d+)$'
    match = re.match(pattern2, file_stem)
    if match:
        song_number = match.group(1)
        song_name = match.group(2).strip()
        page_number = int(match.group(3))
        return song_number, song_name, page_number
    
    # 新增模式，匹配"第0707愿将我的心给你1"这样的格式
    pattern3 = r'第(\d+)([^0-9].+?)(\d+)$'
    match = re.match(pattern3, file_stem)
    if match:
        song_number = match.group(1)
        song_name = match.group(2).strip()
        page_number = int(match.group(3))
        return song_number, song_name, page_number
    
    return None

def vertical_concat_images(image_paths):
    """竖向拼接图片"""
    # 打开所有图片
    images = []
    for i, path in enumerate(image_paths):
        try:
            img = Image.open(path)
            img.load()  # 确保图像已加载
            images.append(img)
        except Exception as e:
            # 继续处理其他图片
            pass
    
    if not images:
        raise ValueError("无有效图片可拼接")
    
    # 找到最大宽度
    max_width = max(img.width for img in images)
    
    # 计算总高度
    total_height = sum(img.height for img in images)
    
    # 创建新图像
    result_img = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))
    
    # 粘贴图片
    y_offset = 0
    for i, img in enumerate(images):
        # 如果图片宽度小于最大宽度，居中放置
        x_offset = (max_width - img.width) // 2
        result_img.paste(img, (x_offset, y_offset))
        y_offset += img.height
    
    return result_img

def apply_yellow_text_effect(image, text_r=187, text_g=159, text_b=97):
    """应用黄字效果（黑底黄字，底色强制纯黑）"""
    try:
        # 转换为RGBA模式，便于处理透明度
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        img_array = np.array(image)

        # 计算亮度，判断文本区域
        luminance = np.mean(img_array[..., :3], axis=2)
        is_text = luminance < 150  # 阈值可调整

        # 新建黑底图像（强制纯黑）
        result = np.zeros_like(img_array)
        result[..., :3] = 0
        result[..., 3] = 255

        # 使用传入的RGB值设置文字颜色
        result[is_text, 0] = text_r  # R
        result[is_text, 1] = text_g  # G
        result[is_text, 2] = text_b  # B
        # 深棕黄色备选方案（注释保留）
        # result[is_text, 0] = 204  # R
        # result[is_text, 1] = 153  # G
        # result[is_text, 2] = 0   # B
        result[is_text, 3] = img_array[is_text, 3]  # 保留原透明度

        # 保留原图透明区域
        transparent_mask = img_array[..., 3] == 0
        result[transparent_mask, 3] = 0

        return Image.fromarray(result)
    except Exception as e:
        print(f"应用黄字效果失败: {e}")
        return image

def process_images(folder_path, output_folder, invert=False, text_r=187, text_g=159, text_b=97):
    """处理文件夹中的图片并按规则拼接，可选择是否反色处理"""
    # 转换为 Path 对象
    folder_path = Path(folder_path)
    output_folder = Path(output_folder)
    
    # 确保输出文件夹存在
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 获取所有图片文件
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    image_files = [f.name for f in folder_path.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    # 按歌名分组
    song_groups = {}
    for img_file in image_files:
        info = extract_info(img_file)
        if info:
            song_number, song_name, page_number = info
            key = f"{song_number}_{song_name}"
            if key not in song_groups:
                song_groups[key] = []
            song_groups[key].append((page_number, folder_path / img_file))
    
    # 处理每个歌曲组
    for key, images in song_groups.items():
        if len(images) > 1:  # 只处理有多个页面的歌曲
            # 按页码排序
            images.sort(key=lambda x: x[0])
            
            # 获取图片路径列表
            image_paths = [str(img[1]) for img in images]
            
            # 拼接图片
            result_img = vertical_concat_images(image_paths)
            
            # 如果需要反色处理
            if invert:
                result_img = apply_yellow_text_effect(result_img, text_r, text_g, text_b)
            
            # 保存结果
            song_number, song_name = key.split('_', 1)
            suffix = "_反色拼接" if invert else "_拼接"
            output_filename = f"第{song_number}首_{song_name}{suffix}.jpg"
            output_path = output_folder / output_filename
            result_img.save(output_path, quality=95)

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量拼接与反色处理工具-教会版V1.1")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # 获取配置文件路径，兼容打包后的EXE
        self.config_path = self.get_config_path()
        self.input_folder = ""
        self.output_folder = ""
        
        # 黄字效果RGB默认值（淡棕黄色）
        self.yellow_text_r = 187
        self.yellow_text_g = 159
        self.yellow_text_b = 97
        
        # 用于实际处理逻辑的变量
        self.invert = tk.BooleanVar(value=False)
        self.only_invert = tk.BooleanVar(value=False)
        self.only_concat = tk.BooleanVar(value=True)  # 默认选择仅拼接
        
        self.create_widgets()
        self.load_config()  # 初始化时加载配置
        
        # 确保模式选择和内部变量一致
        self.update_mode()

    def get_config_path(self):
        """获取配置文件路径，兼容打包后的EXE环境"""
        try:
            import sys
            
            # 检查是否是打包后的可执行文件
            if getattr(sys, 'frozen', False):
                # 打包后的环境，使用可执行文件所在目录
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller 打包
                    exe_dir = Path(sys.executable).parent
                else:
                    # 其他打包工具
                    exe_dir = Path(sys.argv[0]).parent
                config_path = exe_dir / 'config.json'
                print(f"检测到打包环境，配置文件路径: {config_path}")
            else:
                # 开发环境，使用脚本文件所在目录
                config_path = Path(__file__).parent / 'config.json'
                print(f"开发环境，配置文件路径: {config_path}")
            
            return config_path
            
        except Exception as e:
            print(f"获取配置文件路径失败: {e}")
            # 备用方案：使用当前工作目录
            fallback_path = Path.cwd() / 'config.json'
            print(f"使用备用路径: {fallback_path}")
            return fallback_path

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入文件夹选择
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(input_frame, text="输入文件夹:").pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(input_frame, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="浏览...", command=self.browse_input).pack(side=tk.LEFT)
        
        # 输出文件夹选择
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="输出文件夹:").pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(output_frame, width=50)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT)
        
        # 处理选项
        option_frame = ttk.Frame(main_frame)
        option_frame.pack(fill=tk.X, pady=10)
        
        # 创建单独的变量用于Radiobutton
        self.process_mode = tk.StringVar(value="concat")  # 默认为仅拼接
        
        # 创建单选按钮
        ttk.Radiobutton(option_frame, text="反色+拼接", variable=self.process_mode, value="invert_concat",
                        command=self.update_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(option_frame, text="仅反色", variable=self.process_mode, value="invert_only",
                        command=self.update_mode).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(option_frame, text="仅拼接", variable=self.process_mode, value="concat",
                        command=self.update_mode).pack(side=tk.LEFT, padx=10)
        
        # 添加大号运行按钮
        run_button = tk.Button(option_frame, text="运行程序", 
                              command=self.start_processing,
                              font=('Arial', 12, 'bold'),
                              bg='#4CAF50',  # 绿色背景
                              fg='white',    # 白色文字
                              height=2,      # 增加按钮高度
                              width=15)      # 增加按钮宽度
        run_button.pack(side=tk.RIGHT, padx=10)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(fill=tk.X, pady=5)
        
        # 使用更明显的进度条样式
        self.progress = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            style='TProgressbar'
        )
        self.progress.pack(fill=tk.X, ipady=3)  # 增加垂直内边距，使进度条更高
        
        # 尝试配置进度条样式
        try:
            style = ttk.Style()
            style.configure(
                'TProgressbar', 
                thickness=20,                # 增加厚度
                troughcolor='#F0F0F0',      # 进度条背景色
                background='#4CAF50',        # 进度条颜色
                troughrelief=tk.FLAT         # 扁平样式
            )
        except Exception as e:
            print(f"设置进度条样式失败: {e}")
        
        # 日志框
        log_frame = ttk.LabelFrame(main_frame, text="处理日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def load_config(self):
        """加载上次保存的输入输出文件夹路径和黄字效果RGB配置"""
        print(f"🔧 正在加载配置文件: {self.config_path}")
        print(f"配置文件是否存在: {self.config_path.exists()}")
        
        if self.config_path.exists():
            try:
                print("📖 正在读取配置文件...")
                with self.config_path.open('r', encoding='utf-8') as f:
                    cfg = json.load(f)
                
                print(f"📄 配置文件内容: {cfg}")
                
                self.input_folder = cfg.get('input_folder', '')
                self.output_folder = cfg.get('output_folder', '')
                
                # 加载黄字效果RGB配置，如果不存在则使用默认值
                self.yellow_text_r = cfg.get('yellow_text_r', 187)
                self.yellow_text_g = cfg.get('yellow_text_g', 159)
                self.yellow_text_b = cfg.get('yellow_text_b', 97)
                
                print(f"✅ 配置加载成功 - 黄字颜色: RGB({self.yellow_text_r}, {self.yellow_text_g}, {self.yellow_text_b})")
                
                # 自动填充到输入框
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, self.input_folder)
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, self.output_folder)
                
            except Exception as e:
                print(f"❌ 加载配置失败: {e}")
                # 如果加载失败，创建默认配置文件
                self.create_default_config()
        else:
            # 首次运行，创建默认配置文件
            print("🆕 首次运行，正在创建默认配置文件...")
            self.create_default_config()

    def create_default_config(self):
        """创建默认配置文件"""
        try:
            # 确保目录存在
            config_dir = self.config_path.parent
            config_dir.mkdir(parents=True, exist_ok=True)
            print(f"配置文件目录: {config_dir}")
            print(f"目录是否存在: {config_dir.exists()}")
            print(f"目录是否可写: {config_dir.is_dir() and os.access(config_dir, os.W_OK)}")
            
            default_cfg = {
                'input_folder': '',
                'output_folder': '',
                'yellow_text_r': 187,
                'yellow_text_g': 159,
                'yellow_text_b': 97,
                '_comment': '配置说明：yellow_text_r/g/b 为黄字效果的RGB颜色值(0-255)，默认为淡棕黄色'
            }
            
            print(f"准备创建配置文件: {self.config_path}")
            
            with self.config_path.open('w', encoding='utf-8') as f:
                json.dump(default_cfg, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 默认配置文件已创建: {self.config_path}")
            print("您可以编辑config.json来自定义黄字效果的颜色")
            
            # 验证文件是否真的创建成功
            if self.config_path.exists():
                print(f"✅ 配置文件创建验证成功")
            else:
                print(f"❌ 配置文件创建验证失败")
            
        except PermissionError as e:
            print(f"❌ 创建配置文件权限不足: {e}")
            print(f"请确保程序有权限写入目录: {self.config_path.parent}")
        except Exception as e:
            print(f"❌ 创建默认配置文件失败: {e}")
            print(f"配置文件路径: {self.config_path}")
            print(f"错误类型: {type(e).__name__}")

    def save_config(self):
        """保存当前输入输出文件夹路径和黄字效果RGB配置"""
        try:
            cfg = {
                'input_folder': self.input_folder,
                'output_folder': self.output_folder,
                'yellow_text_r': self.yellow_text_r,
                'yellow_text_g': self.yellow_text_g,
                'yellow_text_b': self.yellow_text_b
            }
            with self.config_path.open('w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def browse_input(self):
        folder = filedialog.askdirectory(title="选择输入文件夹")
        if folder:
            self.input_folder = folder
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder)
            self.save_config()  # 选择后保存
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            self.save_config()  # 选择后保存
    
    def log(self, message):
        """添加日志信息到日志框"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def update_progress(self, value, maximum, percent=None):
        """更新进度条和状态"""
        if maximum > 0:
            self.progress['maximum'] = maximum
            self.progress['value'] = min(value, maximum)
            
            if percent is None:
                percent = int((value / maximum) * 100)
            
            self.status_var.set(f"进度: {percent}%")
            # 强制更新界面
            self.root.update_idletasks()
    
    def start_processing(self):
        # 获取输入和输出文件夹
        self.input_folder = self.input_entry.get()
        self.output_folder = self.output_entry.get()
        self.save_config()  # 每次运行前都保存一次
        
        # 验证输入
        if not self.input_folder or not Path(self.input_folder).is_dir():
            messagebox.showerror("错误", "请选择有效的输入文件夹")
            return
        
        if not self.output_folder:
            messagebox.showerror("错误", "请选择输出文件夹")
            return
        
        # 确保输出文件夹存在
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中处理图片，避免界面卡死
        self.status_var.set("正在处理...")
        threading.Thread(target=self.process_in_thread, daemon=True).start()
    
    def process_in_thread(self):
        try:
            # 获取所有图片文件
            input_path = Path(self.input_folder)
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
            image_files = [f.name for f in input_path.iterdir() 
                          if f.is_file() and f.suffix.lower() in image_extensions]
            
            # 确保当前模式与单选按钮选择一致
            mode = self.process_mode.get()
            if mode == "invert_concat" and not self.invert.get():
                self.update_mode()
            elif mode == "invert_only" and not self.only_invert.get():
                self.update_mode()
            elif mode == "concat" and not self.only_concat.get():
                self.update_mode()
            
            if self.only_invert.get():
                # 仅执行反色处理
                # 设置进度条
                total_files = len(image_files)
                self.update_progress(0, total_files, 0)
                
                for i, img_file in enumerate(image_files):
                    input_img_path = input_path / img_file
                    # 保持原始文件名
                    output_img_path = Path(self.output_folder) / img_file
                    
                    # 更新状态
                    self.status_var.set(f"正在处理: {img_file}")
                    
                    try:
                        # 打开图像
                        img = Image.open(input_img_path)
                        img.load()
                        
                        # 执行反色处理
                        inverted_img = apply_yellow_text_effect(img, self.yellow_text_r, self.yellow_text_g, self.yellow_text_b)
                        
                        # 确保图像是RGB模式（没有透明通道）
                        if inverted_img.mode == 'RGBA':
                            inverted_img = inverted_img.convert('RGB')
                        
                        # 保存图像
                        inverted_img.save(output_img_path, quality=95)
                        
                        # 记录日志
                        self.log(f"已反色并保存: {img_file}")
                    except Exception as e:
                        # 记录错误以便调试
                        self.log(f"处理 {img_file} 时出错: {str(e)}")
                    
                    # 更新进度条
                    self.update_progress(i + 1, total_files)
            else:
                # 按歌名分组
                song_groups = {}
                for img_file in image_files:
                    info = extract_info(img_file)
                    if info:
                        song_number, song_name, page_number = info
                        key = f"{song_number}_{song_name}"
                        if key not in song_groups:
                            song_groups[key] = []
                        song_groups[key].append((page_number, input_path / img_file))
                
                # 设置进度条
                total_songs = len(song_groups)
                # 避免除以零错误
                if total_songs == 0:
                    self.log("没有找到可处理的歌曲，请检查文件命名格式")
                    self.update_progress(1, 1, 100)  # 直接设置为完成状态
                else:
                    self.update_progress(0, total_songs, 0)
                
                # 处理每个歌曲组
                processed_count = 0
                for key, images in song_groups.items():
                    # 按页码排序
                    images.sort(key=lambda x: x[0])
                    
                    # 获取图片路径列表
                    image_paths = [img[1] for img in images]
                    
                    # 更新状态
                    song_number, song_name = key.split('_', 1)
                    self.status_var.set(f"正在处理: 第{song_number}首 {song_name}")
                    
                    # 如果只有一张图片且不是仅拼接模式，直接打开它而不是拼接
                    if len(images) == 1 and not self.only_concat.get():
                        try:
                            # 打开图片
                            result_img = Image.open(image_paths[0])
                            result_img.load()
                        except Exception as e:
                            # 跳过这首歌
                            self.log(f"打开图片出错: {str(e)}")
                            continue
                    else:
                        # 拼接图片
                        try:
                            result_img = vertical_concat_images(image_paths)
                        except Exception as e:
                            self.log(f"拼接图片出错: {str(e)}")
                            continue  # 跳过这首歌
                    
                    # 如果需要反色处理（不是仅拼接模式）
                    if self.invert.get() and not self.only_concat.get():
                        try:
                            # 执行反色处理
                            result_img = apply_yellow_text_effect(result_img, self.yellow_text_r, self.yellow_text_g, self.yellow_text_b)
                        except Exception as e:
                            # 但仍然继续处理，保存原始图像
                            self.log(f"反色处理错误: {str(e)}")
                    
                    # 确保图像是RGB模式（没有透明通道）
                    try:
                        if result_img.mode == 'RGBA':
                            result_img = result_img.convert('RGB')
                        
                        # 更新文件命名，恢复原始的命名规则
                        output_filename = f"第{song_number}首 {song_name}.jpg"
                        
                        output_path = Path(self.output_folder) / output_filename
                        result_img.save(output_path, quality=95)
                        
                        # 记录日志
                        if len(images) == 1 and not self.only_concat.get():
                            if self.invert.get():
                                log_msg = f"已反色处理并保存: {output_filename}"
                            else:
                                log_msg = f"已处理并保存: {output_filename}"
                        else:
                            if self.invert.get():
                                log_msg = f"已反色拼接并保存: {output_filename}"
                            elif self.only_concat.get():
                                log_msg = f"已拼接并保存: {output_filename}"
                            else:
                                log_msg = f"已拼接并保存: {output_filename}"
                        self.log(log_msg)
                    except Exception as e:
                        self.log(f"保存图片出错: {str(e)}")
                    
                    # 更新进度条
                    processed_count += 1
                    self.update_progress(processed_count, total_songs)
            
            # 确保进度条显示100%完成
            if self.progress['maximum'] > 0:  # 避免除以零错误
                self.update_progress(self.progress['maximum'], self.progress['maximum'], 100)
                
                # 只在状态栏显示完成信息
                self.root.after(500, lambda: self.status_var.set("处理完成!"))
            else:
                self.status_var.set("处理完成!")
        
        except Exception as e:
            self.status_var.set(f"处理出错: {str(e)}")
            self.log(f"错误详情: {str(e)}")

    def update_mode(self):
        """根据选择的模式更新内部变量"""
        mode = self.process_mode.get()
        
        # 重置所有模式
        self.invert.set(False)
        self.only_invert.set(False)
        self.only_concat.set(False)
        
        # 根据选择设置对应的模式
        if mode == "invert_concat":
            self.invert.set(True)
        elif mode == "invert_only":
            self.only_invert.set(True)
        elif mode == "concat":
            self.only_concat.set(True)
        else:
            # 如果没有选择任何模式，默认为仅拼接
            self.process_mode.set("concat")
            self.only_concat.set(True)
        
        # 强制更新UI
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    
    # 尝试设置按钮样式
    try:
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
    except:
        pass  # 如果样式设置失败，使用默认样式
    
    app = ImageProcessorApp(root)
    root.mainloop()