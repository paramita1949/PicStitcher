import os
import re
import json  # 新增
from pathlib import Path
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser  # 添加colorchooser
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
        self.root.title("图片批量拼接与反色处理工具V1.3 (增强版)")
        self.root.geometry("600x550")  # 稍微增加高度以容纳新按钮
        self.root.resizable(True, True)
        
        # 获取配置文件路径，兼容打包后的EXE
        self.config_path = self.get_config_path()
        self.input_folder = ""
        self.output_folder = ""
        
        # 黄字效果RGB默认值（默认颜色）
        self.yellow_text_r = 174
        self.yellow_text_g = 159
        self.yellow_text_b = 112
        
        # 用于实际处理逻辑的变量
        self.invert = tk.BooleanVar(value=False)
        self.only_invert = tk.BooleanVar(value=True)  # 默认选择仅反色
        self.only_concat = tk.BooleanVar(value=False)
        
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
        self.process_mode = tk.StringVar(value="invert_only")  # 默认为仅反色

        # 创建单选按钮
        ttk.Radiobutton(option_frame, text="反色+拼接", variable=self.process_mode, value="invert_concat",
                        command=self.update_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(option_frame, text="仅反色", variable=self.process_mode, value="invert_only",
                        command=self.update_mode).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(option_frame, text="仅拼接", variable=self.process_mode, value="concat",
                        command=self.update_mode).pack(side=tk.LEFT, padx=10)

        # RGB颜色设置区域 - 增强版
        rgb_frame = ttk.LabelFrame(main_frame, text="颜色设置")
        rgb_frame.pack(fill=tk.X, pady=10)

        # 颜色输入区域 - 重新布局
        color_input_frame = ttk.Frame(rgb_frame)
        color_input_frame.pack(fill=tk.X, padx=10, pady=5)

        # 16进制输入
        ttk.Label(color_input_frame, text="16进制:").pack(side=tk.LEFT)
        self.hex_var = tk.StringVar(value=f"#{self.yellow_text_r:02x}{self.yellow_text_g:02x}{self.yellow_text_b:02x}")
        self.hex_entry = ttk.Entry(color_input_frame, textvariable=self.hex_var, width=10)
        self.hex_entry.pack(side=tk.LEFT, padx=5)
        self.hex_var.trace_add('write', self.on_hex_change)

        # RGB输入 - 移动到16进制右边
        ttk.Label(color_input_frame, text="RGB:").pack(side=tk.LEFT, padx=(15,5))

        # R值输入
        ttk.Label(color_input_frame, text="R:").pack(side=tk.LEFT)
        self.r_var = tk.StringVar(value=str(self.yellow_text_r))
        self.r_entry = ttk.Entry(color_input_frame, textvariable=self.r_var, width=4)
        self.r_entry.pack(side=tk.LEFT, padx=2)
        self.r_var.trace_add('write', self.on_rgb_change)

        # G值输入
        ttk.Label(color_input_frame, text="G:").pack(side=tk.LEFT, padx=(5,0))
        self.g_var = tk.StringVar(value=str(self.yellow_text_g))
        self.g_entry = ttk.Entry(color_input_frame, textvariable=self.g_var, width=4)
        self.g_entry.pack(side=tk.LEFT, padx=2)
        self.g_var.trace_add('write', self.on_rgb_change)

        # B值输入
        ttk.Label(color_input_frame, text="B:").pack(side=tk.LEFT, padx=(5,0))
        self.b_var = tk.StringVar(value=str(self.yellow_text_b))
        self.b_entry = ttk.Entry(color_input_frame, textvariable=self.b_var, width=4)
        self.b_entry.pack(side=tk.LEFT, padx=2)
        self.b_var.trace_add('write', self.on_rgb_change)

        # 融合的颜色预览+系统色盘按钮 - 移动到RGB右边
        self.color_preview = tk.Button(color_input_frame, text="颜色选择",
                                      command=self.open_system_color_picker,
                                      bg=f"#{self.yellow_text_r:02x}{self.yellow_text_g:02x}{self.yellow_text_b:02x}",
                                      fg="white" if (self.yellow_text_r + self.yellow_text_g + self.yellow_text_b) < 384 else "black",
                                      relief=tk.RAISED, borderwidth=2,
                                      width=12, height=2,
                                      font=('Arial', 9))
        self.color_preview.pack(side=tk.LEFT, padx=10)

        # 预设颜色按钮区域
        preset_frame = ttk.Frame(rgb_frame)
        preset_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(preset_frame, text="预设颜色:").pack(side=tk.LEFT)

        # 预设颜色列表 (名称, R, G, B)
        preset_colors = [
            ("默认", 174, 159, 112),
            ("纯黄", 255, 255, 0),
            ("秋麒麟", 218, 165, 32),
            ("晒黑", 210, 180, 140),
            ("结实的树", 222, 184, 135),
            ("马鞍棕色", 139, 69, 19),
            ("沙棕色", 244, 164, 96)
        ]

        for name, r, g, b in preset_colors:
            btn = tk.Button(preset_frame, text=name,
                           bg=f"#{r:02x}{g:02x}{b:02x}",
                           fg="white" if (r + g + b) < 384 else "black",
                           command=lambda r=r, g=g, b=b: self.set_preset_color(r, g, b),
                           relief=tk.RAISED, borderwidth=1, padx=5, pady=2)
            btn.pack(side=tk.LEFT, padx=2)

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

    def open_system_color_picker(self):
        """打开系统颜色选择器 - 新增功能"""
        # 获取当前颜色作为初始颜色
        current_color = f"#{self.yellow_text_r:02x}{self.yellow_text_g:02x}{self.yellow_text_b:02x}"

        # 打开系统颜色选择器
        color = colorchooser.askcolor(
            color=current_color,
            title="选择反色文字颜色",
            parent=self.root
        )

        if color[0]:  # 如果用户选择了颜色
            r, g, b = [int(c) for c in color[0]]

            # 更新内部变量
            self.yellow_text_r = r
            self.yellow_text_g = g
            self.yellow_text_b = b

            # 更新所有相关的UI组件
            self.update_color_ui(r, g, b)

            # 保存配置
            self.save_config()

            print(f"系统色盘选择颜色: RGB({r}, {g}, {b})")

    def update_color_ui(self, r, g, b):
        """更新所有颜色相关的UI组件"""
        # 暂时禁用事件监听，避免循环触发
        self.disable_color_events()

        # 更新RGB输入框
        self.r_var.set(str(r))
        self.g_var.set(str(g))
        self.b_var.set(str(b))

        # 更新16进制输入框
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.hex_var.set(hex_color.upper())

        # 更新颜色预览
        self.update_color_preview(r, g, b)

        # 重新启用事件监听
        self.enable_color_events()

    def disable_color_events(self):
        """禁用颜色变化事件监听"""
        try:
            # 移除RGB输入框的监听
            for var in [self.r_var, self.g_var, self.b_var]:
                if var.trace_info():
                    var.trace_remove('write', var.trace_info()[0][1])

            # 移除16进制输入框的监听
            if self.hex_var.trace_info():
                self.hex_var.trace_remove('write', self.hex_var.trace_info()[0][1])
        except:
            pass

    def enable_color_events(self):
        """重新启用颜色变化事件监听"""
        # 重新绑定RGB输入框事件
        self.r_var.trace_add('write', self.on_rgb_change)
        self.g_var.trace_add('write', self.on_rgb_change)
        self.b_var.trace_add('write', self.on_rgb_change)

        # 重新绑定16进制输入框事件
        self.hex_var.trace_add('write', self.on_hex_change)

    def load_config(self):
        """加载上次保存的输入输出文件夹路径和黄字效果RGB配置"""

        if self.config_path.exists():
            try:
                with self.config_path.open('r', encoding='utf-8') as f:
                    cfg = json.load(f)

                self.input_folder = cfg.get('input_folder', '')
                self.output_folder = cfg.get('output_folder', '')

                # 加载黄字效果RGB配置，如果不存在则使用默认值
                self.yellow_text_r = cfg.get('yellow_text_r', 174)
                self.yellow_text_g = cfg.get('yellow_text_g', 159)
                self.yellow_text_b = cfg.get('yellow_text_b', 112)

                # 自动填充到输入框
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, self.input_folder)
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, self.output_folder)

                # 更新RGB输入框（如果已创建）
                if hasattr(self, 'r_var'):
                    self.r_var.set(str(self.yellow_text_r))
                    self.g_var.set(str(self.yellow_text_g))
                    self.b_var.set(str(self.yellow_text_b))

                # 更新16进制输入框（如果已创建）
                if hasattr(self, 'hex_var'):
                    hex_color = f"#{self.yellow_text_r:02x}{self.yellow_text_g:02x}{self.yellow_text_b:02x}"
                    self.hex_var.set(hex_color.upper())

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
                'yellow_text_r': 174,
                'yellow_text_g': 159,
                'yellow_text_b': 112,
                '_comment': '配置说明：yellow_text_r/g/b 为黄字效果的RGB颜色值(0-255)，默认为默认颜色'
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

    def on_hex_change(self, *args):
        """当16进制值改变时更新RGB值和颜色预览"""
        try:
            hex_value = self.hex_var.get().strip()

            # 移除#号（如果有的话）
            if hex_value.startswith('#'):
                hex_value = hex_value[1:]

            # 确保是6位16进制数
            if len(hex_value) == 6 and all(c in '0123456789ABCDEFabcdef' for c in hex_value):
                # 转换为RGB
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)

                # 更新内部变量
                self.yellow_text_r = r
                self.yellow_text_g = g
                self.yellow_text_b = b

                # 暂时禁用RGB输入框的监听，避免循环触发
                self.r_var.trace_remove('write', self.r_var.trace_info()[0][1] if self.r_var.trace_info() else None)
                self.g_var.trace_remove('write', self.g_var.trace_info()[0][1] if self.g_var.trace_info() else None)
                self.b_var.trace_remove('write', self.b_var.trace_info()[0][1] if self.b_var.trace_info() else None)

                # 更新RGB输入框
                self.r_var.set(str(r))
                self.g_var.set(str(g))
                self.b_var.set(str(b))

                # 重新启用RGB输入框的监听
                self.r_var.trace_add('write', self.on_rgb_change)
                self.g_var.trace_add('write', self.on_rgb_change)
                self.b_var.trace_add('write', self.on_rgb_change)

                # 更新颜色预览
                self.update_color_preview(r, g, b)

                # 保存配置
                self.save_config()

        except (ValueError, IndexError):
            # 如果输入不是有效的16进制值，忽略
            pass

    def on_rgb_change(self, *args):
        """当RGB值改变时更新16进制值和颜色预览"""
        try:
            # 获取RGB值，确保在0-255范围内
            r = max(0, min(255, int(self.r_var.get() or 0)))
            g = max(0, min(255, int(self.g_var.get() or 0)))
            b = max(0, min(255, int(self.b_var.get() or 0)))

            # 更新内部变量
            self.yellow_text_r = r
            self.yellow_text_g = g
            self.yellow_text_b = b

            # 暂时禁用16进制输入框的监听，避免循环触发
            if hasattr(self, 'hex_var') and self.hex_var.trace_info():
                self.hex_var.trace_remove('write', self.hex_var.trace_info()[0][1])

            # 更新16进制输入框
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            if hasattr(self, 'hex_var'):
                self.hex_var.set(hex_color.upper())

            # 重新启用16进制输入框的监听
            if hasattr(self, 'hex_var'):
                self.hex_var.trace_add('write', self.on_hex_change)

            # 更新颜色预览
            self.update_color_preview(r, g, b)

            # 保存配置
            self.save_config()

        except ValueError:
            # 如果输入不是有效数字，忽略
            pass

    def update_color_preview(self, r, g, b):
        """更新颜色预览按钮"""
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_preview.config(bg=hex_color)

        # 根据颜色亮度选择文字颜色
        brightness = (r + g + b) / 3
        text_color = "white" if brightness < 128 else "black"
        self.color_preview.config(fg=text_color)

    def set_preset_color(self, r, g, b):
        """设置预设颜色"""
        # 更新RGB输入框
        self.r_var.set(str(r))
        self.g_var.set(str(g))
        self.b_var.set(str(b))

        # 更新16进制输入框
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.hex_var.set(hex_color.upper())

        # on_rgb_change会自动被触发

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
            # 如果没有选择任何模式，默认为仅反色
            self.process_mode.set("invert_only")
            self.only_invert.set(True)

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
