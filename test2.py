from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
from formatConversion import Midi2roll

if __name__ == '__main__':
    # Load audio
    (audio, _) = load_audio('sample/cutLaCampanella.mp3', sr=sample_rate, mono=True)

    # Transcriptor
    transcriptor = PianoTranscription(device='cpu')    # 'cuda' | 'cpu'

    # Transcribe and write out to MIDI file
    transcribed_dict = transcriptor.transcribe(audio, 'cutLaCampanella.mid')

    # midi to piano roll
    Midi2roll.midiToPianoRoll('cutLaCampanella.mid')
