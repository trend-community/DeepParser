import logging, os, requests, time, sys, sqlite3
import concurrent.futures, jsonpickle, operator
import urllib

def HBTask(sentence1, sentence2):

    link = """{{"inputText":"{}",  "candidateText": "{}"}}""".format(sentence1.replace('"', '%22'), sentence2.replace('"', '%22'))
    link = "http://11.7.151.130:8090/compute?computeInput=" + urllib.parse.quote(link)
    try:
        logging.debug("start:" + link)
        ret = requests.get(link)
        if 100 < ret.status_code < 400:
            result = jsonpickle.decode(ret.text)
            if "candidates" in result:
                candidates = result["candidates"]
                if len(candidates) > 0:
                    similarity = candidates[0]["similarity"]
                    return similarity
            logging.debug("for {}, \n\tret.text={}".format(link, ret.text))
            return -1
        else:
            logging.warning("Error in getting {}. response code: {}".format(link, ret.status_code))
            return -2

    except Exception as e:
        logging.warning("Error in getting {}. response code: {}".format(link, ret.status_code))
        logging.warning(str(e))
        return -3



if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    if len(sys.argv) < 2:
        print("Usage: python3 checkcloseanswer.py [answerfile] [databasefilename] ")
        exit(1)


    DBCon = sqlite3.connect(sys.argv[2])
    cur = DBCon.cursor()
    AQuery = "select distinct answer from brandfaq "
    cur.execute(AQuery)
    rows = cur.fetchall()
    brandanswers = []
    for row in rows:
        brandanswers.append(row[0])
    cur.close()
    DBCon.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        with open(sys.argv[1], 'r', encoding="utf-8") as answerlist:
            for answer in answerlist:
                Result = {}
                future_to_url = {executor.submit(HBTask, answer, brandanswer): brandanswer for brandanswer in brandanswers}
                future_new = {}
                logging.info("There are " + str(len(future_to_url)) + " to process.")
                for future in concurrent.futures.as_completed(future_to_url):
                    s = future_to_url[future]
                    try:
                        Result[s] = future.result()
                    except Exception as exc:
                        logging.debug('%r generated an exception: \n %s' % (s, exc))

                logging.info("Done of retrieving data")

                sortedresult = sorted(Result.items(), key=operator.itemgetter(1), reverse=True)
                print(answer)
                for x in sortedresult[:3]:
                    if x[1]>0.5:
                        print("\t{}-[{}]".format(x[1], x[0]))
                print("-------\n")
