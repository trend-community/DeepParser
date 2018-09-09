
import os, sys, logging
import sqlite3, re

AnswerList = {}
def LoadAnswerList(filelocation):
    with open(filelocation, 'r', encoding="utf-8") as afile:
        for aline in afile:
            answerid_sentence= aline.split("|", 1)
            if len(answerid_sentence) != 2:
                logging.warning("This line has more | :{}".format(line))
                continue
            answerid1 = answerid_sentence[0].strip()
            sentence1 = answerid_sentence[1].rsplit("|", 1)[0].strip()
            AnswerList[sentence1] = answerid1

def PreProcess():
    cur.execute("CREATE TABLE qapair(q text, a text);")


if __name__ == "__main__":

    if len(sys.argv) != 4 :
        print("Usage: python3 qamatch.py [inputfile] [outputdb] [answerlist] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    LoadAnswerList(sys.argv[3])
    #outfile = open(sys.argv[2], 'w', encoding="utf-8")
    DBCon = sqlite3.connect(sys.argv[2])
    cur = DBCon.cursor()
    PreProcess()
    InsertQuery="insert into qapair(q, a) values(?, ?)"

    with open(sys.argv[1], 'r', encoding="utf-8") as RuleFile:
        Q=""
        A=""
        QList = {}

        for line in RuleFile:
            sentence_type= line.rsplit("|", 1)
            if len(sentence_type) != 2:
                logging.warning("This line has more | :{}".format(line))
                continue
            sentence = sentence_type[0].strip()
            qatype = sentence_type[1].strip()   #qa=1: answer from sales; qa=0:question.
            if qatype == '0':
                    Q = sentence
            elif qatype == '1':
                A = sentence
                #cur.execute(InsertQuery, [Q, A])
                #outfile.write("{}\t{}\n".format(Q, A))
                if A in AnswerList:
                    answerid = AnswerList[A]
                    if answerid not in QList:
                        QList[answerid] = []
                    QList[answerid].append(Q)

                    cur.execute(InsertQuery, [Q, A])

    #outfile.close()

    for answerid in QList:
        with open("{}.txt".format(answerid), "w",  encoding="utf-8") as writer:
            for Q in QList[answerid]:
                writer.write("{}\n".format(Q))
