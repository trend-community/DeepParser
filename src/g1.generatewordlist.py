#!/usr/bin/python
#==============================================================
# command line
#==============================================================
import argparse
import pickle
import viterbi1

parser = argparse.ArgumentParser()
parser.add_argument("output", help="output folder")
parser.add_argument("dict", help="pickle dict")
args = parser.parse_args()
print(args)

viterbi1.LoadDictFromPickle(args.dict)
#==============================================================
# unigram tokenization
#==============================================================
import codecs, re

for i in range(1, 15):
    fout = codecs.open(args.output+"/gran_" + str(i) + "_list.txt", 'wb', encoding='utf-8')

    shorlist = [k for k in viterbi1.querydict if len(k) == i]
    for word in sorted(shorlist):
        word = word.replace(":", "\:")
        fout.write(word + "\n")

    fout.close()

