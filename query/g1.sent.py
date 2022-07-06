#!/usr/bin/python -u
# -*- coding: utf8 -*-

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
import copy
minLogPw = -21	# Zetta-words
def viterbi1(strSent, P, maxPhraseLen, isRecursive=True, isDebug=False):
	if isDebug: print "=============================", "strSent=[", strSent, "]", maxPhraseLen

	## init
	sent = ['^'] + strSent.split()
	sentLen = len(sent)
	bestPhrase = copy.deepcopy(sent)
	bestPhraseLen = [1] * sentLen
	bestScore = [0.0] + [ (minLogPw * i) for i in range(1, sentLen+1) ]

	## forward path: fill up "best"
	for i in range(1, sentLen):
		for j in range(max(0, i-maxPhraseLen), i):
			phrase = ' '.join(sent[j+1:i+1])
			LogPw = P.get(phrase, 0)
			if isDebug: print j, '\t', i, '\t', i - j, '\t', bestScore[j], '\t', LogPw, '\t', bestScore[i], '\t', phrase
			if LogPw != 0 and LogPw + bestScore[j] > bestScore[i]:
				bestPhrase[i] = phrase
				bestPhraseLen[i] = i - j
				bestScore[i] = LogPw + bestScore[j]
		if isDebug: print bestPhrase[i], "bestPhrase[i]: ", i, '\t', bestScore[i], '\t', bestPhraseLen[i]

	## backward path: collect "best"
	listPhrases = []; i = sentLen - 1
	while i > 0:
		## recursion
		if bestPhraseLen[i] > 2:
			if isRecursive:
				bestPhrase[i] = ''.join( ['<'] + viterbi1(bestPhrase[i], P, bestPhraseLen[i] - 1, isRecursive, isDebug) + ['>'] )
			else:
				bestPhrase[i] = ''.join( ['\['] + basePhrase[i] + ['\]'] )
		elif bestPhraseLen[i] == 2:
			bestPhrase[i] = '<' + ''.join(sent[i-bestPhraseLen[i]+1 : i+1]) + '>'

		if isDebug: print "============ bestPhrase[i]: ", bestPhrase[i]
		listPhrases[0:0] = [ bestPhrase[i] ]
		i = i - bestPhraseLen[i]

	## return
	if isDebug: input("please....")
	return listPhrases

#==============================================================
# isNonHanzi()
#==============================================================
def isNonHanzi(s): return all( (ord(c) < 0x4e00 or ord(c) > 0x9fff) for c in s)

#==============================================================
# command line
#==============================================================
import argparse
import cPickle as pickle
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file")
parser.add_argument("output", help="output file")
parser.add_argument("dict", help="pickle dict")
parser.add_argument("-r", "--recursive", default=True, help="proceed recursively")
parser.add_argument("-q", "--query", default=False, help="process query format")
parser.add_argument("-d", "--debug", default=False, help="debug mode")
args = parser.parse_args()
print args

#==============================================================
# unigram tokenization
#==============================================================
import codecs
import math
fin = codecs.open(args.input, 'rb', encoding='utf-8')
fout = codecs.open(args.output, 'wb', encoding='utf-8')
dict = pickle.load( open(args.dict, "rb") )
logN = math.log10( dict[''] )
for word in dict: dict[word] = math.log10( dict[word] ) - logN

maxPhraseLen = 20
for line in fin:
	line = line.strip()
	if args.query:
		try:
			[sent, freqstring] = line.split("", 2)
		except:
			print "wront format:[" + line + "]"
			fout.write("wrong format:[" + line + "]\n")
			continue
	else:
		sent = line
	for chunk in sent.split():
		phrase = ''
		word_prev = ''
		for word in list(chunk):
			phrase = phrase + ( '' if isNonHanzi(word_prev) and isNonHanzi(word) else ' ' ) + word
			word_prev = word
		fout.write( ' '.join( viterbi1(phrase.strip(), dict, maxPhraseLen, args.recursive, args.debug) ) + ' ')
	if args.query: fout.write('\t' + freqstring)
	fout.write('\n')
fout.close()
fin.close()
