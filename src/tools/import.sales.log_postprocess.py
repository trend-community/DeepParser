
import  sys, logging
import sqlite3, jsonpickle, json, re


def FetchSession(s_id):
    session_cur = DBCon.cursor()
    SessionQuery = """select  datetime(timestamp/1000, 'unixepoch', 'localtime') , customer_question, staff_response, 
            adopted_answer, sku, recommend_state
                    from alllog where session_id=?  order by timestamp"""
    session_cur.execute(SessionQuery, [s_id, ])
    rows_s = session_cur.fetchall()
    output = ""
    currentsku = ""
    for row_s in rows_s:
        if row_s[4] != "":
            currentsku = row_s[4]
        if row_s[5] == "-1":    #recommend_state
            continue
        output += "\t".join([row_s[0], row_s[1], row_s[2], row_s[3], currentsku]) + "\n"

    return output


#log is created from hive -e "select * from fdm.fdm_hbase_crius_c_alpha_sales_alpha_sales_log" > log.txt
if __name__ == "__main__":

    if len(sys.argv) != 2 :
        print("Usage: python3 import.sales.log.py [inputdb]  ")
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    #outfile = open(sys.argv[2], 'w', encoding="utf-8")
    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()

    SessionIDQuery = "select distinct session_id from alllog where staff_pin like ?"

    staff_pins = ["博世", "kaifang", "haier", "美的"]

    for staff_pin in staff_pins:
        with open("{}.log".format(staff_pin), 'w', encoding="utf-8") as OutputFile:

            cur.execute(SessionIDQuery, ["{}%".format(staff_pin), ])
            rows = cur.fetchall()
            for row in rows:
                session_id = row[0]
                OutputFile.write("\n--------{}\n".format(session_id))
                OutputFile.write(FetchSession(session_id))

    cur.close()
    DBCon.close()

