#!/usr/bin/python
#==============================================================
# command line
#==============================================================
import argparse
import pickle
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file")
parser.add_argument("output", help="output file")
args = parser.parse_args()
print(args)

#==============================================================
# unigram tokenization
#==============================================================
import codecs, re

fin = codecs.open(args.input, 'rb', encoding='utf-8')
fout = codecs.open(args.output, 'wb', encoding='utf-8')

LexiconSet = set()
print("Start reading " + args.input)
for line in fin:
    line = line.strip()
    words = [x.strip() for x in re.split("[< >]", line) if x]

    LexiconSet.update(words)
print("Start writing to " + args.output)
for word in sorted(LexiconSet, key=lambda x: (len(x), x)):
    if len(word) > 1:
        word = word.replace(":", "\:")
        fout.write(word + "\n")

fout.close()
fin.close()
