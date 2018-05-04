#!/usr/bin/python -u
import re

# ==============================================================
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
# ==============================================================
import copy

querydict = {}
lookupset = set()
minLogPw = -21  # Zetta-words


def viterbi1(strSent, maxPhraseLen=20, isRecursive=True):
    ## init
    if querydict[strSent] == -4: #System Lexicon
        return ["".join(strSent.split())]

    sent = ['^'] + strSent.split()
    sentLen = len(sent)
    bestPhrase = copy.deepcopy(sent)
    bestPhraseLen = [1] * sentLen
    bestScore = [0.0] + [(minLogPw * i) for i in range(1, sentLen + 1)]

    ## forward path: fill up "best"
    for i in range(1, sentLen):
        for j in range(max(0, i - maxPhraseLen), i):
            phrase = ' '.join(sent[j + 1:i + 1])
            LogPw = querydict.get(phrase, 0)
            if LogPw != 0 and LogPw + bestScore[j] > bestScore[i]:
                bestPhrase[i] = phrase
                bestPhraseLen[i] = i - j
                bestScore[i] = LogPw + bestScore[j]

    ## backward path: collect "best"
    listPhrases = []
    i = sentLen - 1
    while i > 0:
        ## recursion
        if bestPhraseLen[i] > 2:
            if isRecursive:
                subPhrases = viterbi1(bestPhrase[i], bestPhraseLen[i] - 1, isRecursive)
                if 1 < len(subPhrases) < len(bestPhrase[i].split()):
                    bestPhrase[i] = '<' + ' '.join(subPhrases) + '>'
                else:
                    bestPhrase[i] = ''.join(subPhrases)
            else:
                bestPhrase[i] = ''.join(['\['] + bestPhrase[i] + ['\]'])
        elif bestPhraseLen[i] == 2:  # one word. leave it be.
            bestPhrase[i] = ''.join(sent[i + 1 - 2: i + 1])
        else:
            bestPhrase[i] = bestPhrase[i]

        listPhrases[0:0] = [bestPhrase[i]]
        i = i - bestPhraseLen[i]

    ## return
    return listPhrases


def QuerySegment(Sentence):
    resultPhraseList = viterbi1(normalize(Sentence.strip()), len(Sentence))

    if not resultPhraseList:
        return ''
    if len(resultPhraseList) > 1:
        resultPhrase = '<' + ' '.join(resultPhraseList) + '>'
    else:
        resultPhrase = resultPhraseList[0]
    return resultPhrase


# ==============================================================
# isNonHanzi()
# ==============================================================
def isNonHanzi(s): return all((ord(c) < 0x4e00 or ord(c) > 0x9fff) for c in s)


# ==============================================================
# normalize queries by taking space delimited chunks as phrases
# and by adding spaces in between 'words'
# Here a 'word' is defined as English word or single Chinese character
# ==============================================================
def normalize(sentence):
    phrase = ''
    word_prev = ''
    for word in list(sentence):
        phrase = phrase + ('' if isNonHanzi(word_prev) and isNonHanzi(word) else ' ') + word
        word_prev = word
    return phrase.strip()


def LoadDictFromPickle(dictpath="../data/g1.words.P"):
    global querydict
    import pickle

    # ==============================================================
    # unigram tokenization
    # ==============================================================
    import math
    querydict = pickle.load(open(dictpath, "rb"))
    logN = math.log10(querydict[''])
    for word in querydict:
        querydict[word] = math.log10(querydict[word]) - logN


def LoadDictFromLexicon(dictpath, value):
    global querydict
    print("Before loading from lexicon, size:" + str(len(querydict)))
    with open(dictpath) as lexicondict:
        for line in lexicondict:
            if len(line.strip()) >= 2:
                querydict[normalize(line.strip())] = value
    print("After loading from lexicon, size:" + str(len(querydict)))
    if '中 介' in querydict:
        print("querydict['中 介']=" + str(querydict['中 介']))
    if '军 刀 黑' in querydict:
        print("querydict['军 刀 黑']=" + str(querydict['军 刀 黑']))
    if '胖 妹 妹' in querydict:
        print("querydict['胖 妹 妹']=" + str(querydict['胖 妹 妹']))

def LoadLookupDictFromLexicon(dictpath):
    global querydict
    print("Before loading from lexicon, size:" + str(len(querydict)))
    with open(dictpath) as lexicondict:
        for line in lexicondict:
            if len(line.strip()) >= 2:
                lookupset.add(normalize(line.strip()))
    print("After loading lookup dict from lexicon, size:" + str(len(lookupset)))
    if '中 介' in lookupset:
        print("['中 介'] in lookupset" )
    if '军 刀 黑' in lookupset:
        print("['军 刀 黑'] in lookupset" )
    if '胖 妹 妹' in lookupset:
        print("['胖 妹 妹'] in lookupset" )


if __name__ == "__main__":
    LoadDictFromPickle()

    print(QuerySegment("鼠标和小米手机"))
