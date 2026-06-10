import gradio as gr
import os
import shutil
import tempfile
import glob
from core_ffmpeg import process_video, preview_frame, extract_original_frame

# 强制本地网络请求不走代理，解决 Gradio 502 问题
os.environ["no_proxy"] = "localhost, 127.0.0.1, ::1"

def update_presets(preset):
    # 默认 "无"
    vals = ["无"] * 24
    vals[14] = "不清除" # p_mute
    
    if preset == "轻度去重":
        vals[0] = "上下左右裁1%" # p_crop
        vals[16] = "动态I帧间距" # p_gop
        vals[18] = "彻底清除" # p_meta
        vals[19] = "追加随机字节" # p_md5
    elif preset == "中度去重":
        vals[0] = "上下左右裁1%" # p_crop
        vals[1] = "轻度" # p_noise
        vals[3] = "中度" # p_sharp
        vals[5] = "随机微调" # p_color
        vals[11] = "随机波动" # p_vol
        vals[13] = "低频增益" # p_eq
        vals[16] = "动态I帧间距" # p_gop
        vals[18] = "彻底清除" # p_meta
        vals[19] = "追加随机字节" # p_md5
    elif preset == "重度过原创":
        vals[0] = "上下左右裁2%"
        vals[1] = "中度"
        vals[2] = "水平翻转"
        vals[3] = "重度"
        vals[4] = "中度"
        vals[5] = "随机微调"
        vals[7] = "+5%" # p_contrast
        vals[8] = "降至24fps"
        vals[9] = "极微波动 (0.95x~1.05x)"
        vals[11] = "随机波动"
        vals[12] = "降调"
        vals[13] = "低频增益"
        vals[16] = "动态I帧间距"
        vals[17] = "动态VBR控制"
        vals[18] = "彻底清除"
        vals[19] = "追加随机字节"
        
    return vals

def do_process(input_video, *args):
    params_keys = [
        'p_crop', 'p_noise', 'p_flip', 'p_sharp', 'p_vignette', 'p_color', 'p_feather', 'p_contrast',
        'p_fps', 'p_speed', 'p_reverse', 'p_vol', 'p_pitch', 'p_eq', 'p_mute', 'p_bgm',
        'p_gop', 'p_bitrate', 'p_meta', 'p_md5',
        'p_pip', 'p_text', 'p_img', 'p_delogo'
    ]
    params = dict(zip(params_keys, args))

    if not input_video:
        return None, "请先上传一个视频文件。"

    output_path = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4().hex[:8]}.mp4")
    success, msg = process_video(input_video, output_path, params)
    
    if success:
        return output_path, "处理完成！"
    else:
        return None, f"处理失败：\n{msg}"

def do_preview(input_video, *args):
    params_keys = [
        'p_crop', 'p_noise', 'p_flip', 'p_sharp', 'p_vignette', 'p_color', 'p_feather', 'p_contrast',
        'p_fps', 'p_speed', 'p_reverse', 'p_vol', 'p_pitch', 'p_eq', 'p_mute', 'p_bgm',
        'p_gop', 'p_bitrate', 'p_meta', 'p_md5',
        'p_pip', 'p_text', 'p_img', 'p_delogo'
    ]
    params = dict(zip(params_keys, args))
    
    if not input_video:
        return None, None, "请先上传视频。"

    temp_dir = tempfile.gettempdir()
    preview_out = os.path.join(temp_dir, f"preview_{uuid.uuid4().hex[:8]}.jpg")
    orig_out = os.path.join(temp_dir, f"orig_{uuid.uuid4().hex[:8]}.jpg")
    
    # 提取原图
    extract_original_frame(input_video, orig_out)
    
    # 生成处理后的预览图
    success, msg = preview_frame(input_video, preview_out, params)
    
    if success:
        return orig_out, preview_out, "预览生成成功！(仅展示第1秒画面的处理效果)"
    else:
        return orig_out, None, f"预览生成失败：\n{msg}"

