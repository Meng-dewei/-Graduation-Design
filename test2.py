from piano_transcription_inference import PianoTranscription, sample_rate, load_audio

# Load audio
(audio, _) = load_audio('sample/cutLaCampanella.mp3', sr=sample_rate, mono=True)

# Transcriptor
transcriptor = PianoTranscription(device='cpu')    # 'cuda' | 'cpu'

# Transcribe and write out to MIDI file
transcribed_dict = transcriptor.transcribe(audio, 'cutLaCampanella.mid')

if __name__ == '__main__':
    pass
