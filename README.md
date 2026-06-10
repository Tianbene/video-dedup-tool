# 视频去重过原创神器 (Video Dedup & Anti-plagiarism Tool)

🚀 **一个基于 FFmpeg 与 Gradio 构建的本地化视频深度去重工具**。旨在帮助内容创作者通过底层参数调整与画面精细滤镜，绕过短视频平台机器查重审核。

[🇬🇧 English Version](README_EN.md)

## ✨ 核心特性

- **分级参数预设**：一键切换“轻度”、“中度”、“重度”去重方案。
- **画面深度处理**：支持微量裁剪、动态噪点、色彩微调、暗角、微小翻转等操作。
- **时序与音频扰乱**：支持极微变速、音量随机波动、音频频段增益、抽帧处理等。
- **编码与元数据混淆**：清除原始视频 Meta 信息，支持动态随机 GOP 关键帧结构与 VBR 码率控制，随机追加底层二进制 MD5 混淆字节。
- **批量与单文件支持**：支持单文件拖拽实时单帧效果预览；支持选择本地文件夹进行无感静默批量处理。
- **100% 本地运行**：隐私极佳，不限制视频大小和处理时长。

## 🛠 安装指南

### 1. 安装 FFmpeg
本项目依赖于底层的 `ffmpeg` 命令行工具。
- **Mac**: `brew install ffmpeg`
- **Windows**: 使用 `winget install ffmpeg` 或手动下载配置环境变量
- **Linux**: `sudo apt install ffmpeg`

### 2. 安装 Python 依赖
建议使用 Python 3.8+ 环境：
```bash
pip install -r requirements.txt
```

## 🚀 启动与使用
在终端运行以下命令：
```bash
python app.py
```
终端将会输出一个本地链接（默认通常为 `http://127.0.0.1:7860`），在浏览器中打开即可进入可视化操作界面。

## 📜 许可证 (License)
本项目采用 [MIT License](LICENSE) 开源，允许自由使用、修改与分发。
