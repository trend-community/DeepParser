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
def isNonHanzi(s): return all( (ord(c) < 0x4e00 or ord(c) > 0x9fff) for c in s)

#==============================================================
# command line
#==============================================================
import argparse, os, logging
import utils
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input query unigram file")
parser.add_argument("output", help="output phrase unigram text file")
parser.add_argument("dict", help="output phrase unigram pickle dict")
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

_LexiconBlacklist = []
def LoadLexiconBlacklist(BlacklistLocation):
    if BlacklistLocation.startswith("."):
        BlacklistLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  BlacklistLocation)
    with open(BlacklistLocation, encoding="utf-8") as dictionary:
        for lined in dictionary:
            pattern, _ = utils.SeparateComment(lined)
            if not pattern:
                continue
            _LexiconBlacklist.append(pattern)


def InLexiconBlacklist(word):
    for pattern in _LexiconBlacklist:
        if re.match(pattern, word):
            logging.warning("Blacklisted:" + word)
            return True
    return False


digitsearch = re.compile(r'\d')
N = 0
for line in fin:
    line = line.strip()
    # print line.encode('utf8')
    try:
        [query, freqstring] = line.split("", 2)
        freq = int(freqstring)
        for chunk in query.split():
            phrase = normalize(chunk)
            if len(phrase) < 2:
                continue    #ignore one character word.
            if digitsearch.search(phrase):
                continue    #ignore digit
            if len(phrase) == 2 and InLexiconBlacklist(phrase):
                continue
            querydict[phrase] = querydict.get(phrase, 0) + freq
            N = N + freq
    except Exception as e:
        print("error in processing \n\t" + line)
        print(str(e))
        continue
fin.close()

querydict[''] = N
pickle.dump( querydict, open(args.dict, "wb") )

fout = codecs.open(args.output, 'wb', encoding='utf-8')
for phrase in querydict: fout.write(phrase + '\t' + str(querydict[phrase]) + '\n')
fout.close()
