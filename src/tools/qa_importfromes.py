import jsonpickle, requests, sys, logging, re
import csv, shutil, os.path, filecmp, urllib
from datetime import datetime

fieldnames = ["id", "question", "tag", "shopId", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source", "uuid"]


# LexicalAnalyzeURL = "http://localhost:4001/Normalize/"
# def NTask(Sentence):
#     url = LexicalAnalyzeURL+  urllib.parse.quote(Sentence)
#     #logging.debug("Start: " + url)
#     ret = requests.get(url)
#     return ret.text

from functools import lru_cache
@lru_cache(maxsize=100000)
def  normalization( inputstr):
    if not hasattr(normalization, "fulllength"):
        loadlist()
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


@lru_cache(maxsize=100000)
def FilterTab(inputstr):
    return inputstr.replace("\t", "    ").replace("\n", "|@@|").replace("\r", "|@@|")


def ProcessRow(row):
    temprow = {}
    # for key in row:
    #     # fields not in fieldnames: 'pos', 'isExpires', 'shopId', 'userPin', 'cid2', 'id', 'ner', 'cid1', 'visiable', 'groupTypeSub', 'assistType', 'expiresRange', 'words', 'professionType', 'confirmed', 'tag', 'questionNormalized', 'groupType', 'updateTime', 'version'
    #     if key in fieldnames:
    #         if key == "answer":
    #             answers = jsonpickle.decode(row[key])
    #             temprow["answer"] = FilterTab(answers[0]["answer"])  # only get the first answer.
    #
    #             if temprow["answer"] != answers[0]["answer"]:
    #                 logging.warning("\tModified answer: {} ".format(answers[0]["answer"]))
    #         else:
    #             temprow[key] = FilterTab(row[key])

    for key in fieldnames:
        if key == "answer":

            answers = jsonpickle.decode(row[key])
            temprow["answer"] = FilterTab(answers[0]["answer"])  # only get the first answer.
            temprow["uuid"] = answers[0]["uuid"]

        else:
            if key in row:
                temprow[key] = row[key]

    #temprow["source"] = "2"  # "2" as request from guangtao "silicon_valley"

    # if temprow["brand"] == "美的" and temprow["cid3"] == "空调":
    #     temprow["shopid"] = 1000001452
    # elif temprow["brand"] == "西门子" and temprow["cid3"] == "洗衣机":
    #     temprow["shopid"] = 1000001421
    # elif temprow["brand"] == "海尔" and temprow["cid3"] == "洗衣机":
    #     temprow["shopid"] = 1000001782
    # else:
    #     logging.warning("Unknown brand/cid3:{}".format(row))

    temprow["question"] = normalization(FilterTab(temprow["question"]))

    return temprow


def WriteFAQ(data, location):
    processeddata = []
    brandset = set()
    logging.info("Start writing " + location)
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames, delimiter='\t')
        csvwriter.writeheader()
        for row in sorted(data, key=lambda k: (k['updateTime'],k['id'])):
            temprow = ProcessRow(row)
            brandset.add(temprow["brand"])
            processeddata.append(temprow)
            if temprow["question"] == "":
                logging.debug("Question is empty for:{}".format(row))
            csvwriter.writerow(temprow)

    logging.info(" Completed writing {}, Start loading {} ".format(location, sys.argv[4]))

    return processeddata, brandset


def WriteBrandFAQ(data, brandlist, location):
    with open(sys.argv[4], 'r', encoding="utf-8") as whatisfile:
        Data_Read = csv.DictReader(whatisfile, delimiter="\t")
        # rowid = 0
        for row in Data_Read:
            row["source"] = "2"
            #row["question"] = NTask(row["question"])   #don't need this if the file is whatis_n.txt (normalized)
            data.append(row)

    logging.info(" Complete loading " + sys.argv[4])
    basepath = os.path.dirname(location)
    for brand in brandlist:
        brand_output_file = os.path.join(basepath, brand + ".txt")
        with open(brand_output_file, 'w', encoding="utf-8") as csvfile2:
            csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames, delimiter='\t')
            csvwriter.writeheader()
            for row in data:
                if row["brand"] == brand:
                    if row["question"] == "":
                        logging.debug("Question is empty for:{}".format(row))
                    else:

                        csvwriter.writerow(row)


