
import os, sys, logging
import sqlite3, re

def PreProcess():
    cur.execute("CREATE TABLE qapair(sku text, q text, a text);")


#the input file is created as:
# sqlite3 -separator $'\t' midea.db "select sku, sentence, QA from qalog order by sessionid, timestamp" >midea.qalog.txt

if __name__ == "__main__":

    if len(sys.argv) != 3 :
        print("Usage: python3 qamatch.py [inputfile] [outputdb]  ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    #outfile = open(sys.argv[2], 'w', encoding="utf-8")
    DBCon = sqlite3.connect(sys.argv[2])
    cur = DBCon.cursor()
    PreProcess()
    InsertQuery="insert into qapair(sku, q, a) values(?, ?, ?)"

    with open(sys.argv[1], 'r', encoding="utf-8") as RuleFile:
        Q=""
        A=""

        for line in RuleFile:
            sentence_type= line.rsplit("\t", 2)
            if len(sentence_type) != 3:
                logging.warning("This line has no | :{}".format(line))
                continue
            sku = sentence_type[0].replace("\t", ",").strip()
            sentence = sentence_type[1].strip()
            qatype = sentence_type[2].strip()   #qa=1: answer from sales; qa=0:question.
            if qatype == '0':
                    Q = sentence
            elif qatype == '1':
                A = sentence
                #cur.execute(InsertQuery, [Q, A])
                #outfile.write("{}\t{}\n".format(Q, A))

                cur.execute(InsertQuery, [sku, Q, A])

    #outfile.close
    cur.close()
    DBCon.commit()
    DBCon.close()


