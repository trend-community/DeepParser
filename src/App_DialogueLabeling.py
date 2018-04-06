## This is for analyzing feature/keywords of sales data.
## input file format: sentence\tsalesnum
## output: 2 files: KeywordSales.txt, FeatureSales.txt
# cut -d ',' -f 5,8 '1627被子20171111_20171212171010[10756].csv'
# awk -F',' '{print($2,"\t",$1)}' 1627sale.txt  > 1627sale2.txt

# cut -d ',' -f 5,8 '7052婴幼奶粉20171111_20171212170000[10757].csv' | awk -F',' '{print($2,"\t",$1)}'   > 7052sale2.txt

import logging,  os, argparse
import requests,  jsonpickle
import utils

import singleton
me = singleton.SingleInstance()


# TODO: Use a database (sqlite?) to store the result. link feature/keyword to an ID for each sentence
def AccumulateNodes(node):
    knownitems = {"orgNE":"组织",
                  "comNE":"公司",
                  "perNE":"人名",
                  "prodNE": "产品",
                  "locNE":  "地点",
                  "color":  "颜色",
                  "taste":  "味道",
                  "size":   "大小",
                  "length": "长度",
                  "weight": "重量",
                  "height": "高度",
                  "price":  "价格",
                  "money":  "价格"}
    for feature in node['features']:
        if feature in knownitems:
            return {node["text"]: knownitems[feature]}

    if 'sons' in node:
        alllist = {}
        for s in node['sons']:
            alllist.update( AccumulateNodes(s))
        return alllist
    else:
        return {node["text"]: ''}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
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

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                Content, _ = utils.SeparateComment(line.strip())
                UnitTest.append(Content)

    for Sentence in UnitTest:
        LexicalAnalyzeURL = utils.ParserConfig.get("client", "url_larestfulservice") + "/LexicalAnalyze?Type=json&Sentence="
        ret = requests.get(LexicalAnalyzeURL + "\"" + Sentence + "\"")
        root =  jsonpickle.decode(ret.text)
#        for s in root['sons']:  # ignore the root
        pairlist = AccumulateNodes(root)
        result = "/".join([pair+"_" + pairlist[pair] if pairlist[pair] else pair for pair in pairlist])
        print(result)

        #AccumulateNodes(root)

    print("Done. ")

