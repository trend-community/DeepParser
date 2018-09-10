
import sys, logging
import sqlite3

AnswerList = {}
def LoadDB():
    cur.execute("select answerid, cluster, tcount, dcount from answercluster")
    rows = cur.fetchall()
    for row in rows:
        info = {"answerid":row[0], "cluster":row[1], "tcount": row[2], "dcount": row[3]}
        AnswerList[info["answerid"]] = info


if __name__ == "__main__":

    if len(sys.argv) != 2 :
        print("Usage: python3 qa_tfdf.py [dbfile]  ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()
    LoadDB()
    UpdateQuery="update answercluster set tf=?, df=? where answerid=?"

    tcluster = {}
    dcluster = {}
    for answerid in AnswerList:
        answerinfo = AnswerList[answerid]
        if answerinfo["cluster"] in tcluster:
            tcluster[answerinfo["cluster"]] += answerinfo["tcount"]
        else:
            tcluster[answerinfo["cluster"]] = answerinfo["tcount"]
        if answerinfo["cluster"] in dcluster:
            dcluster[answerinfo["cluster"]] += answerinfo["dcount"]
        else:
            dcluster[answerinfo["cluster"]] = answerinfo["dcount"]

    for answerid in AnswerList:
        answerinfo = AnswerList[answerid]
        cur.execute(UpdateQuery, [answerinfo["tcount"]/tcluster[answerinfo["cluster"]],
                                  answerinfo["dcount"]/dcluster[answerinfo["cluster"]], answerid])

    #outfile.close
    cur.close()
    DBCon.commit()
    DBCon.close()

