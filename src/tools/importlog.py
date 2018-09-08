
import os, sys, logging
import sqlite3, re


def InsertSession(OneSession):
    if not hasattr(InsertSession, "SessionID"):
        InsertSession.SessionID = 0
    InsertQuery = "insert into qalog (sessionid, timestamp, sku, userid, sentence) values (?, ?, ?, ?, ?)"
    sku = ""
    InsertSession.SessionID += 1
    for oneline in OneSession.split("\n"):
        skumatch = re.match("\d\d\d\d-\d\d-\d\d-\d\d\t(\d*.*)", oneline)
        if skumatch:
            sku = skumatch.group(1).strip()
        QAmatch = re.match("(\d*)\t(.*?):(.*)", oneline)
        if QAmatch:
            sentence = QAmatch.group(3)
            if not sku:
                skumatch = re.match(" http://item\.jd\.com/(\d*)\.html", sentence)
                if skumatch:
                    sku = skumatch(1).strip()
            if not sku:
                skumatch = re.search("商品编号：(\d*)", sentence)
                if skumatch:
                    sku = skumatch(1).strip()

            if  not sku :
                logging.error("A session without sku: {}".format(OneSession))
            cur.execute(InsertQuery, [InsertSession.SessionID, int(QAmatch.group(1)), sku, QAmatch.group(2), sentence])


def PreProcess():
    cur.execute("create table qalog (ID INTEGER PRIMARY KEY AUTOINCREMENT, sessionid int, timestamp int, sku text, userid text, sentence text, QA int, reference int);")


def PostProcess():
    cur.execute("create index index_sessionid on qalog(sessionid);")
    cur.execute("create index index_userid on qalog(userid);")
    cur.execute("create index index_sentence on qalog(sentence);")
    cur.execute("create table useridlist as select userid, count(*) as work_count from qalog group by userid;")
    cur.execute("update qalog set QA = 0;")
    cur.execute("update qalog set QA = 1 where userid in (select userid from useridlist where work_count>1000);")
    cur.execute("create table sentences as select sentence, QA, count(*) as sentence_count from qalog group by sentence, QA having count(*)>5;")
    cur.execute("")



if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    DBCon = sqlite3.connect("qalog.db")
    cur = DBCon.cursor()
    PreProcess()

    for filename in sys.argv[1:]:
        if not os.path.exists(filename):
            print("Input file " + filename + " does not exist.")
            exit(0)
        logging.info("Start importing {}".format(filename))

        with open(filename, encoding="utf-8") as RuleFile:
            onesession = ""
            for line in RuleFile:
                if line.strip():
                    if line.find("--------------") >= 0:
                        if onesession:
                            InsertSession(onesession)
                            onesession = ""
                    onesession += "\n" + line

            if onesession:
                InsertSession(onesession)

        DBCon.commit()

    PostProcess()

    cur.close()
    DBCon.commit()
    DBCon.close()
    logging.info("Done")