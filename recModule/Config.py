class recConfig():
    """Config

    Attributes:
        audio_frame_rate: 音频帧速率(一路采样频率)44100Hz
        extened_name: 音频文件扩展名
        sqlalchemy_address: 数据库连接
        support_audio: 支持的音频格式
        max_connection: mysql最大连接数
        insert_number: mysql批量insert数据数量
        max_process_num: 最多音频处理数量
        enable_console_msg: 启用控制台
        search_subdir: 使用addAudioFromDir时搜索子目录
    """
    audio_frame_rate = 44100
    extened_name = ".mp3"
    sqlalchemy_address = "mysql+mysqlconnector://root:mdw153759@localhost:3306/recsong"
    support_audio = [".mp3",".m4a"]
    max_connection = 128
    insert_number = 20000
    max_process_num = 8
    enable_console_msg = True
    search_subdir = False

    def __init__(self):
        pass
