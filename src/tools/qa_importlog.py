
import os, sys, logging
import sqlite3, re


def InsertSession(OneSession):
    if not hasattr(InsertSession, "SessionID"):
        InsertSession.SessionID = 0
    InsertQuery = "insert into qalog (sessionid, timestamp, sku, userid, sentence, sentence_n) values (?, ?, ?, ?, ?, ?)"
    sku = ""
    InsertSession.SessionID += 1
    for oneline in OneSession.split("\n"):
        skumatch = re.match("\d\d\d\d-\d\d-\d\d-\d\d\t(\d*.*)", oneline)
        if skumatch:
            sku = skumatch.group(1).strip()
        QAmatch = re.match("(\d*)\t(.*?):(.*)", oneline)
        if QAmatch:
            sentence = QAmatch.group(3).strip()
            skumatch = re.match(" http://item\.jd\.com/(\d*)\.html", sentence)
            if skumatch:
                sku = skumatch.group(1).strip()
            skumatch = re.search("商品编号：(\d*)", sentence)
            if skumatch:
                sku = skumatch.group(1).strip()

            if  not sku :
                logging.error("A session without sku: {}".format(OneSession))
            cur.execute(InsertQuery, [InsertSession.SessionID, int(QAmatch.group(1)), sku,
                                      QAmatch.group(2).strip(), sentence, normalization(sentence)])


def PreProcess():
    cur.execute("""create table qalog (ID INTEGER PRIMARY KEY AUTOINCREMENT, sessionid int, timestamp int, sku text, 
        userid text, sentence text, QA int, reference int, sentence_n text);""")
    cur.execute("""CREATE TABLE qapair(sessionid int, sku text, q text, a text, qid int, aid int)""")
    cur.execute("""CREATE INDEX a on qapair (a, q);""")
    cur.execute("""CREATE INDEX q on qapair (q, a);""")
    cur.execute("""CREATE INDEX aid on qapair (aid, q);""")
    cur.execute("""CREATE INDEX qid on qapair (qid, a);""")


def PostImportQALogProcess():
    logging.info("PostImportQALogProcess")
    cur.execute("create index index_sessionid on qalog(sessionid, QA);")
    cur.execute("create index index_userid on qalog(userid);")
    cur.execute("create index index_sentence on qalog(sentence_n, sentence);")
    cur.execute("create table useridlist as select userid, count(*) as work_count from qalog group by userid;")
    # TODO: use userlist of the sales representatives to set QA=1.
    cur.execute("update qalog set QA = 0 ")
    useridlike = sys.argv[3]
    condition = " or ".join([" userid like \"" + x + "\"" for x in useridlike.split("/")])
    logging.info("Set Answers: " + "update qalog set QA = 1 where " + condition)
    cur.execute("update qalog set QA = 1 where " + condition)

    # cur.execute("create table sentences (sentenceid integer primary key autoincrement, sentence TEXT, QA INT, sentence_count INT, type int);")
    # cur.execute(" insert into sentences(sentence, QA, sentence_count, type) select sentence_n, QA, count(*) as sentence_count, 3 from qalog group by sentence_n, QA having count(*)>1;")
    # cur.execute(" create unique index sentences_s on sentences(sentence, QA, type);")
    #
    # cur.execute(" update sentences set type=1 where sentence like '【%';")
    # cur.execute(" update sentences set type=2 where sentence like '（%';")


def PostQAPairProcess():
    logging.info("PostQAPairProcess")
    cur.execute("create table sentences (sentenceid integer primary key autoincrement, sentence TEXT, QA INT, sentence_count INT);")
    cur.execute(" insert into sentences(sentence, QA, sentence_count) select q, 0, count(*) as sentence_count from qapair group by q having count(*)>1;")
    cur.execute(" insert into sentences(sentence, QA, sentence_count) select a, 1, count(*) as sentence_count from qapair group by a having count(*)>1;")
    cur.execute(" create unique index sentences_s on sentences(sentence, QA);")
    cur.execute(" update qapair set qid=(select sentenceid from sentences where qapair.q=sentences.sentence and QA=0)")
    cur.execute(" update qapair set aid=(select sentenceid from sentences where qapair.a=sentences.sentence and QA=1)")


def ExportQAFiles():
    logging.info("ExportQAFiles")
    AQuery = "select sentenceid, sentence, sentence_count from sentences where QA = 1 and sentence_count>=10 order by sentence_count desc "

    cur.execute(AQuery)
    rows = cur.fetchall()

    Question_cur = DBCon.cursor()
    QQuery = "select  q from qapair where aid=?"    #not to do "distinct q" in here.

    with open("answerlist.txt", 'w', encoding="utf-8") as answerlist:
        for row in rows:
            answerid = row[0]
            Question_cur.execute(QQuery, [answerid, ])
            questions = Question_cur.fetchall()
            if len(questions) < 10:     #too small amount to output/cluster.
                continue

            answerlist.write("{}\t{}\t{}\n".format(answerid, row[1], row[2]))
            with open("{}.txt".format(answerid), 'a', encoding="utf-8") as foutput:
                for question in questions:
                    foutput.write(question[0]+"\n")

    AQuery = "select sentenceid, sentence, sentence_count from sentences where QA = 0 and sentence_count>=10 order by sentence_count desc "
    cur.execute(AQuery)
    rows = cur.fetchall()
    with open("questionlist.txt", 'w', encoding="utf-8") as questionlist:
        for row in rows:
            questionlist.write("{}\t{}\t{}\n".format(row[0], row[1], row[2]))


