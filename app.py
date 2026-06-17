import gradio as gr
import os
import shutil
import tempfile
import glob
from core_ffmpeg import process_video, preview_frame, extract_original_frame, compress_video
from core_scene import process_scene_shuffle

# 强制本地网络请求不走代理，解决 Gradio 502 问题
os.environ["no_proxy"] = "localhost, 127.0.0.1, ::1"

css = """
#hidden-tabs .tab-nav,
#hidden-tabs div[role="tablist"] {
    display: none !important;
}
"""

def update_presets(preset):
    # 默认 "无"
    vals = ["无"] * 26
    vals[14] = "不清除" # p_mute
    vals[24] = "保持原尺寸" # p_res
    vals[25] = "自动 (CRF 高画质)" # p_target_bitrate
    
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
        'p_pip', 'p_text', 'p_img', 'p_delogo',
        'p_res', 'p_target_bitrate'
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
        'p_pip', 'p_text', 'p_img', 'p_delogo',
        'p_res', 'p_target_bitrate'
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
        'p_pip', 'p_text', 'p_img', 'p_delogo',
        'p_res', 'p_target_bitrate'
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

def do_scene_shuffle(input_video, shuffle_mode, threshold_val, progress=gr.Progress()):
    if not input_video:
        return None, "请先上传一个视频文件。"
        
    output_path = os.path.join(tempfile.gettempdir(), f"shuffle_{uuid.uuid4().hex[:8]}.mp4")
    
    def log_cb(msg):
        progress(0, desc=msg)
        
    try:
        process_scene_shuffle(input_video, output_path, mode=shuffle_mode, threshold=threshold_val, progress_callback=log_cb)
        return output_path, "智能混剪处理完成！可以下载或在其它页面重新上传继续叠加滤镜。"
    except Exception as e:
        return None, f"处理失败：\n{str(e)}"


# -----------------
# 构建 Gradio 界面
# -----------------
import uuid

