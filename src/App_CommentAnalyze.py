## This is for analyzing commordity title of comment
## input file format: comodity comment
## output: 2 files: class file, and segmentation of each title


import logging, sys, re, os, argparse
import requests, json, jsonpickle
import utils

import singleton
me = singleton.SingleInstance()


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

    Class1 = set() #1
    Class2 = set() #3
    Class3 = set() #5
    CommodityName = set()  # 8
    Brand = set()  #10
    Store = set()  #12
    Company = set() #13

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        Firstline = True
        for line in RuleFile:
            if not line:
                continue
            if Firstline:
                Firstline = False
                continue
            columns = line.split('\t')
            if len(columns) < 10:
                continue
            CommodityName.add(columns[8])

            Class1.add(columns[1])
            Class2.add(columns[3])
            Class3.add(columns[5])
            Brand.add(columns[10])
            Store.add(columns[12])
            Company.add(columns[13])

    foutput = open(os.path.join(args.outputfolder, 'Segmentation.txt'), 'w', encoding="utf-8")

    for Sentence in CommodityName:
        LexicalAnalyzeURL = utils.ParserConfig.get("main", "url_larestfulservice") + "/LexicalAnalyze?Type=simple&Sentence="
        ret = requests.get(LexicalAnalyzeURL + "\"" + Sentence + "\"")
        foutput.write(ret.text + "\n")

    foutput.close()

    foutput = open(os.path.join(args.outputfolder, 'Class1.txt'), 'w', encoding="utf-8")
    for s in Class1:
        foutput.write(s + "\n")
    foutput.close()

    foutput = open(os.path.join(args.outputfolder, 'Class2.txt'), 'w', encoding="utf-8")
    for s in Class2:
        foutput.write(s + "\n")
    foutput.close()

    foutput = open(os.path.join(args.outputfolder, 'Class3.txt'), 'w', encoding="utf-8")
    for s in Class3:
        foutput.write(s + "\n")
    foutput.close()

    foutput = open(os.path.join(args.outputfolder, 'Brand.txt'), 'w', encoding="utf-8")
    for s in Brand:
        foutput.write(s + "\n")
    foutput.close()

    foutput = open(os.path.join(args.outputfolder, 'Store.txt'), 'w', encoding="utf-8")
    for s in Store:
        foutput.write(s + "\n")
    foutput.close()

    foutput = open(os.path.join(args.outputfolder, 'Company.txt'), 'w', encoding="utf-8")
    for s in Company:
        foutput.write(s + "\n")
    foutput.close()

    print("Done. Please check the output files in " + args.outputfolder)


