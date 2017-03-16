#!/usr/bin/env python
import time
import os
import argparse
import nltk

from nltk.corpus import stopwords
from nltk.tag import StanfordNERTagger, StanfordPOSTagger
from nltk.tokenize import word_tokenize
from nltk.chunk import conlltags2tree
from nltk.tree import Tree

DEFAULT_LANG = 'english'
DEFAULT_NER_CLASS = 3
DEFAULT_POS_TAGGER = 'nltk'
STOPWORDS = ['huh', '.', ',', '\'m', 's', 'n\'t']  #

stanford_directory_path = '/home/sabr/nltk_data/stanford'
stanford_ner_directory_path = os.path.join(stanford_directory_path, 'stanford-ner')
stanford_pos_tagger_directory_path = os.path.join(stanford_directory_path, 'stanford-postagger')


def pre_process(args):
    stop_words = set(stopwords.words(args.lang)) | set(STOPWORDS)
    with open(args.file, 'r') as f:
        content = f.read()
        words = [w for w in word_tokenize(content, args.lang) if w not in stop_words]
        f.close()
    return words


def nltk_ner(pos):
    start = time.time()
    named_entities_tree = nltk.ne_chunk(pos)
    print 'NLTK NER took %.3f sec, NEs are:\n %s\n' % (time.time() - start, structure_ne(named_entities_tree))


def stanford_ner(words, args):
    start = time.time()
    """
    3 class: Location, Person, Organization
    4 class: Location, Person, Organization, Misc
    7 class: Location, Person, Organization, Money, Percent, Date, Time
    """
    ner_classifier_path = 'english.all.3class.distsim.crf.ser.gz'  # default 3 class

    if args.ner_class == 7:
        ner_classifier_path = 'english.muc.7class.distsim.crf.ser.gz'
    elif args.ner_class == 4:
        ner_classifier_path = 'english.conll.4class.distsim.crf.ser.gz'

    ner_classifier_full_path = os.path.join(stanford_ner_directory_path, 'classifiers', ner_classifier_path)
    ner_jar_path = os.path.join(stanford_ner_directory_path, 'stanford-ner.jar')
    s_ner_tagger = StanfordNERTagger(ner_classifier_full_path,
                                     ner_jar_path,
                                     encoding='UTF-8')
    _tagged = s_ner_tagger.tag(words)

    # NLP BIO tags processing (B-beginning NE, I-inside NE, O-outside NE)
    bio_tagged = []
    prev_tag = "O"
    for token, tag in _tagged:
        if tag == "O":  # O
            bio_tagged.append((token, tag))
            prev_tag = tag
            continue
        if tag != "O" and prev_tag == "O":  # Begin NE
            bio_tagged.append((token, "B-" + tag))
            prev_tag = tag
        elif prev_tag != "O" and prev_tag == tag:  # Inside NE
            bio_tagged.append((token, "I-" + tag))
            prev_tag = tag
        elif prev_tag != "O" and prev_tag != tag:  # Adjacent NE
            bio_tagged.append((token, "B-" + tag))
            prev_tag = tag

    # convert bio_tags to NLTK tree-like format
    tokens, ne_tags = zip(*bio_tagged)
    pos_tags = [pos for token, pos in get_pos_tags(tokens, args)]
    conlltags = [(token, pos, ne) for token, pos, ne in zip(tokens, pos_tags, ne_tags)]
    ne_tree = conlltags2tree(conlltags)

    print 'Stanford NER took %.3f sec, NEs are:\n %s\n' % (time.time() - start, structure_ne(ne_tree))


def structure_ne(ne_tree):
    ne = []
    for subtree in ne_tree:
        if type(subtree) == Tree:  # If subtree is a noun chunk, i.e. NE != "O"
            ne_label = subtree.label()
            ne_string = " ".join([token for token, pos in subtree.leaves()])
            ne.append((ne_string, ne_label))
    return ne


def get_pos_tags(words, args):
    if args.pos_tagger == 'stanford':
        # path to Stanford POS tagger's jar file
        s_pos_tagger_jar_path = os.path.join(stanford_pos_tagger_directory_path, 'stanford-postagger.jar')
        s_pos_tagger_path = os.path.join(stanford_pos_tagger_directory_path, 'models', 'english-bidirectional-distsim.tagger')
        pos_tagger = StanfordPOSTagger(s_pos_tagger_path,
                                       s_pos_tagger_jar_path,
                                       encoding='UTF-8')
        return pos_tagger.tag(words)
    elif args.pos_tagger == 'nltk':
        return nltk.pos_tag(words)  # averaged_perceptron_tagger


def main(args):
    words = pre_process(args)
    # frequency dist
    print "Most 15 common words %s\n" % nltk.FreqDist(words).most_common(15)

    # Part of speech tagging
    pos_tags = get_pos_tags(words, args)

    # NLTK NER
    nltk_ner(pos_tags)

    # Stanford NER
    stanford_ner(words, args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-file', help='Text file to work with')
    parser.add_argument('-lang', help='Language', default=DEFAULT_LANG)
    parser.add_argument('-pos_tagger', help='Part Of Speech tagger class',
                        choices=['stanford', 'nltk'], default=DEFAULT_POS_TAGGER)
    parser.add_argument('-ner_class', help='Stanford NER classifiers\' class amount',
                        choices=[3, 4, 7], type=int, default=DEFAULT_NER_CLASS)
    args = parser.parse_args()
    main(args)