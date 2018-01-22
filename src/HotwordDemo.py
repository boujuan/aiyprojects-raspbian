import aiy.audio
import aiy.cloudspeech
import aiy.voicehat
import miaHotword
import random

def main():
    aiy.voicehat.get_status_ui().status('starting')
    recognizer = aiy.cloudspeech.get_recognizer()
    recognizer.expect_phrase('where should I go on holiday')
    recognizer.expect_phrase('yes')
    recognizer.expect_phrase('no')
    recognizer.expect_phrase('goodbye')
    
    led = aiy.voicehat.get_led()
    recorder=aiy.audio.get_recorder()
    recorder.start()
    voice_only=False
    seconds=0
         
    while True:
        miaHot=miaHotword.miaHotword()
        aiy.voicehat.get_status_ui().status('ready')
        miaHot.waitForHotword(recorder,voice_only,seconds)
        if not(voice_only) or seconds > 0:
            aiy.audio.say(random.choice(['yes honey?','ok?','yep?','yes?','what?','what darling?']))
            holidayList= ["sun","snow","surf"]
            context=[]
            seconds=0
        reply=""
        aiy.voicehat.get_status_ui().status('listening')
        text = recognizer.recognize()
        aiy.voicehat.get_status_ui().status('thinking')
        if not text:
            aiy.voicehat.get_status_ui().status('error')
            reply='Sorry, I did not hear you.'
        else:
            print('You said "', text, '"')
            if 'holiday' in text or 'holidays' in text:
                feature=random.choice(holidayList)
                reply = "do you like {0}".format(feature)
                context.extend([feature])
                voice_only=True
            elif 'goodbye' in text:
                reply = "ok, bye for now"
                break
            elif text=='yes':
                if "sun" in context:
                  reply="how about cuba?"
                elif "snow" in context:
                  reply="what about greenland?"
                elif "surf" in context:
                  reply="california?"
                voice_only = False 
            elif text=='no':
                print (len(holidayList))
                feature=context.pop()
                holidayList.remove(feature)
                if len(holidayList)==0:
                    reply="you are a dead loss"
                    voice_only = True
                    seconds=3 # give a chance to say goodbye
                else:
                    feature=random.choice(holidayList)
                    context.extend([feature])
                    reply = "do you like {0}".format(feature)
                    voice_only = True
        if len(reply) > 0:
          aiy.audio.say(reply)
    if len(reply) > 0:
        aiy.audio.say(reply)
    aiy.voicehat.get_status_ui().status('stopping')
    aiy.voicehat.get_status_ui().status('power-off')              
if __name__ == '__main__':
    main()
    # To run the demo say the hotword and then ask about a holiday
