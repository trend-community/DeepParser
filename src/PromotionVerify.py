import argparse
import ProcessSentence
from utils import *

#File format:  intent\tQ
#intent that we care:
# 1173 能否优惠
# 2184 近期活动咨询
# 940 促销形式
# 54 评价晒单返券和赠品
# 0  赠品领取更换

class Intent(object):
    def __init__(self, pair):
        if len(pair) != 2:
            logging.error("Wrong Intent initialization parameter: {}".format(pair))
        self.Q = pair[1].strip()
        self.Intent = pair[0].strip()
        self.tags = set()

intents = []

def ProcessFile(FileName):
    if FileName.startswith("."):
        FileName = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FileName)

    if not os.path.exists(FileName):
        print("Unit Test file " + FileName + " does not exist.")
        exit(0)

    with open(FileName, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                intent = Intent(line.split(args.delimiter))
                intents.append(intent)


    for intent in intents:
        nodes, dag, _ = ProcessSentence.LexicalAnalyze(intent.Q)
        if not nodes:
            logging.warning("The result for this sentence '{}' is None! ".format(intent.Q))
            continue
        for nodeid in dag.nodes:
            if dag.nodes[nodeid].pnorm:
                intent.tags.add(dag.nodes[nodeid].pnorm)
        logging.info("Gold Standard: {}\tResult:{}".format(intent.Intent, intent.tags))

    PromotionTags=["能否优惠", "近期活动咨询", "促销形式", "评价晒单返券和赠品", "赠品领取更换"]
    for Tag in PromotionTags:
        TP = 0
        FP = 0
        FN = 0
        TN = 0
        P = 0
        R = 0
        F = 0
        for intent in intents:
            if intent.Intent == Tag:
                if Tag in intent.tags:
                    TP += 1
                else:
                    FN += 1
            else:
                if Tag in intent.tags:
                    FP += 1
                else:
                    TN += 1
        print("Tag {}: TP={}, FN={}, FP={}, TN={}".format(Tag, TP, FN, FP, TN))
        if (TP+FP) > 0:
            P = TP/(TP+FP)
        if (TP+FN) >0:
            R = TP/(TP+FN)
        if (P+R) > 0:
            F = 2*P*R/(P+R)
        print("\tPrecision={}, Recall={}, F score={}".format(P, R, F))
        print("\tFN cases:")
        for intent in intents:
            if intent.Intent == Tag:
                if Tag not in intent.tags:
                    print("\t\t{}-{}\t{}".format(intent.Intent, intent.tags, intent.Q))
        print("\tFP cases:")
        for intent in intents:
            if intent.Intent != Tag:
                if Tag  in intent.tags:
                    print("\t\t{}-{}\t{}".format(intent.Intent, intent.tags, intent.Q))

    print("Sentence that has more than 1 tags:")
    for intent in intents:
        if len(intent.tags) > 1:
            print("\t{}-{}\t{}".format(intent.Intent, intent.tags, intent.Q))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--delimiter", default="\t")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    ProcessSentence.LoadCommon()

    ProcessFile(args.inputfile)

