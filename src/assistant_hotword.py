#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

The Google Assistant Library can be installed with:
    env/bin/pip install google-assistant-library==0.0.2

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import re
import subprocess
import sys
from os import popen as ospopen

import aiy.assistant.auth_helpers
import aiy.audio
import aiy.voicehat
from google.assistant.library import Assistant
from google.assistant.library.event import EventType

import aiy.cloudspeech
import RPi.GPIO as GPIO
import miaHotword

import vlc
import youtube_dl
import random

GPIO.setmode(GPIO.BCM)
GPIO.setup(26,GPIO.OUT)
GPIO.setup(6,GPIO.OUT)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)

ydl_opts = {
    'default_search': 'ytsearch1:',
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True
}
vlc_instance = vlc.get_default_instance()
vlc_player = vlc_instance.media_player_new()

def power_off_pi():
    aiy.audio.say('Good bye!')
    subprocess.call('sudo shutdown now', shell=True)


def reboot_pi():
    aiy.audio.say('See you in a bit!')
    subprocess.call('sudo reboot', shell=True)


def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))


def volume(change):

    """Changes the volume and says the new level."""

    GET_VOLUME = r'amixer get Master | grep "Front Left:" | sed "s/.*\[\([0-9]\+\)%\].*/\1/"'
    SET_VOLUME = 'amixer -q set Master %d%%'

    res = subprocess.check_output(GET_VOLUME, shell=True).strip()
    try:
        logging.info("volume: %s", res)
        vol = int(res) + change
        vol = max(0, min(100, vol))
        subprocess.call(SET_VOLUME % vol, shell=True)
        aiy.audio.say('Volume at %d %%.' % vol)
    except (ValueError, subprocess.CalledProcessError):
        logging.exception("Error using amixer to adjust volume.")
        
def volume_set(level):
    GET_VOLUME = r'amixer get Master | grep "Front Left:" | sed "s/.*\[\([0-9]\+\)%\].*/\1/"'
    SET_VOLUME = 'amixer -q set Master %d%%'
    
    res = subprocess.check_output(GET_VOLUME, shell=True).strip()
    try:
        logging.info("volume: %s", res)
        vol = level
        vol = max(0, min(100, vol))
        subprocess.call(SET_VOLUME % vol, shell=True)
        aiy.audio.say('Volume at %d %%.' % vol)
    except (ValueError, subprocess.CalledProcessError):
        logging.exception("Error using amixer to adjust volume.")
        
def volume_up():
    volume(10)

def volume_down():
    volume(-10)
    
def volume_max():
    volume_set(100)
    
def volume_min():
    aiy.audio.say('Muting the volume...')
    volume_set(0)
    

def play_music(name):
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(name, download=False)
    except Exception:
        aiy.audio.say('Sorry, I can\'t find that song.')
        return

    if meta:
        info = meta['entries'][0]
        vlc_player.set_media(vlc_instance.media_new(info['url']))
        aiy.audio.say('Now playing ' + re.sub(r'[^\s\w]', '', info['title']))
        vlc_player.play()
        
def radio_off():
    try:
        player.stop()
    except NameError as e:
        logging.info("Player isn't playing")


def get_station(station_name):
    stations = {
        '1': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p',
        'one': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p',
        '2': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p',
        '3': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio3_mf_p',
        '4': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4fm_mf_p',
        '5': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5live_mf_p',
        '5 sports': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5extra_mf_p',
        '6': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p',
        '1xtra': 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/uk/sbr_high/ak/bbc_radio_1xtra.m3u8',
        '4 extra': 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/uk/sbr_high/ak/bbc_radio_four_extra.m3u8',
        'nottingham': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnotts_mf_p',
        'planet rock': 'http://icy-e-bz-08-boh.sharp-stream.com/planetrock.mp3',
        'heart 80s': 'http://media-the.musicradio.com/Heart80sMP3',
        'uk news': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eieuk',
        'world news': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-einws',
                }
    return stations[station_name]

def radio(text):
    logging.info("Radio command received: %s ", text)
    station_name = (text.replace('radio', '', 1)).strip()
    if station_name == "off":
        logging.info("Switching radio off")
        radio_off()
        return
    try:
        station = get_station(station_name)
    except KeyError as e:
        logging.error("Error finding station %s", station_name)
        # Set a default station here
        station = 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p'
    logging.info("Playing radio: %s ", station)
    instance = vlc.Instance()
    global player
    player = instance.media_player_new()
    media = instance.media_new(station)
    player.set_media(media)
    aiy.audio.say('Playing radio '+station_name+' now')
    player.play()

def pi_temperature():
    tempCPU = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3
    _GPU_ = ospopen('vcgencmd measure_temp').readline();
    tempGPU = _GPU_.replace("temp=","").replace("'C\n","");
    
    say = 'CPU is at '+str(tempCPU)+' degrees and GPU is at '+str(tempGPU)+' degrees'
    print(say)
    aiy.audio.say(say)

def process_event(assistant, event):
    status_ui = aiy.voicehat.get_status_ui()
    if event.type == EventType.ON_START_FINISHED:
        status_ui.status('ready')
        if sys.stdout.isatty():
            print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        status_ui.status('listening')

    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        print('You said:', event.args['text'])
        text = event.args['text'].lower()
        if text == 'power off':
            assistant.stop_conversation()
            aiy.audio.say('Commencing Self-Destruct Sequence in 5. 4. 3. 2. 1')
            power_off_pi()        
        elif text == 'reboot':
            assistant.stop_conversation()
            reboot_pi()
        elif text == 'ip address':
            assistant.stop_conversation()
            say_ip()            
        elif text == 'volume up':
            assistant.stop_conversation()
            volume_up()
        elif text == 'volume down':
            assistant.stop_conversation()
            volume_down()        
        elif text == 'volume max':
            assistant.stop_conversation()
            volume_max()
        elif text == 'mute':
            assistant.stop_conversation()
            volume_min()
        elif text.startswith('volume '):
            assistant.stop_conversation()
            volume_set(int(text[7:]))
        elif text == 'pause':
            assistant.stop_conversation()
            vlc_player.set_pause(True)
        elif text == 'resume':
            assistant.stop_conversation()
            vlc_player.set_pause(False)
        elif text.startswith('play '):
            assistant.stop_conversation()
            play_music(text[5:])
        elif text == 'stop music':
            assistant.stop_conversation()
            vlc_player.stop()
        elif 'radio' in text:
            assistant.stop_conversation()
            radio(text)
        elif text == 'what\'s your temperature':
            assistant.stop_conversation()
            pi_temperature()
            

    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')

    elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED:
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)
        

def _on_button_pressed():
    vlc_player.pause()      
    radio_off()
    

def main():
    radio = False
    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        aiy.voicehat.get_button().on_press(_on_button_pressed)
        for event in assistant.start():
            process_event(assistant, event)


if __name__ == '__main__':
    main()

