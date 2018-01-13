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
import subprocess
import sys

import aiy.assistant.auth_helpers
import aiy.audio
import aiy.voicehat
from google.assistant.library import Assistant
from google.assistant.library.event import EventType

import vlc

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


def power_off_pi():
    aiy.audio.say('Good bye!')
    subprocess.call('sudo shutdown now', shell=True)


def reboot_pi():
    aiy.audio.say('See you in a bit!')
    subprocess.call('sudo reboot', shell=True)


def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))


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
    player.play()


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
            power_off_pi()
        elif text == 'reboot':
            assistant.stop_conversation()
            reboot_pi()
        elif text == 'ip address':
            assistant.stop_conversation()
            say_ip()
        elif 'radio' in text:
            assistant.stop_conversation()
            radio(text)

    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')

    elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED:
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def _on_button_pressed():
    radio_off()


def main():
    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        aiy.voicehat.get_button().on_press(_on_button_pressed)
        for event in assistant.start():
            process_event(assistant, event)


if __name__ == '__main__':
    main()