
from utils import *
import pickle
SentenceCache = {}


def WriteSentenceDB(Sentence, NodeList):
    NodePickle = pickle.dumps(NodeList)
    logging.warning("NodePickle=" + str(NodePickle))
    logging.warning("\tLength:" + str(len(NodePickle)))
    #DBInsertOrUpdate("sentences", "sentence", Sentence, ["result"], [NodePickle])

    cur = DBCon.cursor()
    strsql = "SELECT ID from sentences where sentence=?  limit 1"
    logging.info(strsql)
    logging.info("keyvalue:" + Sentence)
    cur.execute(strsql, (Sentence,))
    resultrecord = cur.fetchone()
    if resultrecord:
        resultid = resultrecord[0]
        try:
            strsql = "update  sentences set result=? , verifytime=DATETIME('now') where ID=?"

            logging.info(strsql)
            cur.execute(strsql, [sqlite3.Binary(NodePickle), resultid])
            resultid = cur.lastrowid
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logging.warning("data writting error. ignore")
            logging.warning(str(e))
            resultid = -1
        DBCon.commit()
    else:
        try:
            strsql = "INSERT into sentences (sentence, result, createtime)" \
                     "values(?, ?, DATETIME('now'))"
            logging.info(strsql)
            cur.execute(strsql, [Sentence, sqlite3.Binary(NodePickle)])
            resultid = cur.lastrowid
            logging.info("Resultid=" + str(resultid))
        except (sqlite3.OperationalError,sqlite3.DatabaseError) as e:
            logging.warning("data writting error. ignore")
            logging.warning(str(e))
            resultid = -1
        DBCon.commit()
    cur.close()
    return resultid


def LoadSentenceDB():
    global SentenceCache
    cur = DBCon.cursor()
    strSQL = "select sentence, result from sentences where result is not null"
    cur.execute(strSQL)
    rows = cur.fetchall()
    for row in rows:
        SentenceCache[row[0]] = pickle.loads(row[1])
        logging.info("Cached:" + str(row[0]))


def WriteWinningRules(Sentence, WinningRules):
    strsql = """INSERT or IGNORE into rulehits (sentenceid, ruleid, createtime, verifytime)
                    VALUES(?, ?, DATETIME('now'), DATETIME('now'))"""
    try:
        SentenceID = DBInsertOrGetID("sentences", ["sentence", ], [Sentence, ])
        cur = DBCon.cursor()

        for ruleid in WinningRules:
            cur.execute(strsql, [SentenceID, ruleid])
        cur.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError)  as e:
        logging.warning("data writting error. ignore.")
        logging.warning("SQL:" + strsql)
        logging.warning("Error:" + str(e))
    DBCon.commit()