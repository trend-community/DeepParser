
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
            sentence = QAmatch.group(3).strip()
            if not sku:
                skumatch = re.match(" http://item\.jd\.com/(\d*)\.html", sentence)
                if skumatch:
                    sku = skumatch.group(1).strip()
            if not sku:
                skumatch = re.search("商品编号：(\d*)", sentence)
                if skumatch:
                    sku = skumatch.group(1).strip()

            if  not sku :
                logging.error("A session without sku: {}".format(OneSession))
            cur.execute(InsertQuery, [InsertSession.SessionID, int(QAmatch.group(1)), sku, QAmatch.group(2).strip(), sentence])


def PreProcess():
    cur.execute("create table qalog (ID INTEGER PRIMARY KEY AUTOINCREMENT, sessionid int, timestamp int, sku text, userid text, sentence text, QA int, reference int);")


def PostProcess():
    cur.execute("create index index_sessionid on qalog(sessionid);")
    cur.execute("create index index_userid on qalog(userid);")
    cur.execute("create index index_sentence on qalog(sentence);")
    cur.execute("create table useridlist as select userid, count(*) as work_count from qalog group by userid;")
    # TODO: use userlist of the sales representatives to set QA=1.
    # cur.execute("update qalog set QA = 0 ")
    # cur.execute("update qalog set QA = 1 where userid in (select userid from useridlist where work_count>500);")
    #
    # cur.execute("create table sentences (sentenceid integer primary key autoincrement, sentence TEXT, QA INT, sentence_count INT, type int);")
    # cur.execute(" insert into sentences(sentence, QA, sentence_count, type) select sentence, QA, count(*) as sentence_count, 3 from qalog group by sentence, QA having count(*)>10;")
    # cur.execute(" create unique index sentences_s on sentences(sentence, QA, type);")
    #
    # cur.execute(" update sentences set type=1 where sentence like '【%';")
    # cur.execute(" update sentences set type=2 where sentence like '（%';")
    # # cur.execute("""delete from sentences where sentenceid in (select qalog.sentenceid from sentences as qalog
    # #                 join sentences on length(qalog.sentence)>length(sentences.sentence) and length(qalog.sentence)<length(sentences.sentence)+5
    # #                     and instr(qalog.sentence, sentences.sentence)>0
    # #                     and sentences.type in (1, 2) );""")
    #
    # cur.execute("create table closesentence(qalogid int, qasentence text, sentenceid int, type int);")
    # # cur.execute("""insert into closesentence (qalogid, qasentence, sentenceid, type)
    # #                 select qalog.id, qalog.sentence, sentences.sentenceid, 0 from qalog
    # #                 join sentences on qalog.sentence=sentences.sentence and sentences.type in (1, 2);
    # # """)
    # cur.execute(""" insert into closesentence (qalogid, qasentence, sentenceid, type)
    #                 select qalog.id, qalog.sentence, sentences.sentenceid, sentences.type from qalog
    #                 join sentences on qalog.sentence = sentences.sentence and qalog.QA<>0 and sentences.QA<>0  ;""")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python3 importlog.py [databasefilename] [inputfile1] [inputfile2]...")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()
    PreProcess()

    for filename in sys.argv[2:]:
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