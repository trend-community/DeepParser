import argparse, logging, os, sys, re
import requests, urllib, sqlite3


# LexicalAnalyzeURL = "http://localhost:4001/Normalize/"
#
# def NTask(Sentence):
#     url = LexicalAnalyzeURL+  urllib.parse.quote(Sentence)
#     #logging.debug("Start: " + url)
#     ret = requests.get(url)
#     return ret.text

def NormalizeDatabase(location):
    DBCon = sqlite3.connect(location)
    cur = DBCon.cursor()
    for tablename in ['shortcut_es', 'es']:
        #    for tablename in ['checked1', 'shortcut', 'origin3']:
        cur.execute("select distinct question from {} ".format(tablename))
        rows = cur.fetchall()
        for row in rows:
            question_n = normalization(row[0])
            sql = """update {} set question_n=\"{}\" where question=\"{}\"""".format(tablename, question_n, row[0])
            try:
                cur.execute(sql)
            except sqlite3.OperationalError as e:
                logging.error("{}:\n{}".format(e, sql))
        logging.info("Finished normalizing {}".format(tablename))
        DBCon.commit()

    cur.close()
    DBCon.commit()
    DBCon.close()


def NormalizeFile(location):
    with open(location, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            print(normalization(line.strip()))


def NormalizeFile_SecondColumn(location):
    with open(location, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                columns = line.strip().split("\t")
                columns[1] = normalization(columns[1])
                print("\t".join(columns))




def  normalization( inputstr):
    temp = re.sub("(https?|ftp)://\S+", " JDHTTP ", inputstr)
    temp = re.sub("\S+@\S+", " JDEMAIL ", temp)
    temp = re.sub("#E-s\d+", " ", temp)
    afterfilter = ""
    for c in temp:
        if c in normalization.dict_fh:
            afterfilter += normalization.dict_fh[c]
            continue
        if c in normalization.signtoremove:
            afterfilter += " "
            continue
        if '😀' <= c <= '🙏' or c == "☹":
            afterfilter += " "
            continue
        afterfilter += c

    return " ".join([x for x in afterfilter.split() if x not in normalization.stopwords])
    # afterreplacestopwords = []
    # for word in afterfilter.split():
    #     if word not in normalization.stopwords:
    #         afterreplacestopwords.append(word)
    #
    # return " ".join(afterreplacestopwords)


def loadlist():

    normalization.fulllength = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｇｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９０：-"
    normalization.halflength = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890:-"
    normalization.dict_fh = {}
    for i in range(len(normalization.fulllength)):
        normalization.dict_fh[normalization.fulllength[i]] = normalization.halflength[i]
    normalization.signtoremove = "！？｡＂＃＄％＆＇（）＊＋，／；＜＝＞＠。［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏" \
                                 + "!\"#$%&\'()*+,/;<=>?@[\\]^_`{|}~"

    normalization.stopwords = set()
    with open(sys.argv[1], encoding="utf-8") as stopwords:
        for stopword in stopwords:
            if stopword.startswith("word,"):
                continue  # opening line
            if "," in stopword:
                word, _ = stopword.split(",")
                normalization.stopwords.add(word.strip())



if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: python3 Normalize_RS.py [databasefilename]")

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info("Start.")

    #NormalizeDatabase(sys.argv[1])
    #NormalizeFile(sys.argv[1])
    loadlist()
    NormalizeFile_SecondColumn(sys.argv[2])

    logging.info("Done")