def RetrieveFromES():
    ESURL = "http://11.3.112.226:9200/"
    QueryData = """{
                    "query": {
                        "match" : {
                        "source":"2"
                        }
                    } }"""
    _scroll_id = ""
    hitstotal = 0
    count = 0
    lastupdateTime = 0
    lastentry = ""
    data = []
    logging.info("Start RetrieveFromES {}".format(ESURL))
    while 1:
        if _scroll_id:
            Link = ESURL + "_search/scroll"
            ScrollData = """{{"scroll": "1m", "scroll_id": "{}"}}""".format(_scroll_id)
            ret = requests.post(Link, ScrollData)

        else:
            Link = ESURL + "sale_exact_content_new/_search?scroll=1m&size=10000"
            ret = requests.post(Link, data=QueryData)
        logging.info("Received:{}".format(Link))

        alldata = jsonpickle.decode(ret.text)
        logging.info("Decoded")
        if "_scroll_id" in alldata:
            _scroll_id = alldata["_scroll_id"]
        if "hits" in alldata and alldata["hits"]:
            #print("Scroll ID:{}".format(alldata["_scroll_id"]))
            count += len(alldata["hits"]["hits"])
            if hitstotal == 0:
                hitstotal = alldata["hits"]['total']

            logging.info("Found total {} hits, out of {}".format(count, hitstotal))
            for hit in alldata["hits"]["hits"]:
                row = hit["_source"]
                if row["confirmed"] != "yes" and row["isExpires"] != "0":
                    logging.warning("This entry is NOT confirmed or expired: {}".format(row))
                    continue
                if row["updateTime"] > lastupdateTime:
                    lastupdateTime = row["updateTime"]
                    lastentry = str(row)
                data.append(row)

            if count >= hitstotal:
                break
        else:
            break

    updateinfo1 = "Last entry:{}\n".format(lastentry)
    updateinfo1 += "LastUpdated(utc):{}\n(local):{}\n(timestamp):{}\n".format(datetime.utcfromtimestamp(lastupdateTime/1000).strftime('%Y-%m-%d %H:%M:%S'),
                                                                   datetime.fromtimestamp(lastupdateTime / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                                                                   lastupdateTime)
    return data, updateinfo1


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Usage: python3 qa_importfromes.py [stopwords] [outputfile] [datetimefile] [whatisfile] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    Data, updateinfo = RetrieveFromES()
    with open(sys.argv[3], 'w') as DatetimeFile:
        DatetimeFile.write(updateinfo)

    ESFileLocation = sys.argv[2]
    TempFileLocation = ESFileLocation+".temp"

    processed, b_list = WriteFAQ(Data, TempFileLocation)
    if os.path.isfile(ESFileLocation) and filecmp.cmp(ESFileLocation, TempFileLocation, shallow=False):
        os.remove(TempFileLocation)
        logging.info("Same file, remove the temp file.")
    else:
        logging.info("Different file, write brands and moving to backup.")
        WriteBrandFAQ(processed, b_list, ESFileLocation)

        maxnum = 15
        if os.path.isfile("{}.{}".format(ESFileLocation, maxnum)):
            os.remove("{}.{}".format(ESFileLocation, maxnum))
        for ii in reversed(range(maxnum)):
            if os.path.isfile("{}.{}".format(ESFileLocation, ii)):
                shutil.move("{}.{}".format(ESFileLocation, ii), "{}.{}".format(ESFileLocation, ii+1))
        if os.path.isfile(ESFileLocation):
            shutil.move(ESFileLocation, "{}.{}".format(ESFileLocation, 0))
        shutil.move(TempFileLocation, ESFileLocation)

    logging.info("Done.")