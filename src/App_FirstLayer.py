## This is for analyzing feature/keywords of sales data.
## input file format: sentence\tsalesnum
## output: 2 files: KeywordSales.txt, FeatureSales.txt


import logging, sys, re, os, argparse
import requests, json, jsonpickle

KeywordSales = {}
FeatureSales = {}


#
def ExtractNextLayer(node):
    if 'sons' in node:
        nodestr = []
        for s in node['sons']:
            nodestr.append("[\"features:\": [" + ",".join(s['features']) + "], \"text\": " + s['text'] + "]")
            #ExtractNextLayer(s)    #for extracting recursively
        print("{" + ",".join(nodestr) + "}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    UnitTest = {}
    if not os.path.exists(args.inputfile):
        print("Json file " + args.inputfile + " does not exist.")
        exit(0)

    with open(args.inputfile, encoding="utf-8") as jsonfile:
        for line in jsonfile:
            root =  jsonpickle.decode(line)
            ExtractNextLayer(root)

    logging.info("Done. ")

