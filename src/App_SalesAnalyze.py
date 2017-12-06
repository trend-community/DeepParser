## This is for analyzing feature/keywords of sales data.
## input file format: sentence\tsalesnum
## output: 2 files: KeywordSales.txt, FeatureSales.txt


import logging, sys, re, os, argparse
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
import requests, json, jsonpickle
from utils import *

import singleton
me = singleton.SingleInstance()
KeywordSales = {}
FeatureSales = {}

def OutputSales():
    KeywordFile = os.path.join(args.outputfolder, 'KeywordSales.txt')
    with open(KeywordFile, "w", encoding="utf-8") as writer:
        for k,v in sorted(KeywordSales.items(), key=lambda d:(d[1], d[0]), reverse = True):
            writer.write(k + "\t" + str(v) + "\n")

    FeatureFile = os.path.join(args.outputfolder, 'FeatureSales.txt')
    with open(FeatureFile, "w", encoding="utf-8") as writer:
        for k,v in sorted(FeatureSales.items(), key=lambda d:(d[1], d[0]), reverse = True):
            writer.write(k + "\t" + str(v) + "\n")

# TODO: Use a database (sqlite?) to store the result. link feature/keyword to an ID for each sentence
def AccumulateNodes(node):
    ignorefeaturelist = ['0', 'npr', 'n', 'XP', '+++', 'a', 'spaceH', 'spaceQ', 'leftB', 'ho', 'sufM', 'fN', 'Pred', 'N0', 'freeM',
                         'boundM', 'an', 'hb', '3', 'cNf', 'fNm', 'c1clear', 'Up', 'enDo', 'doSum', 'VNPPPto', 'cn', 'buyuC', 'Down',
                         'sh', 'preNumc', 'notMod', 'V0', 'vt', 'vn', 'vi', 'A0', '1unit']
    featurelist = node['features']
    if 'punc' in featurelist or len(node['text'].strip()) == 0:
        pass
    else:
        for feature in featurelist:
            if feature in ignorefeaturelist:
                continue

            if feature not in FeatureSales:
                FeatureSales[feature] = 0
            FeatureSales[feature] += UnitTest[Sentence]
        if node['text'] not in KeywordSales:
            KeywordSales[node['text']] = 0
        KeywordSales[node['text']] += UnitTest[Sentence]


    if 'sons' in node:
        for s in node['sons']:
            AccumulateNodes(s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("outputfolder", help="output folder location")
    args = parser.parse_args()
    print(args)

    level = logging.DEBUG

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    UnitTest = {}
    if not os.path.exists(args.inputfile):
        print("Unit Test file " + args.inputfile + " does not exist.")
        exit(0)

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                Content, _ = SeparateComment(line.strip())
                if  Content and '\t' in Content:    # For the testfile that only have test sentence, not rule name
                    TestSentence, Sales = Content.split('\t', 2)
                    UnitTest[TestSentence] = int(Sales)

    #ProcessSentence.LoadCommon()


    for Sentence in UnitTest:
        LexicalAnalyzeURL = ParserConfig.get("main", "url_larestfulservice") + "/LexicalAnalyze?Type=json&Sentence="
        ret = requests.get(LexicalAnalyzeURL + "\"" + Sentence + "\"")
        root =  jsonpickle.decode(ret.text)
        AccumulateNodes(root)

    OutputSales()

