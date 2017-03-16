#!/usr/bin/env python
# Edited version of https://cloud.google.com/speech/docs/rest-tutorial
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Google Cloud Speech API sample application using the REST API for batch
processing."""




# novitoll:

# Requirements:
# Google Cloud Storage with uploaded flac/wav files
#  (16000 Hz sample rate, PCM signed 16-bit little-ending OR FLAC, mono-channel, no longer than 1 min)
# Google Speech API enabled in your Google Console project

# Environment values for Auth:
# GCLOUD_PROJECT: <id>
# GOOGLE_APPLICATION_CREDENTIALS: <absolute path to your google console account cred JSON file>

import time
import re
import os
import base64
import glob
import argparse

import httplib2
import utils

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')
ORIGIN_TRANSCRIPT = os.path.join(os.getcwd(), 'leo', 'o.txt')  # your origin transcript file path


# Application default credentials provided by env variable
# GOOGLE_APPLICATION_CREDENTIALS
def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)
    return discovery.build('speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)


def main(args):
    speech_service = get_speech_service()
    transcripts = []
    confidences = []
    global_timer = time.time()

    audio_files = glob.glob(r'%s/*part_[0-9]*.%s' % (args.path, args.format))
    audio_files.sort(key=sort_fileparts)

    for audio_file in audio_files:
        current = os.path.basename(audio_file)
        with open(audio_file, 'rb') as f:
            content = base64.b64encode(f.read())
            service_request = speech_service.speech().syncrecognize(
                body={
                    'config': {
                        'encoding': 'FLAC' if args.format == 'flac' else 'LINEAR16',
                        'sampleRate': 16000,
                        'languageCode': 'en-US'  # a BCP-47 language tag
                    },
                    'audio': {
                        'content': content.decode('UTF-8')
                    }
                })

            response = service_request.execute()

            if 'error' in response or 'results' not in response or not response:
                print '%s: NOT recognized, full response is %s' % (current, response)
                continue

            print '%s: %s' % (current, 'recognized')

            # collect all results
            _results = []
            for each in response['results']:
                # pick alternative with the highest confidence
                alt_highest_confidence = max(each['alternatives'], key=lambda x: x['confidence'])
                _results.append(alt_highest_confidence['transcript'])
                confidences.append(alt_highest_confidence['confidence'])

            transcript_one_line = ' '.join(_results)
            transcripts.append(transcript_one_line)
            f.close()

    print
    print 'Recognition process took %s sec' % (time.time() - global_timer)
    print

    recognized_transcript = ' '.join(transcripts)

    print '%s frames in recognition' % len(transcripts)
    print
    print 'Average confidence of recognized transcripts is %s' % (sum(confidences) / len(confidences))

    with open(ORIGIN_TRANSCRIPT, 'rb') as f:
        origin_transcript = f.read()
        origin_transcript = origin_transcript.decode('UTF-8')

        print '%s words recognized' % len(re.findall(r'\w+', recognized_transcript))
        print 'Recognized transcript: \n%s' % recognized_transcript
        print

        print '%s words in origin' % len(re.findall(r'\w+', origin_transcript))
        print 'Origin transcript: \n%s' % origin_transcript
        print

        print 'Diff %s' % utils.find_diff(recognized_transcript, origin_transcript)
        # WER = (I + D + S) / N
        print 'WER %s%%' % utils.wer(recognized_transcript.split(), origin_transcript.split())

    # write recognized transcript into file
    f = open(os.path.join(os.getcwd(), 'leo', 'recognized_g_sync.txt'), 'w+')
    f.write(recognized_transcript)
    f.close()


def sort_fileparts(filepath):
    filename = os.path.basename(filepath).partition('.')[0]
    return int(filename.split('part_')[1])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', help='Absolute path to the directory with the audio files')
    parser.add_argument('-format', help='Audio format', default='wav')
    args = parser.parse_args()
    main(args)