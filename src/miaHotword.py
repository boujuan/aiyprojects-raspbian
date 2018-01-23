#!/usr/bin/env python3
import time
import queue
import miasnowboydecoder

import aiy._drivers._recorder

# Global variables. They are lazily initialized.
_voicehat_recorder = None

class miaAudio(object):
    """A processor that queues up sound from the voicehat."""

    def __init__(self):
        self._audio_queue = queue.Queue()

    def add_data(self, data):
        self._audio_queue.put(data)

    def is_done(self):
        return
        
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return
        
    def getAudio(self):
        data = self._audio_queue.get()
        return data

class miaHotword:
    def __init__(self):
      ############# MODIFY THE FOLLOWING #############
      model_file1='./resources/espejito.pmdl' # put your hotword file here. if you want to just try out use ./resources/snowboy.umdl
      model_file2='./resources/smart_mirror.pmdl'
      models=[model_file1,model_file2]
      sensitivity = 0.5
      ############### END OF MODIFY ##################
      self.detection = miasnowboydecoder.HotwordDetector(models, sensitivity=sensitivity)
      
    def waitForHotword(self,recorder, voice_only, seconds):
      if voice_only:
        print('waiting for voice')
        if seconds  > 0:
          revert2hotword=time.time() + seconds  
      else:
        print('waiting for hotword')
      sleep_time=0.03
      audio=miaAudio()
      recorder.add_processor(audio)
      while True:  
          data=audio.getAudio()
          if len(data) == 0:
            time.sleep(sleep_time)
            continue
          ans = self.detection.detector.RunDetection(data)
          if ans > 0:
            print('Hotword Detected!')
            break
          elif ans==0:
            if voice_only:
              break
          if voice_only and seconds > 0 and time.time() > revert2hotword:
            print('sleeping')
            voice_only=False
             
def get_recorder():
    """Returns a driver to control the VoiceHat microphones.

    The aiy modules automatically use this recorder. So usually you do not need to
    use this.
    """
    global _voicehat_recorder
    if _voicehat_recorder is None:
        _voicehat_recorder = aiy._drivers._recorder.Recorder()
    return _voicehat_recorder

if __name__ == '__main__':
    MiaHot=miaHotword()
    recorder=get_recorder()
    recorder.start()
    MiaHot.waitForHotword(recorder,True, 4)
    MiaHot.waitForHotword(recorder,False,0)
    MiaHot.waitForHotword(recorder,True, 0)
    
    
