import jsonpickle, requests, sys, logging, configparser
import csv, shutil, os.path, filecmp, urllib
from datetime import datetime

fieldnames = [ "question", "tag", "shopid", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]


LexicalAnalyzeURL = "http://localhost:4001/Normalize/"
def NTask(Sentence):
    url = LexicalAnalyzeURL+  urllib.parse.quote(Sentence)
    #logging.debug("Start: " + url)
    ret = requests.get(url)
    return ret.text


def FilterTab(inputstr):
    return inputstr.replace("\t", "    ").replace("\n", "|@@|").replace("\r", "|@@|")


def ProcessRow(row):
    temprow = {}
    for key in row:
        # fields not in fieldnames: 'pos', 'isExpires', 'shopId', 'userPin', 'cid2', 'id', 'ner', 'cid1', 'visiable', 'groupTypeSub', 'assistType', 'expiresRange', 'words', 'professionType', 'confirmed', 'tag', 'questionNormalized', 'groupType', 'updateTime', 'version'
        if key in fieldnames:
            if key == "answer":
                answers = jsonpickle.decode(row[key])
                temprow["answer"] = FilterTab(answers[0]["answer"])  # only get the first answer.

                if temprow["answer"] != answers[0]["answer"]:
                    logging.warning("\tModified answer: {} ".format(answers[0]["answer"]))
            else:
                temprow[key] = FilterTab(row[key])

    temprow["source"] = "2"  # "2" as request from guangtao "silicon_valley"

    if temprow["brand"] == "美的" and temprow["cid3"] == "空调":
        temprow["shopid"] = 1000001452
    elif temprow["brand"] == "西门子" and temprow["cid3"] == "洗衣机":
        temprow["shopid"] = 1000001421
    elif temprow["brand"] == "海尔" and temprow["cid3"] == "洗衣机":
        temprow["shopid"] = 1000001782
    else:
        logging.warning("Unknown brand/cid3:{}".format(row))

    temprow["question"] = NTask(temprow["question"])

    return temprow


def WriteBrandFAQ(data, location):
    ProcessedData = []
    brandlist = set()
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames, delimiter='\t')
        csvwriter.writeheader()
        for row in sorted(data, key=lambda k: (k['updateTime'],k['id'])):
            temprow = ProcessRow(row)
            brandlist.add(temprow["brand"])
            ProcessedData.append(temprow)
            csvwriter.writerow(temprow)

    with open(sys.argv[3], 'r', encoding="utf-8") as whatisfile:
        Data_Read = csv.DictReader(whatisfile, delimiter="\t")
        # rowid = 0
        for row in Data_Read:
            row["source"] = "2"
            #row["question"] = NTask(row["question"])   #don't need this if the file is whatis_n.txt (normalized)
            ProcessedData.append(row)

    basepath = os.path.dirname(location)
    for brand in brandlist:
        with open(os.path.join(basepath, brand + ".txt"), 'w', encoding="utf-8") as csvfile2:
            csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames, delimiter='\t')
            csvwriter.writeheader()
            for row in ProcessedData:
                if row["brand"] == brand:
                    if row["question"] == "":
                        logging.warning("Question is empty for:{}".format(row))
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
    while 1:
        if _scroll_id:
            Link = ESURL + "_search/scroll"
            ScrollData = """{{"scroll": "1m", "scroll_id": "{}"}}""".format(_scroll_id)
            ret = requests.post(Link, ScrollData)

        else:
            Link = ESURL + "sale_exact_content_new/_search?scroll=1m&size=10000"
            ret = requests.post(Link, data=QueryData)
        logging.info("Requested:{}".format(Link))

        alldata = jsonpickle.decode(ret.text)
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
    if len(sys.argv) != 4:
        print(
            "Usage: python3 qa_importfromes.py  [outputfile] [datetimefile] [whatisfile] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    Data, updateinfo = RetrieveFromES()
    with open(sys.argv[2], 'w') as DatetimeFile:
        DatetimeFile.write(updateinfo)

    TempFileLocation = sys.argv[1]+".temp"

    WriteBrandFAQ(Data, TempFileLocation)
    if os.path.isfile(sys.argv[1]) and filecmp.cmp(sys.argv[1], TempFileLocation, shallow=False):
        os.remove(TempFileLocation)
        logging.info("Same file, remove the temp file.")
    else:
        logging.info("Different file, moving to backup.")
        maxnum = 5
        if os.path.isfile("{}.{}".format(sys.argv[1], maxnum)):
            os.remove("{}.{}".format(sys.argv[1], maxnum))
        for i in reversed(range(maxnum)):
            if os.path.isfile("{}.{}".format(sys.argv[1], i)):
                shutil.move("{}.{}".format(sys.argv[1], i), "{}.{}".format(sys.argv[1], i+1))
        if os.path.isfile(sys.argv[1]):
            shutil.move(sys.argv[1], "{}.{}".format(sys.argv[1], 0))
        shutil.move(TempFileLocation, sys.argv[1])