with gr.Blocks(title="视频去重过原创神器 - 完整版", theme=gr.themes.Soft(), css=css) as app:
    gr.Markdown("# 🚀 视频去重过原创神器 (完整加强版)")
    
    with gr.Row():
        # 左侧导航栏 (Sidebar)
        with gr.Column(scale=1, min_width=200):
            nav_radio = gr.Radio(
                choices=["单文件去重处理", "批量文件夹去重", "智能场景切片混剪", "极致视频压缩"], 
                value="单文件去重处理", 
                label="", 
                interactive=True
            )
            
        # 右侧主内容区 (Main Content)
        with gr.Column(scale=4):
            with gr.Tabs(elem_id="hidden-tabs") as main_tabs:
                # 页面 1：单文件去重处理
                with gr.TabItem("单文件去重处理", id="单文件去重处理"):
                    gr.Markdown("### 🎦 单文件去重工作台")
                    with gr.Row():
                        with gr.Column():
                            video_input = gr.Video(label="选择本地视频文件")
                            with gr.Row():
                                process_btn = gr.Button("🚀 导出完整视频", variant="primary")
                                preview_btn = gr.Button("🖼️ 单帧效果预览")
                        with gr.Column():
                            video_output = gr.Video(label="处理完成的视频")
                            status_text = gr.Textbox(label="运行状态")
                    with gr.Row():
                        img_orig = gr.Image(label="原视频(第1秒)")
                        img_preview = gr.Image(label="处理后(第1秒)")
    
                # 页面 2：批量文件夹去重
                with gr.TabItem("批量文件夹去重", id="批量文件夹去重"):
                    gr.Markdown("### 📂 批量处理工作台")
                    with gr.Row():
                        folder_input = gr.Textbox(label="粘贴包含视频的本地文件夹路径", placeholder="/Users/username/Desktop/my_videos", scale=4)
                        browse_btn = gr.Button("📂 浏览选择本地文件夹", scale=1)
                    batch_process_btn = gr.Button("🚀 开始批量处理文件夹", variant="primary")
                    batch_log = gr.Textbox(label="批量处理日志", lines=15)
    
                # 页面 3：智能场景切片混剪
                with gr.TabItem("智能场景切片混剪", id="智能场景切片混剪"):
                    gr.Markdown("### ✂️ 智能场景混剪工作台 (纯乱序/不附加去重滤镜)")
                    with gr.Row():
                        with gr.Column():
                            scene_video_input = gr.Video(label="上传要切片的视频")
                            scene_mode = gr.Dropdown(["不启用", "仅轻度乱序", "随机抽取掉15%片段", "完全打乱激烈混剪"], value="完全打乱激烈混剪", label="混剪模式")
                            scene_threshold = gr.Slider(0.1, 0.5, value=0.3, step=0.05, label="场景变化敏感度", info="越低切得越碎（产生更多片段），越高切得越整")
                            scene_process_btn = gr.Button("✂️ 开始智能视觉重组", variant="primary")
                        with gr.Column():
                            scene_video_output = gr.Video(label="混剪完成的视频")
                            scene_status = gr.Textbox(label="运行状态")

                # 页面 4：极致视频压缩
                with gr.TabItem("极致视频压缩", id="极致视频压缩"):
                    gr.Markdown("### 🗜️ 极致压缩工作台 (纯本地H.264 VBR)")
                    with gr.Row():
                        with gr.Column():
                            compress_video_input = gr.Video(label="上传要压缩的视频")
                            compress_crf = gr.Slider(18, 40, value=28, step=1, label="CRF压缩率", info="数值越大，压缩越厉害但画质损失越多（推荐28-32）")
                            compress_preset = gr.Dropdown(["fast", "medium", "slow", "slower", "veryslow"], value="slower", label="编码预设", info="越慢压得越小，极度压榨体积请选 slower 或 veryslow")
                            compress_process_btn = gr.Button("🗜️ 开始极致压缩", variant="primary")
                        with gr.Column():
                            compress_video_output = gr.Video(label="压缩完成的视频")
                            compress_status = gr.Textbox(label="运行状态")

            # 去重滤镜面板 (移到底部，只在单文件和批量处理时显示)
            with gr.Column(visible=True) as filters_col:
                preset_radio = gr.Radio(
                    choices=["轻度去重", "中度去重", "重度过原创", "自定义"], 
                    value="中度去重", 
                    label="快速处理模式", 
                    info="选择配置后，下方的各项细分参数会自动跟随调整"
                )
                
                with gr.Accordion("1. 画面处理 (Video Filters)", open=False):
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
                    
                with gr.Accordion("3. 编码与尺寸 (Encoding, Res & Meta)", open=False):
                    p_res = gr.Dropdown(["保持原尺寸", "1080p (1920x1080/1080x1920)", "720p (1280x720/720x1280)", "4K (3840x2160/2160x3840)"], value="保持原尺寸", label="输出分辨率")
                    p_target_bitrate = gr.Dropdown(["自动 (CRF 高画质)", "2Mbps (极限压缩)", "5Mbps (日常分享)", "8Mbps (高清标准)", "15Mbps (超清)"], value="自动 (CRF 高画质)", label="目标码率")
                    p_gop = gr.Dropdown(["无", "动态I帧间距"], value="无", label="随机帧结构GOP")
                    p_bitrate = gr.Dropdown(["无", "动态VBR控制"], value="无", label="码率浮动")
                    p_meta = gr.Dropdown(["无", "彻底清除"], value="无", label="清除原始Meta")
                    p_md5 = gr.Dropdown(["无", "追加随机字节"], value="无", label="追加干扰数据")
                    
                with gr.Accordion("4. 水印与画中画 (Watermark & PiP)", open=False):
                    p_pip = gr.Dropdown(["无"], value="无", label="添加画中画", interactive=False)
                    p_text = gr.Dropdown(["无"], value="无", label="添加文字水印", interactive=False)
                    p_img = gr.Dropdown(["无"], value="无", label="添加图片水印", interactive=False)
                    p_delogo = gr.Dropdown(["无"], value="无", label="模糊原水印", interactive=False)

                input_components = [
                    p_crop, p_noise, p_flip, p_sharp, p_vignette, p_color, p_feather, p_contrast,
                    p_fps, p_speed, p_reverse, p_vol, p_pitch, p_eq, p_mute, p_bgm,
                    p_gop, p_bitrate, p_meta, p_md5,
                    p_pip, p_text, p_img, p_delogo,
                    p_res, p_target_bitrate
                ]
                preset_radio.change(fn=update_presets, inputs=preset_radio, outputs=input_components)


    # 绑定导航切换逻辑
    def update_nav(nav_val):
        if nav_val == "单文件去重处理":
            return gr.update(visible=True), gr.update(selected="单文件去重处理")
        elif nav_val == "批量文件夹去重":
            return gr.update(visible=True), gr.update(selected="批量文件夹去重")
        elif nav_val == "智能场景切片混剪":
            return gr.update(visible=False), gr.update(selected="智能场景切片混剪")
        elif nav_val == "极致视频压缩":
            return gr.update(visible=False), gr.update(selected="极致视频压缩")

    nav_radio.change(
        fn=update_nav, 
        inputs=nav_radio, 
        outputs=[filters_col, main_tabs]
    )

    # 绑定处理事件
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
    
    browse_btn.click(
        fn=select_local_folder,
        inputs=[folder_input],
        outputs=[folder_input]
    )
    
    batch_process_btn.click(
        fn=do_batch_process,
        inputs=[folder_input] + input_components,
        outputs=[batch_log]
    )
    
    scene_process_btn.click(
        fn=do_scene_shuffle,
        inputs=[scene_video_input, scene_mode, scene_threshold],
        outputs=[scene_video_output, scene_status]
    )

    # 绑定压缩事件
    def handle_compress(input_vid, crf, preset):
        if not input_vid:
            return None, "请先上传视频"
        out_path = os.path.join(tempfile.gettempdir(), f"compressed_{uuid.uuid4().hex[:8]}.mp4")
        success, msg = compress_video(input_vid, out_path, crf, preset)
        if success:
            orig_size = os.path.getsize(input_vid) / (1024 * 1024)
            new_size = os.path.getsize(out_path) / (1024 * 1024)
            return out_path, f"{msg}\n原始大小: {orig_size:.2f} MB\n压缩后: {new_size:.2f} MB\n体积减小: {100 - (new_size/orig_size*100):.1f}%"
        else:
            return None, f"压缩失败: {msg}"

    compress_process_btn.click(
        fn=handle_compress,
        inputs=[compress_video_input, compress_crf, compress_preset],
        outputs=[compress_video_output, compress_status]
    )
    
    # Initialize UI state
    app.load(fn=lambda: update_presets("中度去重"), inputs=None, outputs=input_components)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0")
