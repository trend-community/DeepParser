#!/usr/bin/python
#==============================================================
# command line
# python3 g1.collectnewwords.py ../data/product_title1.txt ../../fsa/X/AllLexicon.txt ../../fsa/X/AllLexicon_Extra.txt

#==============================================================
import sys, logging, re, argparse
from functools import lru_cache
from collections import defaultdict

_LexiconSet = set()

_Top50="[男女的一了是我不在人们有来他这上着个地到大里说就去子得也和那要下看天时过出小么起你都把好还多没为又]"

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


def CleanDict(d):
    #return
    for k, v in list(d.items()):
        if v <= 0:
            del d[k]
    logging.info("size:{}".format(len(d)))


def RemoveKnownLex(newfile):

    worddict = defaultdict(int)
    logging.info("Start reading file{}".format(newfile))
    with open(newfile) as f:
        content = f.read()
    logging.info("File read.")
    content = re.sub("<[^A-z] [^A-z]>", "_", content)
    content = re.sub("[！，；：。()·（）【】“”\n]", "_", content)
    content = re.sub("  ", "_", content)    #space in original sentence.
    content = re.sub("[<>]", " ", content)
    content = re.sub(r"[^ _][^ _]+", "_", content)

    content = re.sub(_Top50, "_", content)

    content = re.sub(" ", "", content)
    logging.info("Known lexicon removed.")

    wordlist = content.split("_")
    for w in wordlist:
        if len(w) > 1 and not IsAscii(w):  #ignore one character word.
            worddict[w] += 1

    CleanDict(worddict)
    logging.info("Word Dict constructed. Found {} raw words".format(len(worddict)))

    for w in sorted(worddict):
        for partw in sorted([ x for x in worddict if len(x)<len(w)], key=len, reverse=True):
            if partw in w:
                for x in w.replace(partw, " ").split():
                    if len(x) > 1:
                        worddict[x] += worddict[w]
                worddict[partw] += worddict[w]
                worddict[w] = -1  # being replaced by partial words

    CleanDict(worddict)
    logging.info("Finished first round. start second round.")
    #repeat to do the new partial words. assume one repeat is enough.
    for w in sorted(worddict) :
        for partw in sorted([ x for x in worddict if len(x)<len(w)], key=len, reverse=True):
            if partw in w:
                for x in w.replace(partw, " ").split():
                    if len(x) > 1:
                        worddict[x] += worddict[w]
                worddict[partw] += worddict[w]
                worddict[w] = -1    #being replaced by partial words

    CleanDict(worddict)
    logging.info("Word Dict constructed. Found {} new words".format(len(worddict)))
    for w in sorted(worddict, key=worddict.get, reverse=True):
        if worddict[w] > 3:
            print("{}\t{}".format(w, worddict[w]))

    logging.info("Done!")


def _help():
    print("python3 g1.collectnewrods.py [LexicalAnalyze --type simple result file]")


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    if len(sys.argv) < 1:
        _help()
        exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="title parsed file (simple format)")
    args = parser.parse_args()
    RemoveKnownLex(args.input)
