
import os, sys, logging
import sqlite3, re, operator


def RetrieveTopCharFromFiles(charnum):
    chardict = {}
    for filename in sys.argv[2:]:
        if not os.path.exists(filename):
            print("Input file " + filename + " does not exist.")
            exit(0)
        logging.info("Start importing {}".format(filename))

        with open(filename, encoding="utf-8") as RuleFile:

            for line in RuleFile:
                for x in line:
                    if x in chardict:
                        chardict[x] += 1
                    else:
                        chardict[x] = 1

    charlist = sorted(chardict, key=chardict.get, reverse=True)
    return charlist[:charnum]


def UpdateSentencesDB(filters):
    DBCon = sqlite3.connect(sys.argv[1])
    cur = DBCon.cursor()

    #DBCon.commit()
    UpdateQuery = "update sentences set s_filtered=? where sentenceid=?"
    cur.execute("select sentenceid, sentence from sentences")
    rows = cur.fetchall()
    for row in rows:
        sentenceid = int(row[0])
        sentence = row[1]
        sentence_filtered = ''.join([c for c in sentence if c not in filters])
        cur.execute(UpdateQuery, [sentence_filtered, sentenceid])

    cur.close()
    DBCon.commit()
    DBCon.close()



def UpdateTop100DB(filters):
    DBCon = sqlite3.connect(sys.argv[2])
    cur = DBCon.cursor()

    UpdateQuery = "update top100 set s_filtered=? where sentence=?"
    cur.execute("select sentence from top100")
    rows = cur.fetchall()
    for row in rows:
        sentence = row[0]
        sentence_filtered = ''.join([c for c in sentence if c not in filters])
        cur.execute(UpdateQuery, [sentence_filtered, sentence])

    cur.close()
    DBCon.commit()
    DBCon.close()

def ManualFilter(filters):
    while True:
        try:
            inputstr = input('to filter:')
            print(''.join([c for c in inputstr if c not in filters]))
        except:
            break

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python3 qa_removetopchar.py [sentencedatabasefilename] [top100db] [inputfile1] [inputfile2]...")
        exit(1)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    #filterchars = RetrieveTopCharFromFiles(100)
    top500 = '152036-897的4 :\n\t美，t./dm小空e调hjc！sa是亲您l一哦装~p_o安fi有服机b时下不元我以可在能费务好单要价级呢为人儿这。g送E购到品客天n开么见频收电：更货需花多欢请自吗变#个现东京Wu大抢】匹w店【？键全效用NU点k什高直免外无、后上挂款会了帮加爱旗舰关喜买营O支修迎羊哈过间享）就光临妹（联看系程们或只L定击没取等r日S新J如爆商号动Q准y纸防尼网吹体通换及注约丽敌省；家你惊心都制发柜麦闪接快果度滤还配保面问包惠活最xz抽冷热询作给出放月架F示升提满预咨订业,普精方劲内师傅使手克显管比行台选参特二话“”谢入早孔优售材减清\xa0超考q熊里实说蓝那灵件持;子哪风同米娃条萌门顾打嗯料标额婷&地气卡殊前尽v低常长来墙限楼详三格具库完也项回题节目期公流区理年返平对压层报式盛倩A温晒情量和择晚工链拉止编处物中狂室铜信众很其梦I微怎建火降哥产哆候器页般存第与进吧成R分运C肆侠明智K八议舒兔功他才少交意丸户够凉便环缩涛者适P际吒斯样承力质试音境(M砖次诺G若啊!Z经再两赔百D付连戳数性复速相排猛之国感增努正夏兜史息别兴差查静些典即)星市暖周积员据城秒五票券由哒稍已受想待肖白Y细'
    top100 = '152036-897的4 :\n\t美，t./dm小空e调hjc！sa是亲您l一哦装~p_o安fi有服机b时下不元我以可在能费务好单要价级呢为人儿这。g送E购到品客天n开么见频收电：更货需花多欢请自吗变#'

    f = top500[:39]
    logging.info(f)

    UpdateSentencesDB(f)
    UpdateTop100DB(f)

    #ManualFilter(f)


    logging.info("Done")