import os, sys, logging
import sqlite3, re



if __name__ == "__main__":

    if len(sys.argv) != 2 :
        print("Usage: python3 splitquestion.3.py [inputfile1] ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


    with open(sys.argv[1], 'r', encoding="utf-8") as RuleFile:
        lastid = -1
        foutput = None
        for line in RuleFile:
            q_sid = line.rsplit("|", 1)
            if len(q_sid) != 2:
                logging.warning("This line has more | :{}".format(line))
                continue
            sid = q_sid[1].strip()
            q = q_sid[0].strip()
            if lastid != sid:
                if foutput:
                    foutput.close()
                foutput = open("{}.txt".format(sid), 'w', encoding="utf-8")
                lastid = sid
            foutput.write(q + "\n")
        if foutput:
            foutput.close()
