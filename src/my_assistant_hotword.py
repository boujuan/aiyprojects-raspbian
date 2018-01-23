#!/usr/bin/env python3
# Based in AIY Google Assistant
# Code for the snowboy hotword detector from https://bitbucket.org/dani_thomas/aiyhotworddetector
import logging
import miaHotword
import re
import subprocess
from os import popen as ospopen
import aiy.assistant.grpc
import aiy.audio
import aiy.voicehat
import RPi.GPIO as GPIO
import vlc
import youtube_dl

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s")

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
    ip_address = subprocess.check_output(
        "hostname -I | cut -d' ' -f1", shell=True)
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
        '1':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p',
        'one':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p',
        '2':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p',
        '3':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio3_mf_p',
        '4':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4fm_mf_p',
        '5':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5live_mf_p',
        '5 sports':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5extra_mf_p',
        '6':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p',
        '1xtra':
        'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/uk/sbr_high/ak/bbc_radio_1xtra.m3u8',
        '4 extra':
        'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/uk/sbr_high/ak/bbc_radio_four_extra.m3u8',
        'nottingham':
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnotts_mf_p',
        'planet rock':
        'http://icy-e-bz-08-boh.sharp-stream.com/planetrock.mp3',
        'heart 80s':
        'http://media-the.musicradio.com/Heart80sMP3',
        'uk news':
        'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eieuk',
        'world news':
        'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-einws',
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
    aiy.audio.say('Playing radio ' + station_name + ' now')
    player.play()


def pi_temperature():
    tempCPU = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3
    _GPU_ = ospopen('vcgencmd measure_temp').readline()
    tempGPU = _GPU_.replace("temp=", "").replace("'C\n", "")
    say = 'CPU is at ' + str(tempCPU) + ' degrees and GPU is at ' + str(
        tempGPU) + ' degrees'
    print(say)
    aiy.audio.say(say)


def process_event(assistant, miaHot, recorder):
    # change to true for not needing to repeat hotword inmedially for seconds=x
    voice_only = False
    seconds = 5
    status_ui = aiy.voicehat.get_status_ui()
    status_ui.set_trigger_sound_wave('resources/dong.wav')
    status_ui.status('starting')
    miaHot.waitForHotword(recorder, voice_only, seconds)
    status_ui.status('listening')
    print('Listening...')
    text, audio = assistant.recognize()
    status_ui.status('thinking')

    if text is not None:
        print('You said "', text, '"')

        if text == 'power off':
            status_ui.status('stopping')
            power_off_pi()
            audio = None
        if text == 'shut down':
            assistant.stop_conversation()
            aiy.audio.say('Commencing Self-Destruct Sequence in 5. 4. 3. 2. 1')
            status_ui.status('stopping')
            power_off_pi()
            audio = None
        elif text == 'reboot':
            status_ui.status('stopping')
            reboot_pi()
            audio = None
        elif text == 'goodbye':
        	status_ui.status('stopping')
        	print('Bye!')
        	power_off_pi()
        elif text == 'IP address':
            say_ip()
        elif text == 'volume up':
            volume_up()
            audio = None
        elif text == 'volume down':
            volume_down()
            audio = None
        elif text == 'maximum volume':
            volume_max()
            audio = None
        elif text == 'mute':
            volume_min()
            audio = None
        elif text.startswith('volume '):
            volume_set(int(text[7:])) # Fix the exception when text[7:] is not an integer 1-100
            audio = None
        elif text == 'pause':
            vlc_player.set_pause(True)
            audio = None
        elif text == 'resume':
            vlc_player.set_pause(False)
            audio = None
        elif text.startswith('play '):
            play_music(text[5:])
            audio = None
        elif text == 'stop music':
            vlc_player.stop()
            radio_off()
            audio = None
        elif text == 'stop':
            vlc_player.stop()
            radio_off()
        elif 'radio' in text:
            radio(text)
            audio = None
        elif text == 'what\'s your temperature':
            pi_temperature()
            audio = None

    if audio is not None:
        aiy.audio.play_audio(audio)


def _on_button_pressed():
    vlc_player.pause()
    radio_off()


def main():
    radio = False
    assistant = aiy.assistant.grpc.get_assistant()
    miaHot = miaHotword.miaHotword()
    with aiy.audio.get_recorder() as recorder:
        aiy.voicehat.get_button().on_press(_on_button_pressed)
        while True:
            process_event(assistant, miaHot, recorder)


if __name__ == '__main__':
    main()
