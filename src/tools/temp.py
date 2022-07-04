import sys, os, logging
import sqlite3


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python3 temp.py  [inputfile] [dbfile] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()
    Query = "insert into s_cat(sentence, cat) values(?, ?)"
    with open(sys.argv[2], encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                sentence, category = line.split("\t", 1)
                cur.execute(Query, (sentence.strip(), category.strip()))

    DBCon.commit()
    DBCon.close()
    #
    # writer = open (sys.argv[2], "w", encoding="utf-8")
    #
    # with open(sys.argv[1], encoding="utf-8") as RuleFile:
    #     freader = csv.reader(RuleFile)
    #     for row in freader:
    #         if row[0] and row[1] and row[2]:
    #             onekey = row[0].strip()
    #             oneq = row[1].strip()
    #             onesku = row[2].strip()
    #         elif row[3]:
    #             writer.write("{}\t{}\t{}\t{}\n".format(onekey, oneq, row[3].strip(), onesku))
    #
    # writer.close()
    #


