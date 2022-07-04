#!/usr/bin/python -u

from viterbi1 import *
#==============================================================
"""
viterbi1
Find the best chunking of the given strSent as a string of space 
delimited sequence of words, purely by Viterbi on phrase unigram.

input:
	strSent: text containing space delimited sequence of words
		We apply no restriction to the definition of "word".
	P: phrase unigram model (in log scale)
	maxPhraseLen: maximum number of words in a phrase
	isRecursive: by default, we recursively apply the same on 
		chunks by shrinking maxPhraseLen to be "one less".

output:
	listPhrases: list of chunked phrases
"""
# bestScore[i] = best log likelihood for phrases ending at position i
# bestPhrase[i] = best phrase ending at position i
# bestPhraseLen[i] = number of words in bestPhrase[i]
#==============================================================

#==============================================================
# command line
#==============================================================
import argparse
import pickle
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file")
parser.add_argument("output", help="output file")
parser.add_argument("dict", help="pickle dict")
parser.add_argument("lexicon", help="system lexicon")
parser.add_argument("lexicon_extra", help="system lexicon")
parser.add_argument("-r", "--recursive", default=True, help="proceed recursively")
parser.add_argument("-q", "--query", default=False, help="process query format")
parser.add_argument("-d", "--debug", default=False, help="debug mode")
args = parser.parse_args()
print(args)

#==============================================================
# unigram tokenization
#==============================================================
import codecs
import math
fin = codecs.open(args.input, 'rb', encoding='utf-8')
fout = codecs.open(args.output, 'wb', encoding='utf-8')
LoadDictFromPickle(args.dict)
LoadDictFromLexicon(args.lexicon, -4)	#each lexicon word is 1/10000 of total query.
LoadDictFromLexicon(args.lexicon_extra, -40)
maxPhraseLen = 20
for line in fin:
	line = line.strip()
	if args.query:
		try:
			[sent, freqstring] = line.split("", 2)
		except:
			print("wrong format:[" + line + "]")
			fout.write("wrong format:[" + line + "]\n")
			continue
	else:
		sent = line

	fout.write(QuerySegment(sent))
	#
	# for chunk in sent.split():
	# 	phrase = normalize(chunk)
	# 	fout.write( ' '.join( viterbi1(phrase.strip(), maxPhraseLen, args.recursive) ) + ' ')
	if args.query: fout.write('\t' + freqstring)
	fout.write('\n')
fout.close()
fin.close()
