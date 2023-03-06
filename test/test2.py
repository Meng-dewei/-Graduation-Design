from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
from formatConversion import Midi2roll

if __name__ == '__main__':
    # Load audio
    (audio, _) = load_audio(path='../sample/Henry Smith 1978 - Give Thanks (cut).mp3', sr=sample_rate, mono=True)

    # Transcriptor
    transcriptor = PianoTranscription(device='cpu')    # 'cuda' | 'cpu'

    # Transcribe and write out to MIDI file
    transcribed_dict = transcriptor.transcribe(audio, '../Henry Smith 1978 - Give Thanks (cut).mid')

    # midi to piano roll
    Midi2roll.midiToPianoRoll('../Henry Smith 1978 - Give Thanks (cut).mid')
