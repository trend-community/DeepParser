# ==============================================================
# a simple server stress test program
# ==============================================================
# !/usr/bin/python2 -u
# -*- coding: utf8 -*-

import os, sys

# set path to correctly import modules
dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
sys.path.append(dir_path + '/../../')

import logging
import codecs
import re
import jsonpickle
import utils, Graphviz
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
import collections

def init():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)

    ProcessSentence.LoadCommon()

def LexicalAnalyze(Sentence, Type = "simple", Debug = False):
    # Sentence is like: AB C
    nodes, winningrules = ProcessSentence.LexicalAnalyze(''.join(Sentence.split(' ')))
    if nodes:
        try:
            return utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
        except Exception as e:
            logging.error(e)
            return ""
    else:
        logging.error("nodes is blank")
        return ""


def clear_format(text):
    return re.sub('[<>]', '', text)


def offline_run(filename):
    fin = codecs.open(filename, 'rb', encoding='utf-8')
    lNum = 0
    err = 0
    res_dict = collections.OrderedDict()
    for line in fin:
        line = line.strip()
        lNum += 1
        if lNum % 10 == 0:
            print('Processing line %d ...' % lNum)
    
        try:
            #get(line, res_dict)
            res = clear_format(LexicalAnalyze(line)).strip()

            if line != res:
                err += 1
                res_dict[line] = res
        except:
            logging.error (  'Error:', line)
            #sys.stdout.flush()
    return float(err)/lNum, res_dict


if __name__ == "__main__":
    try:
        input_file = sys.argv[1]
    except:
        print('usage: python offline_fenci_test.py input_file')
        exit()

    init()

    err_rate, res_dict = offline_run(input_file) # return err_rate and error cases
    
    #fo = open(output_file, 'w')
    #for k in res_dict.keys():
    #    fo.write('label:%s\nres:%s\n\n' % (k, res_dict[k])) 
    #fo.close()
    for k in res_dict.keys():
        print('label:%s\nres:%s\n' % (k, res_dict[k]))
    
    print('Error rate: %.3f' % (err_rate))
    print('Done')
