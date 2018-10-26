import jsonpickle, requests, sys, logging
import csv, shutil, os.path, filecmp
from datetime import datetime

fieldnames = [ "question", "tag", "shopid", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]


def WriteBrandFAQ(data, location):
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in sorted(data, key=lambda k: (k['updateTime'],k['id'])):
            #fields not in fieldnames: 'pos', 'isExpires', 'shopId', 'userPin', 'cid2', 'id', 'ner', 'cid1', 'visiable', 'groupTypeSub', 'assistType', 'expiresRange', 'words', 'professionType', 'confirmed', 'tag', 'questionNormalized', 'groupType', 'updateTime', 'version'
            temprow = {}
            for key in row:
                if key in fieldnames:
                    temprow[key] = row[key]
                    if key == "answer":
                        answers = jsonpickle.decode(row[key])
                        temprow[key] = answers[0]["answer"] #only get the first answer.
            temprow["source"] = "silicon_valley"

            if temprow["brand"] == "美的" and temprow["cid3"] == "空调":
                temprow["shopid"] = 1000001452
            elif temprow["brand"] == "西门子" and temprow["cid3"] == "洗衣机":
                temprow["shopid"] = 1000001421
            elif temprow["brand"] == "海尔" and temprow["cid3"] == "洗衣机":
                temprow["shopid"] = 1000001782
            else:
                logging.warning("Unknown brand/cid3:{}".format(row))
            csvwriter.writerow(temprow)


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

    print("Last entry:{}\n".format(lastentry))
    print("LastUpdated(utc):{}\n(local):{}\n(timestamp):{}".format(datetime.utcfromtimestamp(lastupdateTime/1000).strftime('%Y-%m-%d %H:%M:%S'),
                                                                   datetime.fromtimestamp(lastupdateTime / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                                                                   lastupdateTime))
    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 qa_importfromes.py  [outputfile] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    Data = RetrieveFromES()

    BackupFileLocation = sys.argv[1]+".temp"
    if os.path.isfile(sys.argv[1]):
        shutil.move(sys.argv[1], BackupFileLocation)

    WriteBrandFAQ(Data, sys.argv[1])
    if os.path.isfile(sys.argv[1]):
        if filecmp.cmp(sys.argv[1], BackupFileLocation, shallow=False):
            os.remove(BackupFileLocation)
            logging.info("Same file, nothing to do.")
        else:
            logging.info("Different file, moving to backup.")
            maxnum = 5
            currentfile = "{}.{}".format(sys.argv[1], maxnum)
            if os.path.isfile(currentfile):
                os.remove(currentfile)
            for i in reversed(range(maxnum)):
                if os.path.isfile("{}.{}".format(sys.argv[1], i)):
                    shutil.move("{}.{}".format(sys.argv[1], i), "{}.{}".format(sys.argv[1], i+1))
            shutil.move(BackupFileLocation, "{}.{}".format(sys.argv[1], 0))