def normalization(inputstr):
    if not hasattr( normalization, "fulllength"):
        normalization.fulllength="ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｇｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９０：-"
        normalization.halflength="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890:-"
        normalization.dict_fh = {}
        for i in range(len(normalization.fulllength)):
            normalization.dict_fh[normalization.fulllength[i]] = normalization.halflength[i]
        normalization.signtoremove="！？｡＂＃＄％＆＇（）＊＋，／；＜＝＞＠。［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏" \
                        + "!\"#$%&\'()*+,/;<=>?@[\\]^_`{|}~"

        normalization.stopwordtags={"赞成": "JDSTOPYES", "拒绝":"JDSTOPNO", "无意义":"JDSTOPHELLO", "敏感词": ""}
        normalization.dict_stopwords = {"敏感词": ["亲", "亲亲", "亲爱的", "宝贝", "宝宝"]}
        with open(sys.argv[2], encoding="utf-8") as stopwords:
            for stopword in stopwords:
                if stopword.startswith("word,"):
                    continue    #opening line
                if "," in stopword:
                    word, tag = stopword.split(",")
                    tag = tag.strip()
                    word = word.strip()
                    if tag in normalization.stopwordtags:
                        if tag not in normalization.dict_stopwords:
                            normalization.dict_stopwords[tag] = [word]
                        else:
                            normalization.dict_stopwords[tag].append(word)

    temp = re.sub("(https?|ftp)://\S+", " JDHTTP ", inputstr)
    temp = re.sub("\S+@\S+", " JDHTTP ", temp)
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

    afterreplacestopwords = []
    for word in afterfilter.split():
        replaced = False
        for stopwordtag in normalization.dict_stopwords:
            if word in normalization.dict_stopwords[stopwordtag]:
                afterreplacestopwords.append(normalization.stopwordtags[stopwordtag])
                replaced = True
                break
        if not replaced:
            afterreplacestopwords.append(word)

    return " ".join(afterreplacestopwords)


def QAPairSession(s_id):
    session_cur = DBCon.cursor()
    SessionQuery = """select sku, sentence_n, QA from qalog where sessionid=? order by timestamp"""
    session_cur.execute(SessionQuery, [s_id, ])
    QAWriteQuery = """insert into qapair (sessionid, sku, q, a) values(?, ?, ?, ?)"""
    rows_s = session_cur.fetchall()
    q = ""
    a = ""
    sku = ""
    for row_s in rows_s:
        QA = row_s[2]
        if QA == 0:
            if q and a:     #not empty, write the qa into db
                session_cur.execute(QAWriteQuery, [s_id, sku, q, a])
                q = ""
                a = ""
            if q:
                q += " " + row_s[1]
            else:
                q = row_s[1]
                sku = row_s[0]  #assume the sku in the first q is the right sku

        else:
            if a:
                a += " " + row_s[1]
            else:
                a = row_s[1]

    if q and a:  # not empty, write the qa into db
        session_cur.execute(QAWriteQuery, [s_id, sku, q, a])

    return


def GenerateQA():
    SessionIDQuery = "select distinct sessionid from qalog "

    cur.execute(SessionIDQuery)
    rows = cur.fetchall()
    for row in rows:
        QAPairSession(row[0])


if __name__ == "__main__":
    # x = "this中 文A，B ｃｈｉｎａ。 is , http://abder.dofj.sdf/sjodir/ams in text, this is a@b.c email"
    # print("before:{}\n   after:{}".format(x, normalization(x)))
    # x = "a☹︎b😐"
    # print("before:{}\n   after:{}".format(x, normalization(x)))
    # x = "亲，这款是二级的不是一级吗 是的 嗯 不能噢 "
    # print("before:{}\n   after:{}".format(x, normalization(x)))

    if len(sys.argv) < 4:
        print("Usage: python3 importlog.py [databasefilename] [stopwordlist] [staff_pin_match] [inputfile1] [inputfile2]...")
        print("Example: nohup python3 ../src/qa_importlog.py ../siemens.db ../src/stopwords.csv 博世% ../source/wm*.txt &")
        print("Example: nohup python3 ../src/qa_importlog.py ../haier.db ../src/stopwords.csv haier%/kaifang% ../source/wm*.txt &")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()

    if sys.argv[2] == "qafile":
        logging.info("Generate qafile only")
        ExportQAFiles()

        cur.close()
        DBCon.commit()
        DBCon.close()
        logging.info("Done")
        exit(0)

    PreProcess()

    for filename in sys.argv[4:]:
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

    PostImportQALogProcess()

    GenerateQA()
    PostQAPairProcess()
    ExportQAFiles()

    logging.info("Start closing DB.")
    cur.close()
    DBCon.commit()
    DBCon.close()
    logging.info("Done")

