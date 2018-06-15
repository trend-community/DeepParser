#!/usr/bin/python
#==============================================================
# command line
# python3 g1.collectnewwords.py ../data/product_title1.txt ../../fsa/X/AllLexicon.txt ../../fsa/X/AllLexicon_Extra.txt

#==============================================================
import sys, logging, re
from functools import lru_cache

_LexiconSet = set()


@lru_cache(50000)
def IsAscii(Sentence):
    try:
        Sentence.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True


def LoadLexicon(dictpath):
    print("Before loading from lexicon {}, size={}".format(dictpath, len(_LexiconSet)))
    with open(dictpath) as lexicondict:
        for line in lexicondict:
            blocks = [x.strip() for x in re.split(":", line.split("//", 1)[0]) if x]
            if not blocks:
                continue
            if len(blocks[0]) >= 2:     #ignore one character word.
                _LexiconSet.add(blocks[0])
    print("After loading from lexicon, size={}".format( len(_LexiconSet)))


def RemoveKnownLex(newfile):
    worddict = {}
    with open(newfile) as f:
        content = f.read()
    logging.info("File read.")
    content = content.replace("（", "(").replace("）", ")")
    for lex in _LexiconSet:
        if lex in content:
            content = content.replace(lex, " ")
    logging.info("Lexicon replaced")
    wordlist = content.split()
    for w in wordlist:
        if len(w) >= 2 and not IsAscii(w):  #ignore one character word.
            worddict[w] = 1 + worddict.get(w, 0)
    logging.info("Word Dict constructed.")
    for w in sorted(worddict, key=worddict.get, reverse=True):
        if worddict[w] > 3:
            print("{}\t{}".format(w, worddict[w]))


def _help():
    print("python3 g1.collectnewrods.py [newword file] [lex file 1] [lex file 2] ...")


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    if len(sys.argv) < 3:
        _help()
        exit(1)

    for i in range(2, len(sys.argv)):
        LoadLexicon(sys.argv[i])

    RemoveKnownLex(sys.argv[1])