
import  sys, logging
import sqlite3, jsonpickle, json, re

def PreProcess():
    try:
        cur.execute("""CREATE TABLE alllog ( rowkey text, request_id text, timestamp text, customer_pin text, staff_pin text, plugin_state text,
            recommend_state text, adopt_state text, customer_question text, ai_answers text,
            adopted_answer text, staff_response text, session_id text, qa_pair_id text, 
            position text, additional_info text, dt text, sku text);""")
    except sqlite3.OperationalError:
        logging.warning("Table existed!")
    try:
        cur.execute("""CREATE TABLE answer ( rowkey text, sequenceid int, answer text, optional text,
            pairId text, question text, score float, sourceList text);""")
    except sqlite3.OperationalError:
        logging.warning("Table existed!")


    try:
        cur.execute("""CREATE index loganswer_i on alllog (customer_question, adopted_answer, rowkey);""")
        cur.execute("""CREATE index session_i on alllog (session_id, timestamp, rowkey);""")

        cur.execute("""create index a_i on answer (answer, question, rowkey, sequenceid);""")
        cur.execute("""create index aq_i on answer (question, answer, score, rowkey, sequenceid);""")
        cur.execute("""create index a_id on answer (rowkey, sequenceid, answer, question);""")
    except sqlite3.OperationalError:
        logging.warning("Index existed!")


def StoreAIAnswers(rowkey, text):
    if len(text) < 6:
        return
    text = text[3:-3].replace("   \",", "\",").replace("   \"}", "\"}").replace("   \"}", "\"}").replace("  \"}",
                    "\"}").replace("   \"", "``").replace("哦\",</i>", "哦`,</i>").replace("哦\", \",", "哦`, \",")
    #remove three space+quotes, if there is no comma following.
    ans = text.split("}\",\"{")
    sequenceid = 0
    InsertAIQuery = "insert into answer values("+ ",".join(["?" for _ in range(8)]) + ")"
    for an in ans:
        answer_text = "{" + an + "}"
        try:
            answer = jsonpickle.decode(answer_text)
        except json.decoder.JSONDecodeError as e:
            logging.warning("this answer_text failed to decode: {} in rowkey:{}\nReason:{}".format(answer_text, rowkey, e))
            continue
        #print(answer)
        cur.execute(InsertAIQuery, [rowkey, sequenceid, answer['answer '].strip(), str(answer['optional ']),
                    answer['pairId '].strip() if 'pairId ' in answer else '', answer['question '].strip(),
                    answer['score '], str(answer['sourceList '])
                                  ])
        sequenceid += 1


def StoreAIAnswers_new(rowkey, text):
    sequenceid = 0
    InsertAIQuery = "insert into answer values("+ ",".join(["?" for _ in range(8)]) + ")"
    json_array = json.loads(text)
    #answerlist = jsonpickle.decode(text)
    for answer_text in json_array:
        try:
            answer = jsonpickle.decode(answer_text)
        except json.decoder.JSONDecodeError:
            logging.warning("this answer_text failed to decode: {} in \n{}".format(answer_text, text))
            continue
        #print(answer)
        cur.execute(InsertAIQuery, [rowkey, sequenceid, answer['answer '].strip(), str(answer['optional ']),
                    answer['pairId '].strip() if 'pairId ' in answer else '', answer['question '].strip(),
                    answer['score '], str(answer['sourceList '])
                                  ])
        sequenceid += 1


#log is created from hive -e "select * from fdm.fdm_hbase_crius_c_alpha_sales_alpha_sales_log" > log.txt
if __name__ == "__main__":

    if len(sys.argv) != 3 :
        print("Usage: python3 import.sales.log.py [inputfile] [outputdb]  ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    #outfile = open(sys.argv[2], 'w', encoding="utf-8")
    DBCon = sqlite3.connect(sys.argv[2])
    cur = DBCon.cursor()
    PreProcess()
    InsertQuery="insert into alllog values(" + ",".join(["?" for _ in range(18)]) + ")" #including sku
    print("InsertQuery:\t{}".format(InsertQuery))
    #ai_answerid = 0
    with open(sys.argv[1], 'r', encoding="utf-8") as RuleFile:

        for line in RuleFile:
            columns = line.split("\t")
            columns = [x.strip() for x in columns]
            if len(columns) != 17:
                logging.warning("this line has different tab:{}\n\t{}".format(len(columns), line))
                continue
            if columns[9] != "[]" and len(columns[9]) > 4:
                StoreAIAnswers(columns[0], columns[9])
                columns[9] = ''

            columns.append("")  #sku
            if columns[15] != "{}":  #additional info, contains sku
                addition_info = jsonpickle.decode(columns[15])
                if "sku" in addition_info:
                    columns[17] = addition_info["sku"]

            cur.execute(InsertQuery, columns)
        DBCon.commit()

    cur.execute("delete from answer where rowkey in (select rowkey from alllog where staff_pin like '%test%');")
    cur.execute("delete from alllog where staff_pin like '%test%';")
    cur.close()
    DBCon.commit()
    DBCon.close()

