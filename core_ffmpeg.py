import ffmpeg
import os
import random
import uuid

def generate_filter_graph(video_node, audio_node, params):
    # ------------------
    # 1. 画面滤镜 (Video)
    # ------------------
    v = video_node
    
    p_crop = params.get('p_crop', '无')
    p_noise = params.get('p_noise', '无')
    p_flip = params.get('p_flip', '无')
    p_sharp = params.get('p_sharp', '无')
    p_vignette = params.get('p_vignette', '无')
    p_color = params.get('p_color', '无')
    p_contrast = params.get('p_contrast', '无')
    p_fps = params.get('p_fps', '无')
    p_speed = params.get('p_speed', '无')
    
    # 抽帧处理
    if p_fps == "降至24fps":
        v = v.filter('fps', fps=24)
    elif p_fps == "降至15fps":
        v = v.filter('fps', fps=15)

    # 随机变速
    speed = 1.0
    if p_speed == "极微波动 (0.95x~1.05x)":
        speed = random.uniform(0.95, 1.05)
        # setpts filter expects inverse of speed
        v = v.filter('setpts', f"{1.0/speed}*PTS")

    # 微量裁剪
    if p_crop == "上下左右裁1%":
        v = v.filter('crop', 'iw*0.98', 'ih*0.98').filter('scale', 'iw', 'ih')
    elif p_crop == "上下左右裁2%":
        v = v.filter('crop', 'iw*0.96', 'ih*0.96').filter('scale', 'iw', 'ih')
    elif p_crop == "上下左右裁3%":
        v = v.filter('crop', 'iw*0.94', 'ih*0.94').filter('scale', 'iw', 'ih')

    # 输出分辨率调整
    p_res = params.get('p_res', '保持原尺寸')
    if p_res != "保持原尺寸":
        if "1080p" in p_res:
            v = v.filter('scale', "if(gt(iw,ih),1920,-2)", "if(gt(iw,ih),-2,1920)")
        elif "720p" in p_res:
            v = v.filter('scale', "if(gt(iw,ih),1280,-2)", "if(gt(iw,ih),-2,1280)")
        elif "4K" in p_res:
            v = v.filter('scale', "if(gt(iw,ih),3840,-2)", "if(gt(iw,ih),-2,3840)")

    # 微小翻转
    if p_flip == "水平翻转":
        v = v.filter('hflip')
    elif p_flip == "垂直翻转":
        v = v.filter('vflip')
    elif p_flip == "水平+垂直翻转":
        v = v.filter('hflip').filter('vflip')

    # 微量锐化
    if p_sharp == "轻度":
        v = v.filter('unsharp', luma_msize_x=3, luma_msize_y=3, luma_amount=0.3)
    elif p_sharp == "中度":
        v = v.filter('unsharp', luma_msize_x=5, luma_msize_y=5, luma_amount=0.5)
    elif p_sharp == "重度":
        v = v.filter('unsharp', luma_msize_x=5, luma_msize_y=5, luma_amount=0.8)

    # 胶片噪点
    if p_noise == "轻度":
        v = v.filter('noise', c0s=1.5, c0f='t+u')
    elif p_noise == "中度":
        v = v.filter('noise', c0s=2.5, c0f='t+u')
    elif p_noise == "重度":
        v = v.filter('noise', c0s=4.0, c0f='t+u')

    # 色彩微调
    brightness = 0
    contrast = 1.0
    saturation = 1.0
    
    if p_color == "随机微调":
        brightness += random.uniform(-0.02, 0.02)
        contrast *= random.uniform(0.98, 1.02)
        saturation *= random.uniform(0.98, 1.02)
    elif p_color == "亮度+5%":
        brightness += 0.05
    elif p_color == "对比度+5%":
        contrast *= 1.05

    if p_contrast == "+5%":
        contrast *= 1.05
    elif p_contrast == "+10%":
        contrast *= 1.1

    if brightness != 0 or contrast != 1.0 or saturation != 1.0:
        v = v.filter('eq', brightness=brightness, contrast=contrast, saturation=saturation)

    # 动态干扰 (轻微随机暗角)
    if p_vignette == "轻度":
        v = v.filter('vignette', angle='PI/6')
    elif p_vignette == "中度":
        v = v.filter('vignette', angle='PI/4')
    elif p_vignette == "重度":
        v = v.filter('vignette', angle='PI/3')

    # ------------------
    # 2. 音频滤镜 (Audio)
    # ------------------
    a = audio_node
    
    p_vol = params.get('p_vol', '无')
    p_pitch = params.get('p_pitch', '无')
    p_eq = params.get('p_eq', '无')
    p_mute = params.get('p_mute', '不清除')

    if a is not None:
        if p_mute == "完全静音":
            a = None
        else:
            if speed != 1.0:
                a = a.filter('atempo', str(speed))
                
            if p_vol == "随机波动":
                vol = random.uniform(0.9, 1.1)
                a = a.filter('volume', str(vol))
            elif p_vol == "统一+20%":
                a = a.filter('volume', '1.2')
                
            if p_pitch == "升调":
                a = a.filter('asetrate', 44100 * 1.1)
            elif p_pitch == "降调":
                a = a.filter('asetrate', 44100 * 0.9)
                
            if p_eq == "轻度降噪":
                a = a.filter('afftdn', nf=-20)
            elif p_eq == "低频增益":
                a = a.filter('equalizer', f=100, width_type='h', width=50, g=2.0)

    return v, a

