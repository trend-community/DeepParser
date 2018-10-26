import jsonpickle, requests, sys, logging
import csv

fieldnames = ["ID", "question", "tag", "shopid", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]

Data = []


def WriteBrandFAQ(location):
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in Data:
            if '\ufeffID' in row:
                del row['\ufeffID']
            if 'AnswerID' in row:
                del row['AnswerID']

            #fields not in fieldnames: 'pos', 'isExpires', 'shopId', 'userPin', 'cid2', 'id', 'ner', 'cid1', 'visiable', 'groupTypeSub', 'assistType', 'expiresRange', 'words', 'professionType', 'confirmed', 'tag', 'questionNormalized', 'groupType', 'updateTime', 'version'
            temprow = {}
            for key in row:
                if key in fieldnames:
                    temprow[key] = row[key]
                if key == "answer":
                    answers = jsonpickle.decode(row[key])
                    temprow[key] = answers[0]["answer"] #only get the first answer.
            csvwriter.writerow(temprow)


def RetrieveFromES():
    ESURL = "http://11.3.112.226:9200/sale_exact_content_new/_search"
    QueryData = """{
            "query": {

            "match" : {
            "source":"2"
            }
            }}"""
    InitailLink = ESURL + "?scroll=1m&size=10000"
    _scroll_id = ""
    hitstotal = 0
    count = 0
    while 1:
        if _scroll_id:
            Link = InitailLink + "&scroll_id=" + _scroll_id
        else:
            Link = InitailLink
        logging.info("Requesting:{}".format(Link))
        ret = requests.post(Link, data=QueryData)
        alldata = jsonpickle.decode(ret.text)
        _scroll_id = alldata["_scroll_id"]
        if "hits" in alldata and alldata["hits"]:
            print(alldata)
            print(alldata["_scroll_id"])
            count += len(alldata["hits"]["hits"])
            if hitstotal == 0:
                hitstotal = alldata["hits"]['total']

            logging.info("Found total {} hits, out of {}".format(count, hitstotal))
            for hit in alldata["hits"]["hits"]:
                Data.append(hit["_source"])

            if count >= hitstotal:
                break
        else:
            break


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    RetrieveFromES()

    WriteBrandFAQ("output.csv")