#!/usr/bin/env python
import datetime
import os
import glob
import argparse
import time

from pocketsphinx.pocketsphinx import Decoder

DEFAULT_MODEL_PATH = '/usr/local/share/pocketsphinx/model/en-us'
DEFAULT_CHUNK_SIZE = 307200  # ~ 10 sec of .wav, PCM signed 16-bit little endian, 16 KHz sample rate, mono channel
buzz_words = ['<s>', '</s>', '[SPEECH]', '[NOISE]', '<sil>']

hypothesis = []
bag_of_words = []
decoder = None


def main(args):
    start = time.time()
    # read audio files from directory
    if args.indir:
        audio_filepaths = [glob.glob(e) for e in ['*.wav', '*.raw']]
        if not audio_filepaths:
            print 'No audio file (.wav, .raw) in given directory was found.'
            return
        for f in audio_filepaths:
            recognize_audio(f, args)
    # read given single audio file
    elif args.infile:
        recognize_audio(args.infile, args)

    print '%s recognition took %s sec' % ('Continuous' if not args.full_utt else 'Batch', time.time() - start)

    # write hypothesis into the separate file, joining with empty space
    f = open(os.path.join(os.getcwd(), 'leo', 'recognized_sphinx_%s.txt' % args.chunk_size), 'w+')
    f.write(' '.join(hypothesis))
    f.close()

    # write segments into separate file
    # TODO: further work with segments
    f = open(os.path.join(os.getcwd(), 'leo', 'recognized_sphinx_%s_segments.txt' % args.chunk_size), 'w+')
    [f.write('%s\n' % s) for s in bag_of_words]
    f.close()


def recognize_audio(audio_file, args):
    try:
        decoder.start_utt()
        stream = open(audio_file, 'rb')
        in_speech_bf = False
        while True:
            buf = stream.read(args.chunk_size)
            if buf:
                decoder.process_raw(buf, False, False)  # full_utt = False
                if decoder.get_in_speech() != in_speech_bf:
                    in_speech_bf = decoder.get_in_speech()
                    if decoder.hyp() is not None:
                        hypothesis.append(decoder.hyp().hypstr)
                        [bag_of_words.append(seg.word) for seg in decoder.seg() if seg.word not in buzz_words]
                        decoder.end_utt()
                        decoder.start_utt()
            else:
                break
    except Exception, ex:
        print 'Error occurred with %s \n%s' % (audio_file, ex)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-infile', help='Audio .wav/.raw file')
    parser.add_argument('-indir', help='Directory containing audio files', nargs='?')
    parser.add_argument('-chunk_size', help='Size of audio file in bytes to read', default=DEFAULT_CHUNK_SIZE, type=int)
    parser.add_argument('-hmm', help='Acoustic model directory', default=os.path.join(DEFAULT_MODEL_PATH, 'en-us'))
    parser.add_argument('-lm', help='Language model input file', default=os.path.join(DEFAULT_MODEL_PATH, 'en-us.lm.bin'))
    parser.add_argument('-dict', help='Pronunciation dictionary input file', default=os.path.join(DEFAULT_MODEL_PATH, 'cmudict-en-us.dict'))

    args = parser.parse_args()

    # Create a decoder with certain model
    config = Decoder.default_config()
    config.set_string('-hmm', args.hmm)
    config.set_string('-lm', args.lm)
    config.set_string('-dict', args.dict)
    config.set_string('-logfn', os.path.join(os.getcwd(), 'results-%s.log' % datetime.datetime.now()))

    decoder = Decoder(config)

    main(args)