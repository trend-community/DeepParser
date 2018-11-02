import argparse, logging, os, sys
import requests, urllib, sqlite3


LexicalAnalyzeURL = "http://localhost:4001/Normalize/"

def NTask(Sentence):
    url = LexicalAnalyzeURL+  urllib.parse.quote(Sentence)
    #logging.debug("Start: " + url)
    ret = requests.get(url)
    return ret.text


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 Normalize_RS.py [databasefilename]")

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()
    for tablename in ['shortcut', 'shortcut_es', 'checked_es', 'origin_es', 'origin', 'es']:
        cur.execute("select distinct question from {} ".format(tablename))
        rows = cur.fetchall()
        for row in rows:
            question_n = NTask(row[0])
            cur.execute("update {} set question_n='{}' where question='{}'".format(tablename, question_n, row[0]))
        logging.info("Finished normalizing {}".format(tablename))
        DBCon.commit()

    cur.close()
    DBCon.commit()
    DBCon.close()
    logging.info("Done")
