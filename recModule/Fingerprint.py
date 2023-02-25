from matplotlib import mlab, pyplot as plt
from scipy.ndimage.morphology import generate_binary_structure, iterate_structure, binary_erosion
from scipy.ndimage.filters import maximum_filter
import numpy as np
import hashlib

# Finger print 配置
class FPconfig(object):

    # FFT 窗口大小
    fft_window_size = 4096
    # 窗口大小的重叠面积比率
    fft_overlap_ratio = 0.5
    # 值越高，峰值数量越少，精度越低
    minimun_peak_amplitude = 10 # 20
    peak_neighborhood_size = 20 # 25
    # 通过生成快速组合哈希来获得排序peak
    peak_sort = True
    time_constraint_condition = (9, 200) # (min,max) (9,200)
    fanout_factor = 15 # 20
    fingerprint_cutoff = 0

def getSpecgramArr(sample, fs=2, nfft=FPconfig.fft_window_size, window=mlab.window_hanning, noverlap = int(FPconfig.fft_window_size * FPconfig.fft_overlap_ratio)):
    """获得频谱图 spectrum\n

    使用FFT将时域信号转为频域信号并生成频谱图

    Parameters
    ----------
    sample : Any
        音频向量样本(默认单通道)
    fs : Any
        音频的采样频率
    nfft : int, optional
        用于FFT的每个块中使用的数据点的数量, by default FPconfig.fft_window_size
    window : (x: {__len__}) -> Optional[Any], optional
        NFFT的长度矢量/帧长 即加窗处理中的窗长, by default mlab.window_hanning
    noverlap : int, optional
        帧移 帧长重叠部分 越接近FFT长度 FFT运算次数越多 时间轴上精度越高, by default int(FPconfig.fft_window_size * FPconfig.fft_overlap_ratio)

    Returns
    -------
    NDArray
        对数空间中的频谱
    """

    spectrum, freqs, t = mlab.specgram(sample, NFFT=nfft, Fs=fs, window=window, noverlap=noverlap)
    # 转换到对数空间防止数值过大
    spectrum[spectrum == 0] = 1
    spectrum = 10 * np.log10(spectrum)
    # 将负数替换成0，寻找最大值不影响结果
    spectrum[spectrum == -np.inf] = 0
    print(np.max(spectrum))
    return spectrum

def getConstellationMap(spectrum, plot=False, min_peak_amp=FPconfig.minimun_peak_amplitude):
    """生成星状图Constellation Map\n

    对finger print的过滤并提取特征值,通过比较获取同一时间上突出点频率最大的peak

    Parameters
    ----------
    spectrum : NDArray
        对数空间中的spectrum(来自getSpectramArr)
    plot : bool, optional
        是否显示绘图, by default False
    min_peak_amp : int, optional
        作为峰值peak的最小值, by default FPconfig.minimun_peak_amplitutude

    Returns
    -------
    List[Tuple[Any, Any]]
        2D peaks array [(x1,y1),(x2,y2),.......]
    """
    # 获得原始算子
    struct  = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, FPconfig.peak_neighborhood_size)
    # 使用滤波器找到局部最大值
    local_max = maximum_filter(spectrum, footprint=neighborhood) == spectrum
    background  = (spectrum == 0)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)
    detected_peaks = local_max ^ eroded_background
    # 提取峰值
    amps = spectrum[detected_peaks]
    i, j = np.where(detected_peaks) # 返回满足detected_peaks的索引
    # 滤波器 峰值
    amps = amps.flatten() # 降维
    peaks = zip(j, i, amps)
    peaks_filtered = [x for x in peaks if x[2] > min_peak_amp]
    # 获取频率和时间索引
    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]
    #print(max(time_idx))

    if plot:
        # 分散的峰值
        fig, ax = plt.subplots()
        ax.imshow(spectrum)
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.savefig("test.jpg")
        #plt.xlim(200, 800)
        plt.xlim(200, 500)
        plt.ylim(0, 400)
        plt.show()

    return list(zip(time_idx, frequency_idx))

def getFBHashGenerator(peaks, fanout_factor=FPconfig.fanout_factor):
    """通过计算peak之间的时间差,对相应peak和时间差做hash化处理

    Parameters
    ----------
    peaks : list[tuple]
        二维峰值阵列(来自getConstellationMap)
    fanout_factor : int, optional
        fanout常数 值越大生成指纹越多, by default FPconfig.fanout_factor

    Yields
    ------
    a FBHash list
        Hash list structure:
        sha1_hash   time_offset
        [(e05b341a9b77a51fd26, 32), ... ]
    """
    # peak 以时间顺序排序
    if FPconfig.peak_sort:
        peaks.sort(key=lambda x: x[0])

    # 选择生成指纹的峰值
    for i in range(len(peaks) - fanout_factor):
        for j in range(fanout_factor):
            t1 = peaks[i][0]  # 定位点的时间
            t2 = peaks[i + j][0]  # target zone内点的时间
            freq1 = peaks[i][1]  # 定位点的频率
            freq2 = peaks[i + j][1]  # target zone内点的频率
            t_delta = t2 - t1

            # 把两点的频率和时间差组合生成一个哈希，再加上时间位置生成指纹
            if t_delta >= FPconfig.time_constraint_condition[0] and t_delta <= FPconfig.time_constraint_condition[1]:
                h = hashlib.sha256(
                    ("%s_%s_%s" % (str(freq1), str(freq2), str(t_delta))).encode())
                yield (h.hexdigest()[0:64 - FPconfig.fingerprint_cutoff], t1)