def do_batch_process(input_folder, *args):
    params_keys = [
        'p_crop', 'p_noise', 'p_flip', 'p_sharp', 'p_vignette', 'p_color', 'p_feather', 'p_contrast',
        'p_fps', 'p_speed', 'p_reverse', 'p_vol', 'p_pitch', 'p_eq', 'p_mute', 'p_bgm',
        'p_gop', 'p_bitrate', 'p_meta', 'p_md5',
        'p_pip', 'p_text', 'p_img', 'p_delogo'
    ]
    params = dict(zip(params_keys, args))
    
    if not input_folder or not os.path.exists(input_folder):
        return "错误：文件夹路径不存在！"
        
    exts = ('*.mp4', '*.mov', '*.avi', '*.mkv')
    video_files = []
    for ext in exts:
        video_files.extend(glob.glob(os.path.join(input_folder, ext)))
        video_files.extend(glob.glob(os.path.join(input_folder, ext.upper())))
        
    if not video_files:
        return "错误：指定文件夹内没有找到支持的视频文件 (mp4, mov, avi, mkv)。"
        
    output_dir = os.path.join(input_folder, "dedup_output")
    os.makedirs(output_dir, exist_ok=True)
    
    logs = [f"找到 {len(video_files)} 个视频，开始批量处理..."]
    
    for vf in video_files:
        basename = os.path.basename(vf)
        name, ext = os.path.splitext(basename)
        out_path = os.path.join(output_dir, f"{name}_dedup{ext}")
        
        logs.append(f"正在处理: {basename}")
        yield "\n".join(logs)
        
        success, msg = process_video(vf, out_path, params)
        if success:
            logs.append(f"  -> 成功: 保存在 dedup_output 目录")
        else:
            logs.append(f"  -> 失败: {msg}")
            
        yield "\n".join(logs)
        
    logs.append("全部处理完成！")
    yield "\n".join(logs)

def select_local_folder(current_val):
    import subprocess
    try:
        # 仅限 Mac 系统使用的原生弹窗
        res = subprocess.run(["osascript", "-e", "POSIX path of (choose folder with prompt \"请选择包含视频的文件夹\")"], capture_output=True, text=True)
        path = res.stdout.strip()
        if path:
            return path
    except Exception as e:
        print("选择文件夹失败:", e)
    return current_val

# -----------------
# 构建 Gradio 界面
# -----------------
import uuid

