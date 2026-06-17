import ffmpeg
import os
import random
import subprocess
import re

def get_duration(video_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    return float(subprocess.check_output(cmd).decode().strip())

def check_has_audio(video_path):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    return len(subprocess.check_output(cmd).decode().strip()) > 0

def detect_scenes(video_path, threshold=0.3):
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-filter:v', f"select='gt(scene,{threshold})',showinfo",
        '-f', 'null',
        '-'
    ]
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    timestamps = [0.0]
    for line in process.stderr:
        if 'Parsed_showinfo' in line and 'pts_time:' in line:
            match = re.search(r'pts_time:([\d\.]+)', line)
            if match:
                val = float(match.group(1))
                # 限制最短场景间隔为 0.5 秒，避免切得过于稀碎
                if val > timestamps[-1] + 0.5: 
                    timestamps.append(val)
    process.wait()
    
    duration = get_duration(video_path)
    if duration - timestamps[-1] > 0.5:
        timestamps.append(duration)
    else:
        timestamps[-1] = duration
        
    return timestamps

def process_scene_shuffle(video_path, output_path, mode="完全打乱激烈混剪", threshold=0.3, progress_callback=None):
    if mode == "不启用":
        import shutil
        shutil.copy2(video_path, output_path)
        return

    if progress_callback: progress_callback("正在利用智能视觉算法扫描场景切换点，这需要一点时间...")
    timestamps = detect_scenes(video_path, threshold)
    
    segments = []
    for i in range(len(timestamps)-1):
        segments.append({
            'start': timestamps[i],
            'end': timestamps[i+1],
            'duration': timestamps[i+1] - timestamps[i]
        })
        
    if len(segments) <= 1:
        if progress_callback: progress_callback("未检测到明显的镜头切换，直接导出。")
        import shutil
        shutil.copy2(video_path, output_path)
        return
        
    # 应用混剪策略
    if mode == "仅轻度乱序":
        # 随机交换相邻片段
        for i in range(0, len(segments)-1, 2):
            if random.random() > 0.4:
                segments[i], segments[i+1] = segments[i+1], segments[i]
    elif mode == "随机抽取掉15%片段":
        num_to_keep = max(1, int(len(segments) * 0.85))
        segments = random.sample(segments, num_to_keep)
        segments.sort(key=lambda x: x['start']) # 保持时间正序，仅抽帧
    elif mode == "完全打乱激烈混剪":
        random.shuffle(segments)
        
    if progress_callback: progress_callback(f"共识别出 {len(timestamps)-1} 个镜头，根据策略将提取 {len(segments)} 个片段进行精确缝合重渲染...")
    
    has_audio = check_has_audio(video_path)
    
    filter_complex = ""
    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        filter_complex += f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
        if has_audio:
            filter_complex += f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];"
            
    for i in range(len(segments)):
        filter_complex += f"[v{i}]"
        if has_audio:
            filter_complex += f"[a{i}]"
            
    if has_audio:
        filter_complex += f"concat=n={len(segments)}:v=1:a=1[outv][outa]"
    else:
        filter_complex += f"concat=n={len(segments)}:v=1:a=0[outv]"
        
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-filter_complex', filter_complex,
        '-map', '[outv]'
    ]
    if has_audio:
        cmd.extend(['-map', '[outa]', '-c:a', 'aac'])
        
    cmd.extend(['-c:v', 'libx264', '-crf', '18', '-preset', 'fast', output_path])
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if progress_callback: progress_callback("🎉 智能混剪全部完成！")
