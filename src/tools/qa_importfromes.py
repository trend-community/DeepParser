import jsonpickle, requests, sys, logging, configparser
import csv, shutil, os.path, filecmp
from datetime import datetime

fieldnames = [ "question", "tag", "shopid", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]


def FilterTab(inputstr):
    return inputstr.replace("\t", "    ").replace("\n", "|@@|").replace("\r", "|@@|")


def WriteBrandFAQ(data, location):
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames, delimiter='\t')
        csvwriter.writeheader()
        for row in sorted(data, key=lambda k: (k['updateTime'],k['id'])):
            #fields not in fieldnames: 'pos', 'isExpires', 'shopId', 'userPin', 'cid2', 'id', 'ner', 'cid1', 'visiable', 'groupTypeSub', 'assistType', 'expiresRange', 'words', 'professionType', 'confirmed', 'tag', 'questionNormalized', 'groupType', 'updateTime', 'version'
            temprow = {}
            for key in row:
                if key in fieldnames:
                    if key == "answer":
                        answers = jsonpickle.decode(row[key])
                        temprow["answer"] = FilterTab(answers[0]["answer"]) #only get the first answer.

                        if temprow["answer"] != answers[0]["answer"]:
                            logging.warning("\tModified answer: {} ".format(answers[0]["answer"]))
                    else:
                        temprow[key] = FilterTab(row[key])

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

    updateinfo = "Last entry:{}\n".format(lastentry)
    updateinfo += "LastUpdated(utc):{}\n(local):{}\n(timestamp):{}\n".format(datetime.utcfromtimestamp(lastupdateTime/1000).strftime('%Y-%m-%d %H:%M:%S'),
                                                                   datetime.fromtimestamp(lastupdateTime / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                                                                   lastupdateTime)
    return data, updateinfo



def runSimpleSubprocess(aCommand):
    import subprocess
    sys.stdout.flush()
    sys.stderr.flush()

    p = subprocess.Popen(aCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error_output = p.communicate()
    sys.stdout.flush()
    sys.stderr.flush()
    if p.returncode != 0:
        logging.error('ERROR: command failed with status %d' % p.returncode)
        logging.error('    Command: \n' + aCommand)
        logging.error('    Output: \n' + str(output))
        logging.error('    ErrorOutput: \n' + str(error_output))
        return p.returncode, error_output
    else:
        return p.returncode, output


def DoExtra():
    try:
        Config = configparser.RawConfigParser()
        Config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'importfromes.ini'))
        ExtraCommand = Config.get("main", "extracommand")
        logging.info("Start to execute:\n{}".format(ExtraCommand))
        _, output = runSimpleSubprocess(ExtraCommand)
        logging.info("\tDone. Output:\n{}".format(output))

    except RuntimeError as e:
        logging.error("Failed to read Config: {}".format(e))


def CheckESUpdate(DatetimeFileLocation):
    ESURL = "http://11.3.112.226:9200/"
    QueryData = """{"aggs" : {"max_update":{"max":{"field":"updateTime"}}}}"""

    Link = ESURL + "sale_exact_content_new/_search"
    logging.info("Requesting:{}".format(Link))
    ret = requests.post(Link, data=QueryData)
    aggreinfo = jsonpickle.decode(ret.text)
    maxupdatevalue = aggreinfo["aggregations"]["max_update"]["value"]
    maxupdatevalueasstring = aggreinfo["aggregations"]["max_update"]["value_as_string"]
    logging.info("maxupdatevalue={}, maxupdatevalueasstring={}".format(maxupdatevalue, maxupdatevalueasstring))
    if not os.path.isfile(DatetimeFileLocation):
        return True, maxupdatevalueasstring

    with open(DatetimeFileLocation, 'r') as DatetimeF:
        firstline = DatetimeF.readline()
        _, lastupdatevalue = firstline.split(":", 1)
        if lastupdatevalue.strip() == maxupdatevalueasstring.strip():
            return False, maxupdatevalueasstring
        else:
            return True, maxupdatevalueasstring


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python3 qa_importfromes.py  [outputfile] [datetimefile] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    Updated, MaxUpdateTime =  CheckESUpdate(sys.argv[2])
    if not Updated:
        exit(0)

    Data, updateinfo = RetrieveFromES()
    with open(sys.argv[2], 'w') as DatetimeFile:
        DatetimeFile.write("DBUpdateInfo:{}\n".format(MaxUpdateTime))
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

        DoExtra()

