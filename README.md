# PicStitcher Plus

图片智能拼接工具 - 自动识别歌曲编号和页码，批量拼接图片

## 功能特点

- 🎵 **智能识别**：自动从文件名中提取歌曲编号、歌名和页码
- 📁 **批量处理**：一次性处理整个文件夹的图片
- 🎨 **自定义背景**：支持自定义背景颜色
- 💾 **配置保存**：自动保存上次使用的设置
- 🖼️ **多格式支持**：支持 JPG、PNG、BMP 等常见图片格式

## 支持的文件名格式

程序支持以下三种文件名格式：

1. `第001首 歌名1.jpg` - 标准格式
2. `001.歌名1.jpg` - 简化格式
3. `第0707愿将我的心给你1.jpg` - 紧凑格式

## 系统要求

- Windows 10/11
- 无需安装 Python 环境（使用打包版本）

## 下载安装

### 方式一：下载可执行文件（推荐）

1. 访问 [Releases](https://github.com/paramita1949/PicStitcher/releases) 页面
2. 下载最新版本的 `PicStitcher-vX.X.X.exe`
3. 双击运行即可使用

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/paramita1949/PicStitcher.git
cd PicStitcher

# 安装依赖
pip install -r requirements-minimal.txt

# 运行程序
python main.py
```

## 使用方法

1. **启动程序**：双击运行 `PicStitcher.exe`
2. **选择输入文件夹**：点击"浏览"按钮，选择包含待拼接图片的文件夹
3. **选择输出文件夹**：点击"浏览"按钮，选择拼接后图片的保存位置
4. **设置背景颜色**（可选）：点击"选择背景颜色"按钮自定义背景色
5. **开始处理**：点击"开始处理"按钮，等待处理完成
6. **查看结果**：处理完成后，在输出文件夹中查看拼接好的图片

## 配置文件

程序会自动在当前目录生成 `config.json` 配置文件，保存以下设置：

```json
{
  "input_folder": "上次使用的输入文件夹路径",
  "output_folder": "上次使用的输出文件夹路径",
  "background_color": [255, 255, 255]
}
```

## 开发说明

### 项目结构

```
PicStitcher Plus/
├── main.py                 # 主程序
├── icon.ico               # 程序图标
├── config.json            # 配置文件
├── requirements-minimal.txt  # 最小依赖
├── build_pyinstaller_fixed.bat  # 本地打包脚本
├── .github/
│   └── workflows/
│       └── build-and-release.yml  # GitHub Actions 自动打包
└── 版本管理/              # 历史版本
```

### 本地打包

使用 PyInstaller 打包：

```bash
# 方式一：使用批处理脚本
build_pyinstaller_fixed.bat

# 方式二：手动打包
pyinstaller --onefile --windowed --icon=icon.ico main.py
```

### 自动打包和发布

本项目使用 GitHub Actions 自动打包和发布：

1. **创建标签**：
   ```bash
   git tag v1.5.0
   git push origin v1.5.0
   ```

2. **自动构建**：推送标签后，GitHub Actions 会自动：
   - 安装依赖
   - 使用 PyInstaller 打包程序
   - 创建 Release
   - 上传可执行文件

3. **查看结果**：访问 [Releases](https://github.com/paramita1949/PicStitcher/releases) 页面查看发布的版本

## 更新日志

详细更新历史请查看 [updata.txt](updata.txt)

## 许可证

本项目为私有项目，仅供授权用户使用。

## 联系方式

如有问题或建议，请通过 GitHub Issues 反馈。

