## This is for labeling KG keywords

import logging,  os, argparse, sqlite3, atexit
import requests,  jsonpickle
import utils

import singleton
me = singleton.SingleInstance()

KGExtraDB = None
ThirdNames = set()
AttributeNames = set()
def Init():
    """load third class name;
        load KGKeys
    """

    global KGExtraDB
    try:
        KGExtraDB = sqlite3.connect('../data/KGAppendix.db')
    except sqlite3.OperationalError:
        logging.error("Database file does not exists!")
        return

    cur = KGExtraDB.cursor()
    cur.execute("PRAGMA synchronous=2;")
    cur.execute("PRAGMA journal_mode=0;")
    cur.execute("PRAGMA TEMP_STORE=MEMORY;")  # reference: https://www.sqlite.org/wal.html

    KGExtraDB.commit()
    logging.info("DBCon Init")
    atexit.register(CloseDB)

    #global ThirdNames, AttributeNames
    strsql = "select item_third_cate_name from category"
    cur.execute(strsql)
    rows = cur.fetchall()
    for row in rows:
        names = row[0].split('/')
        for name in names:
            ThirdNames.add(name)

    strsql = "select com_attr_name from attributes"
    cur.execute(strsql)
    rows = cur.fetchall()
    for row in rows:
        AttributeNames.add(row[0])
    cur.close()


def CloseDB():
    KGExtraDB.commit()
    KGExtraDB.close()
    logging.info("DBCon closed.")


def SeparateValues():
    """ one time thing, to separate the values by "," signs.
    """
    cur = KGExtraDB.cursor()
    strsearch = """select com_attr_group_name, com_attr_name, com_attr_value from attribute 
                where  com_attr_value like '%、%' or  com_attr_value like '%;%' com_attr_value like '%；%'"""
    cur.execute(strsearch)
    rows = cur.fetchall()
    for row in rows:
        com_attr_group_name = row[0]
        com_attr_name = row[1]
        combinedvalue = row[2]


# filterfeatures = ("measure", "attrC",
#                      "orgNE", "comNE", "prodNE", "brand",
#                      "color", "taste", "size", "length", "weight",
#                      "height", "temp", "prod"
#                   )
filterfeatures = ("color", "height", "length", "width", "size",
                  "volt", "electricity", "weight", "density", "temp")

blacklistfeatures = ("price", "money")

def Filtering(node):

    for f in node["features"]:
        if f in filterfeatures:
            return True

    if 'sons' in node:
        for s in node['sons']:
            if Filtering(s):
                return True
    return False

def Blacklist(node):
    for f in node["features"]:
        if f in blacklistfeatures:
            return True
    if 'sons' in node:
        for s in node['sons']:
            if  Blacklist(s):
                return True
    return False

# TODO: Use a database (sqlite?) to store the result. link feature/keyword to an ID for each sentence
def AccumulateNodes(node, upperfoundfeature = False):
    knownitems = {"orgNE":  "组织",
                  "comNE":  "公司",
                  "perNE":  "人名",
                  "prodNE": "品牌",
                  "brand":  "品牌",
                  "locNE":  "地点",
                  "color":  "颜色",
                  "taste":  "味道",
                  "size":   "大小",
                  "length": "长度",
                  "weight": "重量",
                  "height": "高度",
                  "price":  "价格",
                  "money":  "价格",
                  "temp":   "温度"}

    if "text" not in node:
        logging.warning("Wrong text.")
        return False
    text = node["text"]
    if text in ("一个", "两个", "三个"):
        return [(text, '')]


    if len(text) > 1 and ("NC" in node['features'] or "AP" in node['features']):
        for name in ThirdNames:
            if text == name:
                return [(text, '三级品类')]

        cur = KGExtraDB.cursor()
        strsql = """select distinct com_attr_name from attribute where com_attr_value=?
            and com_attr_name<>'适用类型' and com_attr_name<>'型号'
         order by com_attr_name<>'品牌' limit 1"""
        cur.execute(strsql, [text, ])
        rows = cur.fetchall()
        if rows:
            keys = ";".join([row[0] for row in rows])
            return [(text, keys)]
    if "keyKG" in node['features']:
        return [(text, "属性名称")]
    if "valueKG" in node['features']:
        return [(text, "属性值")]


    text_feature = ''
    if len(text) > 1 and ("NC" in node['features'] or "AP" in node['features']):
        for feature in node['features']:
            if feature in knownitems:
                text_feature = knownitems[feature]


    if 'sons' in node:
        alllist = []
        hit = False
        for s in node['sons']:
            parsed = AccumulateNodes(s, text_feature!='')
            alllist += parsed
            for p in parsed:
                if p[1]:
                    hit = True
                    break
        if hit or not upperfoundfeature:
            return alllist

    return [(text, text_feature)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("filter", help="yes/no. Set to no for trusted questions")
    args = parser.parse_args()
    print(args)

    level = logging.INFO

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    Init()

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
        try:
            ret = requests.get(LexicalAnalyzeURL + "\"" + Sentence + "\"")
        except requests.exceptions.ConnectionError as e:
            logging.warning("Failed to process:\n" + Sentence)
            continue
        root =  jsonpickle.decode(ret.text)
#        for s in root['sons']:  # ignore the root
        pairlist = AccumulateNodes(root)
        result = "".join([pair[0]+"_" + pair[1] + " " if pair[1] else pair[0] for pair in pairlist])
        if args.filter == "no":
            print(result)
        else:
            if Filtering(root) and not Blacklist(root):
                print(result )

        #AccumulateNodes(root)

    print("Done. ")

