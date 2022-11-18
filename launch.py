import os
import librosa
import soundfile
import shutil
import midi_resolve
from tqdm import tqdm
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip

# 首先解析 midi 文件，获得解析的结果 all_list
midiname = 'midi_file.mid'
all_list = midi_resolve.resolve(midiname)
length = len(all_list)
clips = []

# 读入所有的视频文件
for i in range(length):
    one_clip = VideoFileClip(os.getcwd() + "\\input_videos" + "\\" + str(i) + ".wmv")
    clips.append(one_clip)

output_path = os.getcwd() + "\\output_videos"
try:
    os.makedirs(output_path)
except FileExistsError:
    shutil.rmtree(output_path)
    os.makedirs(output_path)

raw_audio_name = "raw_audioclip.wav"
audio_name = "audioclip.wav"
# 设置一下拉伸长度
coff = 1.5

for i in range(length):
    track = all_list[i]
    track_length = len(track)
    # track 有三层，分别是音道，音道里面的 action，然后每个 action 自带了时间和频率信息
    # 首先把初始频率拿到手
    pitch0 = track[0][0][2]

    # 这波是明修栈道暗度陈仓，音频和视频各走各的
    # 音频需要来一手合成大法
    audioclip = clips[i].audio
    # 音频拿到手之后写出去准备之后拿回来变调
    audioclip.write_audiofile(raw_audio_name)
    # 顺便直接将视频干沉默，闷声发大财
    clips[i].without_audio()

    # 这个是用来存放这一个音轨的视频文件的
    video_clip = []
    new_audio_track = []

    print('少女祈祷中...')
    # 首先大循环是每一个音道进行扫描
    for j in range(track_length):
        # 小循环是对每一个音道的 action 进行扫描
        for action in tqdm(track[j]):
            # 获取剪辑信息
            start, end, pitch = action
            # 片段长度
            duration = end - start
            # 音调变化
            dpitch = pitch - pitch0
            # 首先对视频进行裁剪
            new_videoclip = clips[i].subclip(0, coff * duration)
            # 设置起始点并导入总视频
            video_clip.append(new_videoclip.set_start(coff * start))

            # 读入音轨并且变调，不管怎么样这是每一次都要做的
            y, sr = librosa.load(raw_audio_name)
            y = librosa.effects.pitch_shift(y, sr, n_steps=dpitch)
            # 读入音轨并合并
            soundfile.write(audio_name, y, sr)
            audioclip = AudioFileClip(audio_name)
            # 对音频文件进行裁剪
            audioclip = audioclip.subclip(0, coff * duration)
            # 乱七八糟的音频全部往 new_audio_track 里面扔就完事了，也不需要排序，美滋滋
            new_audio_track.append(audioclip.set_start(coff * start))
    # 现在循环出来了，音频拼接，反正全在一起也没关系
    audio_clip_add = CompositeAudioClip(new_audio_track)
    # 视频拼接，反正全在一起也没关系
    video_clip = CompositeVideoClip(video_clip)

    # 将音频写入最终的视频
    final_video = video_clip.set_audio(audio_clip_add)

    video_name = "\\track" + str(i) + ".mp4"
    final_video.write_videofile(output_path + video_name)

    # 删除相关文件，还世界一个清净
    os.remove(raw_audio_name)
    os.remove(audio_name)