with gr.Blocks(title="视频去重过原创神器 - 完整版") as app:
    gr.Markdown("# 🚀 视频去重过原创神器 (完整加强版)")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Tabs():
                with gr.TabItem("单文件处理"):
                    video_input = gr.Video(label="选择本地视频文件 (单文件处理)")
                with gr.TabItem("批量处理文件夹"):
                    with gr.Row():
                        folder_input = gr.Textbox(label="粘贴包含视频的本地文件夹路径", placeholder="/Users/username/Desktop/my_videos", scale=4)
                        browse_btn = gr.Button("📂 浏览选择本地文件夹", scale=1)
            
            preset_radio = gr.Radio(
                choices=["轻度去重", "中度去重", "重度过原创", "自定义"], 
                value="中度去重", 
                label="快速处理模式", 
                info="选择配置后，下方的各项细分参数会自动跟随调整"
            )
            
            with gr.Accordion("1. 画面处理 (Video Filters)", open=True):
                p_crop = gr.Dropdown(["无", "上下左右裁1%", "上下左右裁2%", "上下左右裁3%"], value="无", label="微量裁剪")
                p_noise = gr.Dropdown(["无", "轻度", "中度", "重度"], value="无", label="动态噪点")
                p_flip = gr.Dropdown(["无", "水平翻转", "垂直翻转", "水平+垂直翻转"], value="无", label="微小翻转")
                p_sharp = gr.Dropdown(["无", "轻度", "中度", "重度"], value="无", label="微量锐化")
                p_vignette = gr.Dropdown(["无", "轻度", "中度", "重度"], value="无", label="微量暗角")
                p_color = gr.Dropdown(["无", "随机微调", "亮度+5%", "对比度+5%"], value="无", label="色彩微调")
                p_feather = gr.Dropdown(["无"], value="无", label="边缘羽化", interactive=False)
                p_contrast = gr.Dropdown(["无", "+5%", "+10%"], value="无", label="调整对比度")
                
            with gr.Accordion("2. 时序与音频 (Audio & Time)", open=False):
                p_fps = gr.Dropdown(["无", "降至24fps", "降至15fps"], value="无", label="抽帧处理")
                p_speed = gr.Dropdown(["无", "极微波动 (0.95x~1.05x)"], value="无", label="随机变速")
                p_reverse = gr.Dropdown(["无"], value="无", label="画面倒放", interactive=False)
                p_vol = gr.Dropdown(["无", "随机波动", "统一+20%"], value="无", label="音量微调")
                p_pitch = gr.Dropdown(["无", "升调", "降调"], value="无", label="音频变调")
                p_eq = gr.Dropdown(["无", "轻度降噪", "低频增益"], value="无", label="降噪/均衡")
                p_mute = gr.Dropdown(["不清除", "完全静音"], value="不清除", label="清除原音")
                p_bgm = gr.Dropdown(["无"], value="无", label="添加背景音", interactive=False)
                
            with gr.Accordion("3. 编码与特征 (Encoding & Meta)", open=False):
                p_gop = gr.Dropdown(["无", "动态I帧间距"], value="无", label="随机帧结构GOP")
                p_bitrate = gr.Dropdown(["无", "动态VBR控制"], value="无", label="码率浮动")
                p_meta = gr.Dropdown(["无", "彻底清除"], value="无", label="清除原始Meta")
                p_md5 = gr.Dropdown(["无", "追加随机字节"], value="无", label="追加干扰数据")
                
            with gr.Accordion("4. 水印与画中画 (Watermark & PiP)", open=False):
                p_pip = gr.Dropdown(["无"], value="无", label="添加画中画", interactive=False)
                p_text = gr.Dropdown(["无"], value="无", label="添加文字水印", interactive=False)
                p_img = gr.Dropdown(["无"], value="无", label="添加图片水印", interactive=False)
                p_delogo = gr.Dropdown(["无"], value="无", label="模糊原水印", interactive=False)

            # Define inputs array
            input_components = [
                p_crop, p_noise, p_flip, p_sharp, p_vignette, p_color, p_feather, p_contrast,
                p_fps, p_speed, p_reverse, p_vol, p_pitch, p_eq, p_mute, p_bgm,
                p_gop, p_bitrate, p_meta, p_md5,
                p_pip, p_text, p_img, p_delogo
            ]
            
            # Preset event
            preset_radio.change(fn=update_presets, inputs=preset_radio, outputs=input_components)

        with gr.Column(scale=1):
            with gr.Tabs():
                with gr.TabItem("单文件输出结果"):
                    process_btn = gr.Button("🚀 导出完整视频", variant="primary")
                    preview_btn = gr.Button("🖼️ 单帧效果预览")
                    
                    status_text = gr.Textbox(label="运行状态")
                    video_output = gr.Video(label="处理完成的视频")
                    
                    with gr.Row():
                        img_orig = gr.Image(label="原视频(第1秒)")
                        img_preview = gr.Image(label="处理后(第1秒)")
                        
                with gr.TabItem("批量处理结果"):
                    batch_process_btn = gr.Button("🚀 开始批量处理文件夹", variant="primary")
                    batch_log = gr.Textbox(label="批量处理日志", lines=15)

    # 绑定按钮事件 (单视频)
    process_btn.click(
        fn=do_process,
        inputs=[video_input] + input_components,
        outputs=[video_output, status_text]
    )
    
    preview_btn.click(
        fn=do_preview,
        inputs=[video_input] + input_components,
        outputs=[img_orig, img_preview, status_text]
    )
    
    # 绑定浏览文件夹按钮
    browse_btn.click(
        fn=select_local_folder,
        inputs=[folder_input],
        outputs=[folder_input]
    )
    
    # 绑定按钮事件 (批量文件夹)
    batch_process_btn.click(
        fn=do_batch_process,
        inputs=[folder_input] + input_components,
        outputs=[batch_log]
    )
    
    # Initialize UI state using default preset ("中度去重")
    app.load(fn=lambda: update_presets("中度去重"), inputs=None, outputs=input_components)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0")
