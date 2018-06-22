#!/usr/bin/python -u

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
querydict = {}
minLogPw = -21	# Zetta-words
def viterbi1(strSent,  maxPhraseLen=20, isRecursive=True):

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
			LogPw = querydict.get(phrase, 0)
			if LogPw != 0 and LogPw + bestScore[j] > bestScore[i]:
				bestPhrase[i] = phrase
				bestPhraseLen[i] = i - j
				bestScore[i] = LogPw + bestScore[j]

	## backward path: collect "best"
	listPhrases = []; i = sentLen - 1
	while i > 0:
		## recursion
		if bestPhraseLen[i] > 2:
			if isRecursive:
				bestPhrase[i] = ''.join( ['<'] + viterbi1(bestPhrase[i], bestPhraseLen[i] - 1, isRecursive) + ['>'] )
			else:
				bestPhrase[i] = ''.join( ['\['] + bestPhrase[i] + ['\]'] )
		elif bestPhraseLen[i] == 2:
			bestPhrase[i] = '<' + ''.join(sent[i-bestPhraseLen[i]+1 : i+1]) + '>'
		else:
			bestPhrase[i] = bestPhrase[i] 

		listPhrases[0:0] = [ bestPhrase[i] ]
		i = i - bestPhraseLen[i]

	## return
	return listPhrases

#==============================================================
# isNonHanzi()
#==============================================================
def isNonHanzi(s): return all( (ord(c) < 0x4e00 or ord(c) > 0x9fff) for c in s)

#==============================================================
# add space
#==============================================================
def normalize(sentence):
	phrase = ''
	word_prev = ''
	for word in list(sentence):
		phrase = phrase + ('' if isNonHanzi(word_prev) and isNonHanzi(word) else ' ') + word
		word_prev = word
	return phrase.strip()


def init():
	global querydict
	import pickle

	#==============================================================
	# unigram tokenization
	#==============================================================
	import math
	querydict = pickle.load( open("data/g1.words.P", "rb") )
	logN = math.log10( querydict[''] )
	for word in querydict: querydict[word] = math.log10( querydict[word] ) - logN


if __name__ == "__main__":

	init()
	print(viterbi1(normalize("鼠标和苹果手机")))
