#!/usr/bin/python
#==============================================================
# command line
# python3 g1.collectnewwords.py ../data/product_title1.txt ../../fsa/X/AllLexicon.txt ../../fsa/X/AllLexicon_Extra.txt

#==============================================================
import sys, logging, re
from functools import lru_cache
from collections import defaultdict

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

    worddict = defaultdict(int)
    logging.info("Start reading file{}".format(newfile))
    with open(newfile) as f:
        content = f.read()
    logging.info("File read.")
    content = re.sub("[！，；。（）【】“”]", " ", content)
    content = re.sub(r"[ -z]", " ", content)
    while "   " in content:
        content = re.sub("   ", " ", content)
    content = re.sub("  ", " ", content)
    logging.info("English Alphabet removed.")

    for lex in _LexiconSet:
        if lex in content:
            content = content.replace(lex, " ")
    logging.info("Lexicon replaced.")

    wordlist = content.split()
    for w in wordlist:
        if len(w) > 1 and not IsAscii(w):  #ignore one character word.
            worddict[w] += 1
    logging.info("Word Dict constructed. Found {} raw words".format(len(worddict)))

    for w in sorted(worddict):
        for partw in [ x for x in worddict if len(x)<len(w)]:
            if partw in w:
                for x in w.replace(partw, " ").split():
                    if len(x) > 1:
                        worddict[x] += worddict[w]
                worddict[w] = -1    #being replaced by partial words

    #repeat to do the new partial words. assume one repeat is enough.
    for w in sorted(worddict):
        for partw in [ x for x in worddict if len(x)<len(w)]:
            if partw in w:
                for x in w.replace(partw, " ").split():
                    if len(x) > 1:
                        worddict[x] += worddict[w]
                worddict[w] = -1    #being replaced by partial words

    logging.info("Word Dict constructed. Found {} new words".format(len(worddict)))
    for w in sorted(worddict, key=worddict.get, reverse=True):
        if worddict[w] > 3:
            print("{}\t{}".format(w, worddict[w]))

    logging.info("Done!")

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