def get_encode_args(params):
    args = {
        'vcodec': 'libx264',
        'acodec': 'aac',
        'crf': 18,
        'preset': 'fast',
    }
    
    p_meta = params.get('p_meta', '无')
    p_gop = params.get('p_gop', '无')
    p_bitrate = params.get('p_bitrate', '无')

    # 元数据清除
    if p_meta == "彻底清除":
        args['map_metadata'] = '-1'
        
    # 编码结构随机化
    if p_gop == "动态I帧间距":
        args['g'] = random.randint(48, 112)
        args['bf'] = random.randint(1, 3)
        args['profile:v'] = random.choice(['main', 'high'])
        
    # 目标码率控制
    p_target_bitrate = params.get('p_target_bitrate', '自动 (CRF 高画质)')
    if p_target_bitrate != "自动 (CRF 高画质)":
        if "2Mbps" in p_target_bitrate:
            args['b:v'] = '2M'
            args['maxrate'] = '2.5M'
            args['bufsize'] = '4M'
            args.pop('crf', None)
        elif "5Mbps" in p_target_bitrate:
            args['b:v'] = '5M'
            args['maxrate'] = '6M'
            args['bufsize'] = '10M'
            args.pop('crf', None)
        elif "8Mbps" in p_target_bitrate:
            args['b:v'] = '8M'
            args['maxrate'] = '10M'
            args['bufsize'] = '16M'
            args.pop('crf', None)
        elif "15Mbps" in p_target_bitrate:
            args['b:v'] = '15M'
            args['maxrate'] = '18M'
            args['bufsize'] = '30M'
            args.pop('crf', None)

    # 随机码率浮动 (仅在未指定固定码率时生效)
    if p_bitrate == "动态VBR控制" and 'maxrate' not in args:
        args['maxrate'] = '5M'
        args['bufsize'] = '10M'
        
    return args

def process_video(input_path, output_path, params):
    """
    处理整个视频
    """
    try:
        probe = ffmpeg.probe(input_path)
        has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])
        
        in_file = ffmpeg.input(input_path)
        v = in_file.video
        a = in_file.audio if has_audio else None
        
        v, a = generate_filter_graph(v, a, params)
        
        encode_args = get_encode_args(params)
        
        if a is not None:
            out = ffmpeg.output(v, a, output_path, **encode_args)
        else:
            out = ffmpeg.output(v, output_path, **encode_args)
            
        out.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        # MD5 混淆 (追加随机字节)
        if params.get('p_md5') == "追加随机字节":
            with open(output_path, 'ab') as f:
                f.write(os.urandom(random.randint(10, 50)))
                
        return True, "处理成功"
    except ffmpeg.Error as e:
        return False, e.stderr.decode('utf8', errors='ignore')
    except Exception as e:
        return False, str(e)

def preview_frame(input_path, output_path, params):
    """
    截取第一秒的单帧进行处理，用于预览
    """
    try:
        in_file = ffmpeg.input(input_path, ss=1)
        v = in_file.video
        v, _ = generate_filter_graph(v, None, params)
        
        # 只输出一帧作为图片
        out = ffmpeg.output(v, output_path, vframes=1, format='image2', vcodec='mjpeg')
        out.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "预览生成成功"
    except ffmpeg.Error as e:
        return False, e.stderr.decode('utf8', errors='ignore')
    except Exception as e:
        return False, str(e)

def extract_original_frame(input_path, output_path):
    """
    提取原图用于对比
    """
    try:
        in_file = ffmpeg.input(input_path, ss=1)
        out = ffmpeg.output(in_file.video, output_path, vframes=1, format='image2', vcodec='mjpeg')
        out.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True
    except:
        return False

def compress_video(input_path, output_path, crf=28, preset="slower"):
    """
    极致压缩视频
    """
    try:
        in_file = ffmpeg.input(input_path)
        out = ffmpeg.output(
            in_file, 
            output_path, 
            vcodec='libx264', 
            acodec='aac', 
            crf=crf, 
            preset=preset,
            map_metadata='-1' # 清除冗余元数据
        )
        out.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "极致压缩成功"
    except ffmpeg.Error as e:
        return False, e.stderr.decode('utf8', errors='ignore')
    except Exception as e:
        return False, str(e)
