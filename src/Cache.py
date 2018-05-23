
from utils import *
import utils
import pickle
SentenceCache = {}
# LogicalMatchCache = {}

# def WriteSentenceDB(Sentence, NodeList):
#     WriteSentenceDB_Async(Sentence, NodeList)
#     t = Thread( target=WriteSentenceDB_Async, args=(Sentence, NodePickle))
#     t.start()


def WriteSentenceDB(Sentence, NodeList):
    NodePickle = pickle.dumps(NodeList)
    try:
        DBConnection = InitDB_T()
        cur = DBConnection.cursor()
        strsql = "replace into sentences (sentence, result, createtime)" \
                 "values(?, ?, DATETIME('now'))"
        cur.execute(strsql, [Sentence, sqlite3.Binary(NodePickle)])
        cur.close()
        CloseDB(DBConnection)
    except (sqlite3.OperationalError,sqlite3.DatabaseError) as e:
        logging.warning("WriteSentenceDB error. ignore")
        logging.warning(str(e))

    return


def LoadSentenceDB():
    global SentenceCache
    if ParserConfig.get("main", "runtype").lower() == "debug":
        return  #don't load when it is in debug mode.
    try:
        cur = utils.DBCon.cursor()
        strSQL = "select sentence, result from sentences where result is not null " \
                 "order by createtime desc limit " + str(maxcachesize)
        cur.execute(strSQL)
        rows = cur.fetchall()

        for row in rows:
            SentenceCache[row[0]] = pickle.loads(row[1])
        logging.info("SentenceCache size:" + str(len(SentenceCache)))
    except (sqlite3.OperationalError,sqlite3.DatabaseError) as e:
                logging.warning("LoadSentenceDB error. ignore")
                logging.warning(str(e))


def WriteWinningRules_Async(Sentence, WinningRules):
    strsql = """INSERT or IGNORE into rulehits (sentenceid, ruleid, createtime, verifytime)
                    VALUES(?, ?, DATETIME('now'), DATETIME('now'))"""
    try:
        DBConnection = InitDB_T()
        cur = DBConnection.cursor()
        strsql_id = "SELECT ID from sentences where sentence=?  limit 1"
        cur.execute(strsql_id, (Sentence,))

        resultrecord = cur.fetchone()
        if resultrecord:
            SentenceID = resultrecord[0]

            for ruleid in WinningRules:
                cur.execute(strsql, [SentenceID, ruleid])
        cur.close()
        CloseDB(DBConnection)

    except (sqlite3.OperationalError, sqlite3.DatabaseError)  as e:
        logging.warning("WriteWinningRules error. ignore.")
        logging.warning("SQL:" + strsql)
        logging.warning("Error:" + str(e))


def InitDB_T():   #thread-safe
    try:
        tempDB = sqlite3.connect('../data/parser.db')
        cur = tempDB.cursor()
        cur.execute("PRAGMA read_uncommitted = true;")
        #cur.execute("PRAGMA synchronous=OFF;")
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA TEMP_STORE=MEMORY;")  # reference: https://www.sqlite.org/wal.html
        cur.close()
        tempDB.commit()
        return tempDB
        #atexit.register(utils.CloseDB, (tempDB,))
    except sqlite3.OperationalError:
        logging.error("Database file does not exists!")

    return None

# def CheckLogitMatchCache(strtokenlist, i, rule):
#     start = strtokenlist.get(i)
#     for ruletoken in rule.Tokens:
#         if ruletoken.SubtreePointer:
#             return False    # we don't deal with SubtreePointer in this cache
#         if (start.signature, ruletoken.word) in LogicalMatchCache:
#             return True
#         start = start.next
#     return False
