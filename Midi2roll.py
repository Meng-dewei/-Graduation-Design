import numpy as np
import pretty_midi
import matplotlib.pyplot as plt

def midiToPianoRoll(name):
    midi_data = pretty_midi.PrettyMIDI(name)
    print(midi_data.instruments)
    a = midi_data.instruments[0].get_piano_roll()
    # reshape 图片为3维，并将通道级联成3，即rgb
    m = np.reshape(a,(a.shape[0],a.shape[1],1))
    img = np.concatenate((m,m,m),axis=2)

    # 图像显示与保存
    plt.figure("Image",figsize=(12,8))

    plt.imshow(img)
    plt.axis('on') # 关掉坐标轴为 off
    plt.title('image') # 图像题目
    plt.savefig('show.png')# 图像保存
    plt.show()

if __name__ == '__main__':
    midiToPianoRoll('cutLaCampanella.mid')