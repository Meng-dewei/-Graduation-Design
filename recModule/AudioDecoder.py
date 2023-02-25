from recModule import Console
from pydub import AudioSegment
from recModule.Config import recConfig
from typing import Union, Tuple, Any, List, Generator
import os, hashlib
import numpy as np


def generateFilehash(filepath: "str", blocksize = 2 ** 16) -> str:
    """计算文件的sha256值作为歌曲的唯一标识码。



    Parameters
    ----------
    filepath : str
        音频文件路径
    blocksize : int, optional
        单次读取文件的大小, by default 2**16

    Returns
    -------
    str
        返回经过sha256加密的十六进制文件标识码
    """
    m = hashlib.sha256()
    with open(filepath, "rb") as fh:
        while True:
            buf = fh.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest().upper()

def encodeAudio(filepath: "str", dir="temp"):
    """调整音频的路径和格式.\n

    使用ffmpeg编码音频.

    Parameters
    ----------
    filepath : str
        音频文件路径
    dir : str, optional
        额外的中间路径, by default "temp"

    Returns
    -------
    Union[Tuple[int, int], Tuple[Any, List[None]]]
        返回采样频率和通道数
    """
    dir = os.path.realpath(dir)
    Console.log("Encode Audio with ffmpeg......", end = "")
    if not os.path.exists(dir):
        os.makedirs(dir)
    path = os.path.join(dir, "temp" + generateFilehash(filepath)[:6:] + recConfig.extened_name)
    os.system(" ".join(["ffmpeg", "-loglevel", "quiet", "-i", "\"%s\"" % filepath, "-y", "-acodec", "mp3", "-ar", str(recConfig.audio_frame_rate), "\"%s\"" % path]))
    return read(path)

def read(filepath) -> Union[Tuple[int, int], Tuple[Any, List[None]]]:
    """通过文件路径读取音频文件以获取 frame_rate 和 channels.\n

    Call encodeAudio Function to set all audio file frame rate with a default value and same extensions.

    Parameters
    ----------
    filepath : str
        音频文件路径

    Returns
    -------
    Union[Tuple[int, int], Tuple[Any, List[None]]]
        返回采样频率和通道数
    """
    try:
        filename, exten = os.path.splitext(filepath)
        audiofile = AudioSegment.from_file(filepath)
        if audiofile.frame_rate != recConfig.audio_frame_rate or exten != recConfig.extened_name:
            return encodeAudio(filename)
        data = np.fromstring(audiofile.raw_data, dtype=np.int16)
        channels = []
        for channel in range(audiofile.channels):
            channels.append(data[channel::audiofile.channels])
    except:
        return 0, 0

    return audiofile.frame_rate, channels

def readDir(filesdir) -> Generator[Tuple[Union[bytes, str], Any, str], Any, None]:
    """Encrypt the corresponding files in the directory.\n

    文件目录中具有受支持扩展名的文件进行sha256加密。

    Parameters
    ----------
    filesdir : str
        文件目录

    Returns
    -------
    Generator[Tuple[Union[bytes, str], Any, str], Any, None]
        生成器 (filepath, filename, filehash)
    """
    for root, dirs, files in os.walk(filesdir):
        # 遍历文件
        for file in files:
            filename, ext = os.path.splitext(os.path.split(file)[1])
            if ext in recConfig.support_audio:
                try:
                    fh = generateFilehash(os.path.join(root, file))
                except:
                    continue
                yield(os.path.join(root, file), filename, fh)
        if not recConfig.search_subdir:
            break


if __name__ == '__main__':
    s = generateFilehash("C:/Users/mdw/Desktop/demo/liangyu.mp3")
    print(f"data:{s}") # data:C50E13E556E19735000A601DA973484A

    p = read("C:/Users/mdw/Desktop/demo/liangyu.mp3")
    print(p) # (44100, [array([0, 0, 0, ..., 0, 0, 0], dtype=int16), array([0, 0, 0, ..., 0, 0, 0], dtype=int16)])

    a = readDir("C:/Users/mdw/Desktop/demo")
    a.__next__()