### 1, read in corpus
#   2, sliding window, get all "words". length: 2 character/3 characters; (Chinese characters)
#   3, for each word, in a fix-size window, get all neighbour words, with counts. (for query, the frequency can be used)
#   3.5, trim the neighour words to a specific size, such as 10 (or 100) neighbours.
#   4, for specific words to query, calculate the similarity of the neighbour with other words.
#   5, output the highest similar words. specify the highest word that are already in our system lexicon.
# for step 4, "graph", neo4j is good.

#usage: python3 WordEmbedding.py ../../../fsa/test/input/testCoffee.txt 10 50 ../../../fsa/X/Q/lexicon/CleanLexicon_gram_2_list.txt ../../../fsa/X/AllLexicon.txt
# python3 WordEmbedding.py --query q ../../temp/g0.raw.txt 10 50 ../../../fsa/X/Q/lexicon/CleanLexicon_gram_2_list.txt ../../../fsa/X/AllLexicon.txt


import argparse, logging
import re
from collections import defaultdict

WordList2 = []
WordDict = {}
NeighbourList = []  # each neighbour is a dict (word:frequency).
stopsigns = '[' + '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.'
stopsigns += ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~' + ']'
restopsigns = re.compile(stopsigns)
LexiconWordIDs = []
LexiconWords = []

#push the s[i] (2 and 3 character words) into the window, and remove the oldest one.
# return: the link betwen the new ones and the existing ones
def WindowPush(s, i, w):
    for item in list(w.keys()):
        w[item] -= 1
        if w[item] < 0:
            del w[item]

    newrelationship = []
    existingwords = list(w.keys())
    if len(s) >= i+2:
        newwordid = InsertOrGetID( s[i:i+2])
        if newwordid >= 0:
            w[newwordid] = neighbourwindowsize
            newrelationship = [(newwordid, oldid) for oldid in existingwords
                                    if len(WordList2[oldid]) + w[oldid] < neighbourwindowsize    #exclude overlap word as neighbour.

                               ]

    if len(s) >= i+3:
        newwordid = InsertOrGetID( s[i:i+3])
        if newwordid >= 0:
            w[newwordid] = neighbourwindowsize
            newrelationship.extend([(newwordid, oldid) for oldid in existingwords
                                    if len(WordList2[oldid]) + w[oldid] < neighbourwindowsize

                                ])

    return newrelationship


def InsertOrGetID( word):
    if word not in BothWords:
        return -1

    if word not in WordDict:
        WordDict[word] = len(WordList2)
        WordList2.append(word)
        frequencypair = defaultdict(int)
        NeighbourList.append(frequencypair)

    return WordDict.get(word, -1)


def ImportCorpus(line):
    freq = 1
    if args.query:
        try:
            line, freq = re.split('\x01', line)
            freq = int(freq)
        except ValueError:
            return
    if not line:
        return
    sentences = restopsigns.split(line)
    #sentences = re.split(stopsigns, line)
    for sentence in sentences:
        window = dict()
        for index in range(len(sentence) - 1):
            newrelations = WindowPush(sentence, index, window)
            for r in newrelations:
                NeighbourList[r[0]][r[1]] += freq  #can be the query frequency here.
                NeighbourList[r[1]][r[0]] += freq


    # remove the words that are not in  QueryWords or word in LexiconWords
    # re-index
def TrimNeighbours(size = 3):
    global LexiconWordIDs
    logging.info("Start creating LexiconIDs")
    LexiconWordIDs = [WordDict.get(w, -1) for w in LexiconWords]
    logging.info("Start trimming neighbourlist")
    for i in range(len(NeighbourList)):
        NeighbourList[i] = {k:NeighbourList[i][k] for k in sorted(NeighbourList[i], key=NeighbourList[i].get, reverse=True)[:size]} #  if k in LexiconWordIDs}

    logging.info("finished trimming neighbourlist!")


#DistanceCache = {}
def Distance(a, b, a_neighbourdict, a_neighbourset):
    # if (b, a) in DistanceCache:
    #     return DistanceCache[(b, a)]
    # if (a, b) in DistanceCache:
    #     return DistanceCache[(a, b)]

    intersec = a_neighbourset.intersection(NeighbourList[b].keys())
    distance = 0
    if intersec:
        distance = sum([(1 - abs(a_neighbourdict[x] - NeighbourList[b][x]) / (a_neighbourdict[x] + NeighbourList[b][x]))
                        for x in intersec])    / (len(a_neighbourdict)+len(NeighbourList[b]))
#        DistanceCache[(a, b)] = distance
    return distance


def SimilarWord(word):
    if word not in WordDict:
        return None, None
    wordid = WordDict[word]
    neighbourdict = NeighbourList[wordid]
    if len(neighbourdict) == 0:
        return None, None

    neighbourset  = set(neighbourdict.keys())
    similarlist = {}
    for i in range(len(NeighbourList)):
        if i == wordid:
            continue

        distance = Distance(wordid, i, neighbourdict, neighbourset)

        if distance > 0:
            similarlist[i] = distance

    result = sorted(similarlist, key=similarlist.get, reverse=True)[:100]

    output = word + ":"
    for index in result:
       if index == WordDict[word]:
           continue
       output +=  WordList2[index] + "(" + str(similarlist[index]) + ") "
#    print(output)

    return result, similarlist


def LoadCorpus(FileName):
    with open(FileName, encoding="utf-8") as CorpusFile:
        for line in CorpusFile:
            if line.strip():
                ImportCorpus(line.strip())
    logging.info("Finish loading")
    logging.info("Word size: " + str(len(NeighbourList)))


#one word each line. stop at stopsign
def LoadFile(FileName, stopsign=' '):
    result = []
    with open(FileName, encoding="utf-8") as CorpusFile:
        for line in CorpusFile:
            if line.strip():
                result.append(line.strip().split(stopsign)[0])
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument("corpusfile", help="input file")
    parser.add_argument("neighbourwindowsize", help="how far away considered as neighbour")
    parser.add_argument("neighboursize", help="20?")
    parser.add_argument("querywordfile", help="the words to query")
    parser.add_argument("lexiconwordfile", help="known words")
    parser.add_argument("--query", help="for query file with \01 with frequency")
    parser.add_argument("--all", help="output all match words")

    args = parser.parse_args()

    neighbourwindowsize = int(args.neighbourwindowsize)
    logging.info("Start.")

    QueryWords = LoadFile(args.querywordfile)
    LexiconWords = LoadFile(args.lexiconwordfile, ':')
    BothWords = set(QueryWords+LexiconWords)

    import cProfile, pstats
    cProfile.run("LoadCorpus(args.corpusfile)", 'restats')
    p = pstats.Stats('restats')
    p.sort_stats('time').print_stats(20)

    #LoadCorpus(args.corpusfile)

    TrimNeighbours(int(args.neighboursize))


    for q in QueryWords:
        #cProfile.run("SimilarWord(q)", 'sw')

        swlist, swdict = SimilarWord(q)
        if swlist:
            similarwords = q + ":"
            count = 0
            for sw in swlist:
                if sw in LexiconWordIDs:
                    similarwords += " '"+ WordList2[sw] + "'"
                    similarwords += "(" + str(swdict[sw]) + ")"
                    if not args.all:
                        break
                    count += 1
                    if count > 10:
                        break
            print(similarwords)
    # psw = pstats.Stats('sw')
    # psw.sort_stats('time').print_stats(10)
    logging.info("Done.")
