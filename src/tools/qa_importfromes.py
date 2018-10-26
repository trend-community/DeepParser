import jsonpickle, requests, sys, logging
import csv
from datetime import datetime

fieldnames = [ "question", "tag", "shopid", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]


def WriteBrandFAQ(data, location):
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in data:
            #fields not in fieldnames: 'pos', 'isExpires', 'shopId', 'userPin', 'cid2', 'id', 'ner', 'cid1', 'visiable', 'groupTypeSub', 'assistType', 'expiresRange', 'words', 'professionType', 'confirmed', 'tag', 'questionNormalized', 'groupType', 'updateTime', 'version'
            temprow = {}
            for key in row:
                if key in fieldnames:
                    temprow[key] = row[key]
                    if key == "answer":
                        answers = jsonpickle.decode(row[key])
                        temprow[key] = answers[0]["answer"] #only get the first answer.
            temprow["source"] = "silicon_valley"

            if row["confirmed"] != "yes" and row["isExpires"] != "0":
                logging.warning("This entry is NOT confirmed: {}".format(row))
                continue
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
    data = []
    while 1:
        if _scroll_id:
            Link = ESURL + "_search/scroll?scroll=1m&scroll_id=" + _scroll_id
            ret = requests.post(Link)
            #ScrollData = """{{"scroll": "1m", "scroll_id": "{}"}}""".format(_scroll_id)
        else:
            Link = ESURL + "sale_exact_content_new/_search?scroll=1m&size=10000"
            ret = requests.post(Link, data=QueryData)
        logging.info("Requesting:{}".format(Link))

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
                if hit["_source"]["updateTime"] > lastupdateTime:
                    lastupdateTime = hit["_source"]["updateTime"]
                data.append(hit["_source"])

            if count >= hitstotal:
                break
        else:
            break

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


    WriteBrandFAQ(Data, sys.argv[1])
