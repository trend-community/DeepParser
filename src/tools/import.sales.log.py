#Log info: https://cf.jd.com/pages/viewpage.action?pageId=138728223
import  sys, logging
import sqlite3, jsonpickle, json
"""
#!/bin/sh
#getlog.sh
set -x

hive -e "select * from fdm.fdm_hbase_crius_c_alpha_sales_log_alpha_sales_event_tracking_log where dt='$1'" > alllog.$1.log
hive -e "select * from fdm.fdm_hbase_crius_c_alpha_sales_answer_alpha_sales_info_log where dt='$1'" > extrainfo.$1.log

python3 import.sales.log.py alllog.$1.log extrainfo.$1.log log.$1.db


"""
def PreProcess():
    try:
        cur.execute("""CREATE TABLE alllog ( pair_id text, pair_id2 text, sid text, ts text, staff text, customer text, 
            question text, adopted text, response text, r_state text, a_state text,
            position text, plugin_state text, sku_id text, brand text, cate text, 
            shop_id text, intent_1 text, intent_2 text, confidence text, source text,
            is_presale text, answer_top_1 text, test_flag text, log_type text, create_date text,
            dt text);""")
    except sqlite3.OperationalError:
        logging.warning("Table existed!")
    try:
        cur.execute("""CREATE TABLE answer ( pair_id text, pair_id2 text,sequenceid int, sid int, question text, answer text, sourcelist text,
             score float, confidencescore float, optional text, xgboostscore float, sku text,
             ai_question text, additional_info text, create_date text, dt text);""")
    except sqlite3.OperationalError:
        logging.warning("Table existed!")


    try:
        cur.execute("""CREATE index loganswer_i on alllog (question, adopted, sid);""")
        cur.execute("""CREATE index session_i on alllog (sid, ts, pair_id);""")
        cur.execute("""CREATE unique index pairid on alllog(pair_id, ts, question)""")

        cur.execute("""CREATE unique index a_pairid on answer(pair_id, sequenceid, question) """)
        cur.execute("""create index a_i on answer (answer, question, pair_id, sid);""")
        cur.execute("""create index aq_i on answer (question, answer, score, pair_id, sid);""")
        cur.execute("""create index a_id on answer (pair_id, sid, answer, question);""")
    except sqlite3.OperationalError:
        logging.warning("Index existed!")


def StoreAIAnswers(row):

    if len(row[4]) < 6:
        return
    answertext = row[4][3:-3].replace("   \",", "\",").replace("   \"}", "\"}").replace("   \"}", "\"}").replace("  \"}",
                    "\"}").replace("   \"", "``").replace("哦\",</i>", "哦`,</i>").replace("哦\", \",", "哦`, \",")
    #remove three space+quotes, if there is no comma following.
    ans = answertext.split("}\",\"{")

    InsertAIQuery = "insert or ignore into answer values("+ ",".join(["?" for _ in range(16)]) + ")"
    sequenceid = 0
    for an in ans:
        answer_text = "{" + an + "}"
        try:
            answer = jsonpickle.decode(answer_text)
        except json.decoder.JSONDecodeError as e:
            logging.warning("this answer_text failed to decode: {} in row:{}\nReason:{}".format(answer_text, str(row), e))
            continue
        #print(answer)
        try:
            cur.execute(InsertAIQuery, [row[0], row[1], sequenceid, row[2], row[3], answer['answer '].strip(), str(answer['sourceList ']),
                    answer['score '], answer['confidenceScore '], str(answer['optional ']),
                    answer['xgboostScore '], answer['sku '].strip() if 'sku ' in answer else '',
                    answer['question '], row[5], row[6], row[7]
                                  ])
        except (RuntimeError,KeyError) as e:
            logging.error(e)
            logging.error("\tanswer_text: " + answer_text)
            logging.error("\tline:" + str(row))
        sequenceid += 1


#log is created from hive -e "select * from fdm.fdm_hbase_crius_c_alpha_sales_alpha_sales_log" > log.txt
if __name__ == "__main__":

    if len(sys.argv) != 4 :
        print("Usage: python3 import.sales.log.py [inputfile_log] [inputfile_aianswer] [outputdb]  ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    #outfile = open(sys.argv[2], 'w', encoding="utf-8")
    DBCon = sqlite3.connect(sys.argv[3])
    cur = DBCon.cursor()
    PreProcess()
    InsertQuery="insert or ignore into alllog values(" + ",".join(["?" for _ in range(27)]) + ")" #including sku
    print("InsertQuery:\t{}".format(InsertQuery))
    #ai_answerid = 0
    with open(sys.argv[1], 'r', encoding="utf-8") as RuleFile:
        for line in RuleFile:
            columns = line.split("\t")
            columns = [x.strip() for x in columns]
            if len(columns) != 27:
                logging.warning("this line has different tab:{}\n\t{}".format(len(columns), line))
                continue
            # if columns[9] != "[]" and len(columns[9]) > 4:
            #     StoreAIAnswers(columns[0], columns[9])
            #     columns[9] = ''
            #
            # columns.append("")  #sku
            # if columns[15] != "{}":  #additional info, contains sku
            #     addition_info = jsonpickle.decode(columns[15])
            #     if "sku" in addition_info:
            #         columns[17] = addition_info["sku"]

            cur.execute(InsertQuery, columns)
        DBCon.commit()

    logging.info("Done with {}. Start importing from {}".format(sys.argv[1], sys.argv[2]))
    with open(sys.argv[2], 'r', encoding="utf-8") as RuleFile:
        for line in RuleFile:
            columns = line.split("\t")
            columns = [x.strip() for x in columns]
            if len(columns) != 8:
                logging.warning("this line has different tab:{}\n\t{}".format(len(columns), line))
                continue
            StoreAIAnswers(columns)
        DBCon.commit()

#    cur.execute("delete from answer where rowkey in (select rowkey from alllog where staff_pin like '%test%');")
#    cur.execute("delete from alllog where staff_pin like '%test%';")
    cur.close()
    DBCon.commit()
    DBCon.close()

