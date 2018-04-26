## This is for analyzing feature/keywords of sales data.
## input file format: sentence\tsalesnum
## output: 2 files: KeywordSales.txt, FeatureSales.txt


import logging,  os, argparse
import requests,  jsonpickle
import utils

import singleton
me = singleton.SingleInstance()

# TODO: Use a database (sqlite?) to store the result. link feature/keyword to an ID for each sentence
def CollectFeatures(node, KeywordSet, FeatureSet, IsRoot):
    ignorefeaturelist = ['0', 'npr', 'n', 'XP', '+++', 'a', 'spaceH', 'spaceQ', 'leftB', 'ho', 'sufM', 'fN', 'Pred', 'N0', 'freeM',
                         'boundM', 'an', 'hb', '3', 'cNf', 'fNm', 'c1clear', 'Up', 'enDo', 'doSum', 'VNPPPto', 'cn', 'buyuC', 'Down',
                         'sh', 'preNumc', 'notMod', 'V0', 'vt', 'vn', 'vi', 'A0', '1unit']
    featurelist = node['features']
    if 'punc' in featurelist or len(node['text'].strip()) == 0 or IsRoot:
        pass
    else:
        for feature in featurelist:
            if feature in ignorefeaturelist:
                continue

            if feature not in FeatureSet:
                FeatureSet.add(feature)
        if node['text'] not in KeywordSet :
            KeywordSet.add(node['text'])


    if 'sons' in node:
        for s in node['sons']:
            CollectFeatures(s, KeywordSet, FeatureSet, IsRoot = False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("outputfolder", help="output folder location")
    args = parser.parse_args()
    print(args)

    level = logging.INFO

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    UnitTest = []
    if not os.path.exists(args.inputfile):
        print("Unit Test file " + args.inputfile + " does not exist.")
        exit(0)

    UnitTest = {}

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            columns = line.split(',')
            if len(columns) > 4 and columns[3].isdigit():
                UnitTest[columns[7].strip()] = columns[3]



    fidlist = open(os.path.join(args.outputfolder, 'IDList.txt'), 'w', encoding="utf-8")
    fkeyword = open(os.path.join(args.outputfolder, 'Keywords.txt'), 'w', encoding="utf-8")
    ffeature = open(os.path.join(args.outputfolder, 'Features.txt'), 'w', encoding="utf-8")
    fidlist.writelines("//ID\t Sentence" + "\n")
    fkeyword.writelines("//ID\t Keyword" + "\n")
    ffeature.writelines("//ID\t Feature" + "\n")

    x = 0

    for Sentence in UnitTest:
        ID = UnitTest[Sentence]
        LexicalAnalyzeURL = utils.ParserConfig.get("main", "url_larestfulservice") + "/LexicalAnalyze?Type=json&Sentence="
        ret = requests.get(LexicalAnalyzeURL + "\"" + Sentence + "\"")
        root =  jsonpickle.decode(ret.text)
        KeywordSet = set()
        FeatureSet = set()

        CollectFeatures(root, KeywordSet, FeatureSet, IsRoot = True)

        fidlist.writelines(str(ID) + "\t" + Sentence + "\n")
        for k in sorted(KeywordSet):
            fkeyword.write(str(ID) + "\t" + k + "\n")
        for f in sorted(FeatureSet):
            ffeature.write(str(ID) + "\t" + f + "\n")


    print("Done. Please check the output files in " + args.outputfolder)

    ffeature.close()
    fkeyword.close()
    fidlist.close()
