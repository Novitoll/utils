#!/usr/bin/env python
# Valid for MS CS Bing SR API v3.0
# Doc: https://www.microsoft.com/cognitive-services/en-us/speech-api/documentation/API-Reference-REST/BingVoiceRecognition
# Example: python microsoft_cogn_serv_speech_api.py -key <subscription_key> -path <audio_file_dir> -o_transc <original transcription file>
import re
import time
import os
import json
import glob
import requests
import argparse
import uuid
import utils
import difflib

# external WER calculation tool (https://martin-thoma.com/word-error-rate-calculation/)

URL = 'https://speech.platform.bing.com/recognize?'


def main(args):
    transcripts = []
    confidences = []
    nospeech_count = 0
    url = build_url()
    start_time = time.time()

    token = get_token(args.key)
    audio_files = glob.glob(r'%s/*part_[0-9]*.wav' % args.path)
    audio_files.sort(key=sort_fileparts)

    if not audio_files:
        print 'No *part_*.wav audio files were found'
        return

    headers = {
        'Content-Type': 'audio/wav; samplerate=16000',
        'Authorization': 'Bearer %s' % token
    }

    for audio_file_path in audio_files:
        with open(audio_file_path, 'rb') as f:
            current = os.path.basename(audio_file_path)
            r = requests.post(url, headers=headers, data=f.read())

            if not r.content:
                print '%s: No response content' % current
                f.close()
                continue

            r = json.loads(r.content)
            _header = r['header']

            if _header['status'] == 'error':
                nospeech_count += 1
                print '%s: No speech recognition result, header: %s' % (current, _header)
                f.close()
                continue

            _results = r['results']
            assert len(_results) == 1, 'Should return 1 element with the best confidence'
            print '%s: recognized' % current

            transcripts.append(_results[0]['lexical'])
            confidences.append(float(_results[0]['confidence']))

    print
    print 'Recognition process took %s sec' % (time.time() - start_time)
    print 'Amount of unrecognized speech %s' % nospeech_count
    print 'Mean confidence: %s' % (sum(confidences) / len(confidences))
    print

    recognized_transcript = ' '.join(transcripts)

    with open(args.o_transc, 'rb') as f:
        origin_transcript = f.read()
        origin_transcript = origin_transcript.decode('UTF-8')
        print '%s words recognized' % len(re.findall(r'\w+', recognized_transcript))
        print 'Recognized transcript: \n%s' % recognized_transcript
        print

        print '%s words in origin' % len(re.findall(r'\w+', origin_transcript))
        print 'Origin transcript: \n%s' % origin_transcript
        print

        print 'Diff %s' % find_diff(recognized_transcript, origin_transcript)
        # WER = (I + D + S) / N
        print 'WER %s%%' % utils.wer(recognized_transcript.split(), origin_transcript.split())

    # write recognized transcript into file
    f = open(os.path.join(os.getcwd(), 'leo', 'recognized_m.txt'), 'w+')
    f.write(recognized_transcript)
    f.close()


def build_url():
    params = ['scenarios=ulm', 'appid=f84e364c-ec34-4773-a783-73707bd9a585', 'locale=en-US', 'device.os=wp7', 'version=3.0', 'format=json']
    params.append('requestid=%s' % uuid.uuid4())
    params.append('instanceid=%s' % uuid.uuid4())
    params.append('maxnbest=%s' % 1)  # results array should contain 1 the element
    return URL + '&'.join(params)


def sort_fileparts(filepath):
    filename = os.path.basename(filepath).partition('.')[0]
    return int(filename.split('part_')[1])


def get_token(key):
    token_url = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
    r = requests.post(token_url, headers={'Ocp-Apim-Subscription-Key': key})
    return r.content


def find_diff(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-key', help='Microsoft Bing API subscription key')
    parser.add_argument(
        '-path', help='Absolute path to the directory with the audio files')
    parser.add_argument(
        '-o_transc', help='Absolute path to the original transcription file')
    args = parser.parse_args()
    main(args)