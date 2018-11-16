
import csv, logging, sys, re

fieldnames = ["id", "question", "tag", "shopId", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]

from functools import lru_cache
@lru_cache(maxsize=100000)
def  normalization( inputstr):
    if not hasattr(normalization, "fulllength"):
        loadlist()
    temp = re.sub("(https?|ftp)://\S+", " JDHTTP ", inputstr)
    temp = re.sub("\S+@\S+", " JDEMAIL ", temp)
    temp = re.sub("#E-s\d+", " ", temp)
    afterfilter = ""
    for c in temp:
        if c in normalization.dict_fh:
            afterfilter += normalization.dict_fh[c]
            continue
        if c in normalization.signtoremove:
            afterfilter += " "
            continue
        if '😀' <= c <= '🙏' or c == "☹":
            afterfilter += " "
            continue
        afterfilter += c

    return " ".join([x for x in afterfilter.split() if x not in normalization.stopwords])


def loadlist():
    normalization.fulllength = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｇｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９０：-"
    normalization.halflength = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890:-"
    normalization.dict_fh = {}
    for i in range(len(normalization.fulllength)):
        normalization.dict_fh[normalization.fulllength[i]] = normalization.halflength[i]
    normalization.signtoremove = "！？｡＂＃＄％＆＇（）＊＋，／；＜＝＞＠。［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏" \
                                 + "!\"#$%&\'()*+,/;<=>?@[\\]^_`{|}~"

    normalization.stopwords = set()
    with open(sys.argv[1], encoding="utf-8") as stopwords:
        for stopword in stopwords:
            if stopword.startswith("word,"):
                continue  # opening line
            if "," in stopword:
                word, _ = stopword.split(",")
                normalization.stopwords.add(word.strip())


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("""
            Usage:   python3 qa_applyid_initialize.py [stopwords] [qafile] [outputfile] [starting number] [source]
            Example: python3 qa_applyid_initialize.py ../../data/stopwords.csv ../../temp/whatis_plus100_n.txt ../../temp/wa.output.txt 10000000 "silicon valley"
                     python3 qa_applyid_initialize.py ../../data/stopwords.csv ../../temp/KGSKUQA3.csv ../../temp/wk.output.txt 50000000 knowledge

            """)
        exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    data = []
    uniquedata = set()
    rowid = int(sys.argv[4])
    logging.info("Start loading" + sys.argv[2])
    with open(sys.argv[2], 'r', encoding="utf-8") as sourcefile:
        firstline = sourcefile.readline()
        delimiter = ','
        if "\t" in firstline:
            delimiter='\t'
        elif "," in firstline:
            delimiter=','
        sourcefile.seek(0, 0)
        Data_Read = csv.DictReader(sourcefile, delimiter=delimiter)

        # rowid = 0
        for row in Data_Read:
            if row["question"] == "question":
                continue    #duplication of header.
            row["question"] = normalization(row["question"])
            if str(row) in uniquedata:   #exclude repeat data.
                continue
            uniquedata.add(str(row))

            row["source"] = sys.argv[5]     # "sillicon valley" for ts.  "knowledge" for kg
            row["id"] = rowid
            rowid += 1
            data.append(row)


    logging.info("Start writing " + sys.argv[3])
    with open(sys.argv[3], 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames, delimiter='\t')
        csvwriter.writeheader()
        csvwriter.writerows(data)

    logging.info(" Completed writing {} ".format(sys.argv[3]))
