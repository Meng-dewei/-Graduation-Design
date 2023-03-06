import librosa.feature
import librosa.display
import matplotlib.pyplot as plt
from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)

audio_data = 'song/liangyu.mp3'
x, sr = librosa.load(audio_data)
sr = librosa.get_samplerate(audio_data)
X = librosa.stft(x)
Xdb = librosa.amplitude_to_db(abs(X))
plt.figure(figsize=(20, 5))
librosa.display.specshow(Xdb, sr=sr, x_axis='time', y_axis='hz')
plt.colorbar()
plt.show()
# print(sr)
print(x)

chromagram = librosa.feature.chroma_stft(y=x, sr=sr, hop_length=512)
print(chromagram.shape)
plt.figure(figsize=(15, 5))
librosa.display.specshow(chromagram, x_axis='time', y_axis='chroma', hop_length=512, cmap='coolwarm')
plt.colorbar()
plt.show()
