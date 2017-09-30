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

# Requirements:
# Google Cloud Storage with uploaded wav files (16000 Hz sample rate, PCM signed 16-bit little-ending, mono-channel, no longer than 80 mins)
# Google Speech API enabled in your Google Console project

# Environment values for Auth:
# GCLOUD_PROJECT: <id>
# GOOGLE_APPLICATION_CREDENTIALS: <absolute path to your google console account cred JSON file>

import time
import re
import os

import httplib2
import utils

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')
ORIGIN_TRANSCRIPT = os.path.join(os.getcwd(), 'leo', 'o.txt')  # path to the origin transcript file


# Application default credentials provided by env variable
# GOOGLE_APPLICATION_CREDENTIALS
def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)
    return discovery.build('speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)


def main():
    urls = ['gs://<folder>/%s_part.wav' % i for i in xrange(1, 5)]  # put your GS files in this list
    
    speech_service = get_speech_service()
    operations = []
    transcripts = []

    global_timer = time.time()

    for url in urls:
        service_request = speech_service.speech().asyncrecognize(
            body={
                'config': {
                    'encoding': 'LINEAR16',
                    'sampleRate': 16000,
                    'languageCode': 'en-US'  # a BCP-47 language tag
                },
                'audio': {
                    'uri': url
                }
            })
        response = service_request.execute()
        operations.append(response.get('name'))

    confidences = []

    for o in operations:
        response = None
        attempt = 0
        start = time.time()

        while True:
            operation = speech_service.operations().get(name=str(o))
            response = operation.execute()

            if 'error' in response:
                print response
                continue

            if 'response' in response and response.get('metadata').get('progressPercent') == 100:
                print 'Operation %s took %s sec' % (o, time.time() - start)
                break
            else:
                attempt += 1
                print 'Operation %s attempt %s' % (o, attempt)
            time.sleep(10)  # debounce timeout for 10 secs

        if 'results' not in response.get('response'):
            continue

        # collect all results
        _results = []
        for each in response.get('response').get('results'):
            # pick alternative with the highest confidence
            alt_highest_confidence = max(each['alternatives'], key=lambda x: x['confidence'])
            _results.append(alt_highest_confidence['transcript'])
            confidences.append(alt_highest_confidence['confidence'])

        transcript_one_line = ' '.join(_results)
        transcripts.append(transcript_one_line)

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
    f = open(os.path.join(os.getcwd(), 'leo', 'recognized_g.txt'), 'w+')
    f.write(recognized_transcript)
    f.close()


if __name__ == '__main__':
    main()