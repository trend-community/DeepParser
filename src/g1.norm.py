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
import pickle, zipfile
import codecs
fin = codecs.open(args.input, 'rb', encoding='utf-8')

from viterbi1 import *

_LexiconBlacklist = []
_Blacklist_Freq = {}
Freq_Basic = 10
Freq_Basic_Blacklist = 30
Freq_Base = 200000000.0   # the number in blacklist is based on 2 billion
                            # try using the base as 0.2 billion. 20180309

def LoadLexiconBlacklist(BlacklistLocation, freq_basic = Freq_Basic_Blacklist):
    if BlacklistLocation.startswith("."):
        BlacklistLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  BlacklistLocation)
    if BlacklistLocation.endswith(".txt.zip"):
        with zipfile.ZipFile(BlacklistLocation) as z:
            with  z.open(os.path.basename(BlacklistLocation)[:-4]) as dictionary:
                for lined in dictionary:
                    line = lined.decode("utf-8", "ignore")
                    pattern, _ = utils.SeparateComment(line)
                    if not pattern:
                        continue
                    blocks = [x.strip() for x in re.split(":", pattern) if x]
                    if not blocks:
                        continue
                    _LexiconBlacklist.append(blocks[0] + "$")  # from begin to end
    else:
        with open(BlacklistLocation, encoding="utf-8") as dictionary:
            for lined in dictionary:
                pattern, _ = utils.SeparateComment(lined)
                if not pattern:
                    continue
                blocks = [x.strip() for x in re.split(":", pattern) if x]
                if not blocks:
                    continue
                word_freq = blocks[0].split()
                if len(word_freq) == 2:
                    _Blacklist_Freq[word_freq[0]+"$"] = int(word_freq[1])
                else:
                    _Blacklist_Freq[word_freq[0]+"$"] = freq_basic
                _LexiconBlacklist.append(word_freq[0]+"$") #from begin to end


from functools import lru_cache
@lru_cache(maxsize=1000000)
def FreqInLexiconBlacklist(word):
    for pattern in _LexiconBlacklist:
        if re.match(pattern, word):
            return _Blacklist_Freq[pattern]
    return -1


LoadLexiconBlacklist(args.blacklist)
LoadLexiconBlacklist(args.filter, 0)

#LoadLexiconBlacklist("../../fsa/X/LexBlacklist_TopChars.txt.zip")
digitsearch = re.compile(r'\d')
N = 0
for line in fin:
    line = line.strip()
    # print line.encode('utf8')
    try:
        s = line.split('\x01', 2)
        [query, freqstring] = line.split('\x01', 2)
        freq = int(freqstring)
        if freq < Freq_Basic:       # remove item that less than 10.
            continue
        for chunk in query.split():
            if len(chunk) < 2:
                continue    #ignore one character word.
            if digitsearch.search(chunk):
                continue    #ignore digit
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
q_list = copy.copy(querydict)
for phrase in q_list:
    if querydict[phrase] < Freq_Basic*delta:
        del querydict[phrase]
        continue
    originphrase = ''.join(phrase.split())
    blackitem_freq = FreqInLexiconBlacklist(originphrase) #-1 for not in Blacklist
    if querydict[phrase] < blackitem_freq * delta or blackitem_freq == 0:
        logging.warning("Blacklisted:" + originphrase)
        del querydict[phrase]

fin.close()

querydict[''] = N
pickle.dump( querydict, open(args.outputdict, "wb") )

fout = codecs.open(args.output, 'wb', encoding='utf-8')
for phrase in querydict: fout.write(phrase + '\t' + str(querydict[phrase]) + '\n')
fout.close()
print("Total freq:" + str(N))
