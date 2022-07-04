#The input is a list of documents, each as one line in a file.
#the output is jason objects in one file.
import logging, sys, os, jsonpickle
import ProcessSentence, Rules, FeatureOntology
from utils import *

import singleton
me = singleton.SingleInstance()

def SentenceSegmentation(Doc):
    Sentences = [x.strip() for x in re.split("([。；！])", Doc) if x]
    #combine the sign with previous one.
    for i in range(len(Sentences)-1, -1, -1):
        if Sentences[i] in "。；！" and i>0:
            Sentences[i-1] += Sentences[i]
            del Sentences[i]

    return Sentences


if __name__ == "__main__":
    jsonpickle.set_encoder_options('json', ensure_ascii=False)
    DebugMode = False
    NoFeature = False
    level = logging.INFO
    UnitTestFileName = ''
    if len(sys.argv) > 1:
        UnitTestFileName = sys.argv[1]
        if len(sys.argv) > 2:
            command = sys.argv[2]
            if command == 'Debug':
                DebugMode = True
                level = logging.DEBUG
            if command == 'NoFeature':
                NoFeature = True

    else:
        print(
            "Usage: python ProcessDocuments.py file [Debug]/[NoFeature]")
        exit(0)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    ProcessSentence.LoadCommon()

    DocList = []
    if not os.path.exists(UnitTestFileName):
        print("Unit Test file " + UnitTestFileName + " does not exist.")
        exit(0)

    with open(UnitTestFileName, encoding="utf-8") as DocFile:
        for line in DocFile:
            if line.strip():
                DocList.append(line)

    for doc in DocList:
        sentences = SentenceSegmentation(doc)

        nodeslist = []
        for TestSentence in sentences:

            TestSentence = TestSentence.strip("/")
            if DebugMode:
                print("*** runing sentence: " + TestSentence)

            nodes, _ = ProcessSentence.LexicalAnalyze(TestSentence)

            if DebugMode:
                for node in nodes:
                    print(node)

            nodeslist.append(nodes)
        print(jsonpickle.encode(nodeslist))


