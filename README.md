# Video Dedup & Anti-plagiarism Tool

🚀 **A robust, localized video deep-deduplication tool built with FFmpeg and Gradio**. Designed to help content creators bypass machine-based plagiarism checks on major short video platforms (like TikTok, Kuaishou, etc.) through deep parameter adjustments and fine-grained visual filters.

[🇨🇳 中文版说明 (Chinese Version)](README_zh.md)

## ✨ Core Features

- **Tiered Parameter Presets**: One-click switching between "Light", "Medium", and "Heavy" deduplication presets.
- **Deep Visual Processing**: Supports micro-cropping, dynamic film grain, color tweaking, vignette, and minor geometric flips.
- **Temporal & Audio Obfuscation**: Features micro-speed variations, random volume fluctuations, specific audio band gain adjustments, and frame dropping/fps reduction.
- **Encoding & Metadata Obfuscation**: Completely strips original video metadata, supports dynamic randomized GOP keyframe structures and VBR bitrates, and appends randomized hex bytes to the underlying binary file for MD5 obfuscation.
- **Batch & Single File Support**: Drag-and-drop a single file for real-time visual frame preview; or select a local folder for completely silent, hands-free batch processing.
- **100% Local Execution**: Excellent privacy. No file size limits, no processing time limits, and absolutely no data uploaded to the cloud.

## 🛠 Installation Guide

### 1. Install FFmpeg
This project relies on the underlying `ffmpeg` command-line tool.
- **Mac**: `brew install ffmpeg`
- **Windows**: Use `winget install ffmpeg` or download manually and configure environment variables.
- **Linux**: `sudo apt install ffmpeg`

### 2. Install Python Dependencies
Python 3.8+ environment is recommended:
```bash
pip install -r requirements.txt
```

## 🚀 Usage
Run the following command in your terminal:
```bash
python app.py
```
The terminal will output a local URL (typically `http://127.0.0.1:7860`). Open it in your web browser to access the visual operation interface.

## 📜 License
This project is licensed under the [MIT License](LICENSE), allowing you to freely use, modify, and distribute the code.
