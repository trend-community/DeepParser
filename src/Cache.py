
from utils import *
SentenceCache = {}

def WriteSentenceDB(Sentence, NodeList):
    try:
        SentenceID = DBInsertOrGetID("sentences", ["sentence", ], [Sentence, ])
        cur = DBCon.cursor()

        for ruleid in ResultWinningRules:
            cur.execute(strsql, [SentenceID, ruleid])
        cur.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError)  as e:
        logging.warning("data writting error. ignore.")
        logging.warning("SQL:" + strsql)
        logging.warning("Error:" + str(e))
    DBCon.commit()


def LoadSentenceDB():
    global SentenceCache
