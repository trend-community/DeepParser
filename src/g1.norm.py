#!/usr/bin/python

#Usage for query data:
# Step 1, Generate wordlist.txt by removing special characters and the frequency
# : (Ust Ctrl-V-H to input ^H
#sed - e "s/^H\|^F\|^A.*//g" g0.raw.txt > wordlist.txt
# Step 2, Use g1.norm.py to generate pickle dictionary file w1.P
# Step 3.1 Website can utilize the pickle dictionary file w1.P now
# Step 3.2 Feed wordlist.txt into g1.sent.py using the same pickle dictionary file,
#    to generate rule file rule.txt
# Step 4, Generate "lexicon" from rule.txt using g1.generatelexicon.py
# Step 5, Remove "not rule" from rule.txt by:
#    grep -v "<" rule.txt > cleanrule.txt
# Step 6, include lexicon file and cleanrule.txt in parser pipeline.



#==============================================================
# isNonHanzi()
#==============================================================
def isNonHanzi(ss): return all( (ord(c) < 0x4e00 or ord(c) > 0x9fff) for c in ss)

#==============================================================
# command line
#==============================================================
import argparse, os, logging, traceback
import utils
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input query unigram file")
parser.add_argument("blacklist", help="black list with freq")
parser.add_argument("filter", help="black list with unlimited freq")
parser.add_argument("output", help="output phrase unigram text file")
parser.add_argument("outputdict", help="output phrase unigram pickle dict")
args = parser.parse_args()
print (str(args))

#==============================================================
# The most useful output is the pickle'd dictionary of phrases
# with accumulated frequencies.
#==============================================================
import pickle
import codecs
fin = codecs.open(args.input, 'rb', encoding='utf-8')

from viterbi1 import *

_LexiconFilterSet = set()
_Blacklist_Freq = {}
Freq_Basic = 10
Freq_Basic_Blacklist = 30
Freq_Base = 2000000000.0 * 0.1   # the number in blacklist is based on 2 billion
                            # try using the base as 0.2 billion. 20180309


def LoadLexiconFilterlist(BlacklistLocation):
    if BlacklistLocation.startswith("."):
        BlacklistLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  BlacklistLocation)
    with open(BlacklistLocation, encoding="utf-8") as dictionary:
            for lined in dictionary:
                word, _ = utils.SeparateComment(lined)
                if  word:
                    _LexiconFilterSet.add(word)

def LoadLexiconBlacklist(BlacklistLocation):
    if BlacklistLocation.startswith("."):
        BlacklistLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  BlacklistLocation)
    with open(BlacklistLocation, encoding="utf-8") as dictionary:
            for lined in dictionary:
                content, _ = utils.SeparateComment(lined)
                if not content:
                    continue
                if " " in content or "\t" in content:
                    spaceindex = content.find(" ")
                    if spaceindex < 0:
                        spaceindex = content.find("\t")
                    _word = content[:spaceindex] + "$"
                    _freq = int(content[spaceindex+1:])
                else:
                    _word = content[0] + "$"
                    _freq = Freq_Basic_Blacklist
                _Blacklist_Freq[_word] = _freq



from functools import lru_cache
@lru_cache(maxsize=10000000)
def FreqInLexiconBlacklist(word):
    MaxFreq = -1
    for pattern in _Blacklist_Freq:
        if  re.match(pattern, word):
            if _Blacklist_Freq[pattern] == 0:
                return 0
            if _Blacklist_Freq[pattern] > MaxFreq:
                MaxFreq = _Blacklist_Freq[pattern]

    return MaxFreq


LoadLexiconBlacklist(args.blacklist)
LoadLexiconFilterlist(args.filter)
print(FreqInLexiconBlacklist('我是猫'))
#LoadLexiconBlacklist("../../fsa/X/LexBlacklist_TopChars.txt.zip")
digitsearch = re.compile(r'\d')
N = 0
for line in fin:
    line = line.strip()
    # print line.encode('utf8')
    try:
        #s = line.split('\t', 2)
        [query, freqstring] = line.split('\t', 2)
        freq = int(freqstring)
        if freq < Freq_Basic:       # remove item that less than 10.
            continue
        for chunk in query.split():
            if len(chunk) < 2:
                continue    #ignore one character word.
            if digitsearch.search(chunk):
                continue    #ignore digit
            if chunk in _LexiconFilterSet:
                continue
            phrase = normalize(chunk)
            querydict[phrase] = querydict.get(phrase, 0) + freq

            N = N + freq
    except Exception as e:
        print(" Ignored: error in processing \n\t" + line)
        print(str(e))
        logging.warning(traceback.format_exc())
        continue

logging.info("Start applying blacklist: N=" + str(N))
delta = N/Freq_Base
freq_basic = Freq_Basic*delta
q_list = copy.copy(querydict)
for phrase in q_list:
    if querydict[phrase] < freq_basic:
        del querydict[phrase]
        continue
    originphrase = ''.join(phrase.split())
    blackitem_freq = FreqInLexiconBlacklist(originphrase) #-1 for not in Blacklist
    if blackitem_freq == 0 or querydict[phrase] < blackitem_freq * delta :
        logging.warning("Blacklisted:" + originphrase)
        del querydict[phrase]

fin.close()

querydict[''] = N
pickle.dump( querydict, open(args.outputdict, "wb") )

fout = codecs.open(args.output, 'wb', encoding='utf-8')
for phrase in sorted(querydict, key=querydict.get, reverse=True): fout.write(phrase + '\t' + str(querydict[phrase]) + '\n')
fout.close()
print("Total freq:" + str(N))
