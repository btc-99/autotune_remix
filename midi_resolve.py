import mido


def tempo_function(tempo_list, tick_time):
    real_time = 0
    last_tick = 0
    last_tempo = 1e6
    for point in tempo_list:
        current_tick, current_tempo = point
        if tick_time <= current_tick:
            real_time += (tick_time - last_tick) * last_tempo
            break
        real_time += (current_tick - last_tick) * last_tempo
        last_tick, last_tempo = point
    return real_time


def resolve(midiname):
    # 导入midi文件
    mid = mido.MidiFile(midiname)
    # 获取归一化系数
    unit = mid.ticks_per_beat
    # 获取所有音轨
    all_tracks = mid.tracks
    tempo_list = []

    Inf = float('Inf')

    flag = False
    for track in all_tracks:
        # tick 时间从头计数
        tick_time = 0
        # 逐一读取音轨中的每个事件
        for message in track:
            # 通过 tick_time 累加来进行计时
            tick_time += message.time
            # 如果事件为修改速度，那么加入到设置函数的大军中
            if message.type == 'set_tempo':
                flag = True
                tempo_list.append([tick_time, message.tempo])
        if flag:
            break

    final_tempo = tempo_list[-1][1]
    tempo_list.append([Inf, final_tempo])

    all_list = []
    flag = False
    for track in all_tracks:
        # tick 时间从头计数
        tick_time = 0
        # 首先初始化 note_on_list 和 track_list
        # 准备好10个音道
        prepare_num = 10
        note_on_list = {}
        track_list = []
        # 权宜之计，总不会有那么多同时按的吧
        # 就是不用 try，不想用
        for i in range(prepare_num):
            note_on_list[i] = None
            track_list.append([])
        # 逐一读取音轨中的每个事件
        for message in track:
            # 通过 tick_time 累加来进行计时
            tick_time += message.time
            # 如果是按下的 note_on 操作
            if message.type == 'note_on':
                flag = True
                # 参考 tempo_list 算出实际时间是多少
                real_note_on_time = tempo_function(tempo_list, tick_time)/unit * 1e-6
                # 提取出按下的是哪个键
                note_on_type = message.note
                for i in range(prepare_num):
                    # 从头开始一个个检查，第一个检查到为 None 的就写入
                    if note_on_list[i] is None:
                        # 将时间和按键输入 note_on_list 中去
                        note_on_list[i] = [real_note_on_time, note_on_type]
                        # 完成写入工作之后，头也不回就跑
                        break
            # 如果是弹起的 note_off 操作
            if message.type == 'note_off':
                # 首先还是知道这个弹起操作的真实时间和按键是什么
                note_off_type = message.note
                real_note_off_time = tempo_function(tempo_list, tick_time)/unit * 1e-6
                # 在 note_on_list 进行查找
                for i in range(prepare_num):
                    if note_on_list[i] is not None:
                        # 将弹起键位与按下键位进行对比
                        current_note_on = note_on_list[i][1]
                        if note_off_type == current_note_on:
                            # 相同就把时间和按键输出到 track_list 中去
                            track_list[i].append([note_on_list[i][0], real_note_off_time, note_off_type])
                            # 添加完成后删除 note_on 列表中的元素，防止下次查找出现
                            # 因为按下的按键不可能再按下，所以删除之后就不会再有相同的按键了
                            note_on_list[i] = None
                            break
            if message.type == 'end_of_track' and flag:
                track_list = list(filter(None, track_list))
                all_list.append(track_list)
    return all_list
