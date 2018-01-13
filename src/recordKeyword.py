import time
import wave
import sys
import base64
import requests
import aiy._drivers._player
import aiy._drivers._recorder
import aiy._drivers._tts

AUDIO_SAMPLE_SIZE = 2  # bytes per sample
AUDIO_SAMPLE_RATE_HZ = 16000

# Global variables. They are lazily initialized.
_voicehat_recorder = None
_voicehat_player = None
_status_ui = None


class _WaveDump(object):
    """A processor that saves recorded audio to a wave file."""

    def __init__(self, filepath, duration):
        self._wave = wave.open(filepath, 'wb')
        self._wave.setnchannels(1)
        self._wave.setsampwidth(2)
        self._wave.setframerate(16000)
        self._bytes = 0
        self._bytes_limit = int(duration * 16000) * 1 * 2

    def add_data(self, data):
        max_bytes = self._bytes_limit - self._bytes
        data = data[:max_bytes]
        self._bytes += len(data)
        if data:
            self._wave.writeframes(data)

    def is_done(self):
        return self._bytes >= self._bytes_limit

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._wave.close()
        
def get_player():
    """Returns a driver to control the VoiceHat speaker.

    The aiy modules automatically use this player. So usually you do not need to
    use this. Instead, use 'aiy.audio.play_wave' if you would like to play some
    audio.
    """
    global _voicehat_player
    if _voicehat_player is None:
        _voicehat_player = aiy._drivers._player.Player()
    return _voicehat_player
          
def play_wave(wave_file):
    """Plays the given wave file.

    The wave file has to be mono and small enough to be loaded in memory.
    """
    player = get_player()
    player.play_wav(wave_file)
    

def get_recorder():
    """Returns a driver to control the VoiceHat microphones.

    The aiy modules automatically use this recorder. So usually you do not need to
    use this.
    """
    global _voicehat_recorder
    if _voicehat_recorder is None:
        _voicehat_recorder = aiy._drivers._recorder.Recorder()
    return _voicehat_recorder

def record_to_wave(recorder,filepath, duration):
    """Records an audio for the given duration to a wave file."""
    dumper = _WaveDump(filepath, duration)
    with dumper:
        recorder.add_processor(dumper)
        while not dumper.is_done():
            time.sleep(0.1)
    time.sleep(1)

def get_wave(fname):
    with open(fname,'rb') as infile:
        byte_content = infile.read()
    
    base64_bytes = base64.b64encode(byte_content)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string   
    
                    
if __name__ == '__main__':

    ############# MODIFY THE FOLLOWING #############
    token = "44b84e72d34173825d3d588be92d761322f8cd5a"
    hotword_name = "smartmirror"
    language = "en"
    age_group = "20_29"
    gender = "M"
    microphone = "voicehat"
    durationSecs=2
    ############### END OF MODIFY ##################
    
    endpoint = "https://snowboy.kitt.ai/api/v1/train/"
    filepath = "./resources/"+hotword_name
    ok="N"
    recorder=get_recorder()
    recorder.start()
    while ok.upper()=="N":
        print("Ready to record hotword")
        time.sleep(1)
        print("Recording")
        record_to_wave(recorder,filepath+"1.wav",durationSecs)
        print("Ready to record hotword a second time")
        print("Recording")
        record_to_wave(recorder,filepath+"2.wav",durationSecs)
        print("Ready to record hotword for last time")
        print("Recording")
        record_to_wave(recorder,filepath+"3.wav",durationSecs)
        print("Playing hotword version 1")
        play_wave(filepath+"1.wav")
        print("Playing hotword version 2")
        play_wave(filepath+"2.wav")
        print("Playing hotword version 3")
        play_wave(filepath+"3.wav")
        ok = input('Are these recordings ok (Y/N): ')
        
    print ("sending to hotword creator")
    data = {
        "name": hotword_name,
        "language": language,
        "age_group": age_group,
        "gender": gender,
        "microphone": microphone,
        "token": token,
        "voice_samples": [
            {"wave": get_wave(filepath+"1.wav")},
            {"wave": get_wave(filepath+"2.wav")},
            {"wave": get_wave(filepath+"3.wav")}
        ]
    }
    response = requests.post(endpoint, json=data)
    if response.ok:
        with open(filepath +".pmdl", "wb") as outfile:
            outfile.write(response.content)
        print ("Saved model to %s.pmdl" % filepath)
    else:
        print ("Request failed.")
        print (response.text)