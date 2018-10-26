import os, sys, csv, logging, copy

Shops = {"美的": {"ID":1000001452, "profession": "大家电行业：空调"},
           "海尔": {"ID":1000001782,  "profession": "大家电行业：洗衣机"},
           "西门子": {"ID":1000001421,  "profession": "大家电行业：洗衣机"}
         }


fieldnames = ["question", "tag", "shopid", "brand", "cid3", "sku", "answer", "cat1",
              "cat2", "profession", "source"]

Data = []
Answers = {}


def WriteBrandFAQ(location):
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in Data:
            temprow = {}
            for key in row:
                if key in fieldnames:
                    temprow[key] = row[key]

            csvwriter.writerow(temprow)


def WriteBrandFAQ_Extra(location):
    with open(location, 'w', encoding="utf-8") as csvfile2:
        csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in Data:
            if row["ID"] < 400000:
                temprow = {}
                for key in row:
                    if key in fieldnames:
                        temprow[key] = row[key]

                csvwriter.writerow(temprow)


def GetOriginRow(answer):
    for row in Data:
        if row["answer"] == answer:
            return row
    logging.warning("Can't find a specific answer:{}".format(answer))
    return None


def ExpandBrandFAQ():
    ID = 200000
    for q in Questions:
        if "锁盖保护" in q.question:
            logging.info("锁盖保护")
        if q.answerid == -1 or q.answer == "":
            logging.warning("This question has -1 answerid: {}".format(q))
            continue
        originRow = GetOriginRow(q.answer)
        if originRow:
            row = copy.copy(originRow)
            row["question"] = q.question
            row["ID"] = 0
            ID += 1
            Data.append(row)


def ReadBrandFAQ(location):
    global Data
    with open(location, 'r', encoding="utf-8") as csvfile:
        firstline = csvfile.readline()
        delimiter = ','
        if "\t" in firstline:
            delimiter='\t'
        elif "," in firstline:
            delimiter=','

        csvfile.seek(0, 0)
        Data_Read = csv.DictReader(csvfile, delimiter=delimiter)
        # rowid = 0
        for row in Data_Read:
            # row["ID"] = rowid
            # rowid += 1
            if "\ufeffID" in row:
                row["ID"] = int(row["\ufeffID"])

            if row["answer"] not in Answers:
                newanswer = ANSWER(row["answer"])
                Answers[row["answer"]] = newanswer
            row["AnswerID"] = Answers[row["answer"]].ID
            Answers[row["answer"]].questions.add(row["question"])
            Data.append(row)


class ANSWER(object):
    counter = 1
    def __init__(self, text):
        self.questions = set()
        self.answer = text
        self.ID = ANSWER.counter
        ANSWER.counter += 1


class NewQuestion(object):
    def __init__(self, questionid, text):
        self.question = text
        self.questionid = questionid
        self.answerid = -1
        self.answer = ''
    def __str__(self):
        return "{}-{}-{}".format(self.question, self.questionid, self.answerid)


MyList = {}     #format: questionid, question
Questions = []
def ReadMyList(location):
    with open(location, 'r', encoding="utf-8") as mylist:
        for line in mylist:
            if line:
                qid, q = line.split("\t", 1)
                q = q.strip()
                Questions.append(NewQuestion(qid.strip(), q.strip() ))

    for q in Questions:
        for a in Answers.values():
            if q.question in a.questions:
                for allq in Questions:
                    if allq.questionid == q.questionid:
                        allq.answerid = a.ID
                        allq.answer = a.answer
                break
    #print("\n".join([str(q) for q in Questions]))


def SearchQuestion(newq):
    for q in Questions:
        if newq == q.question:
            return q
    logging.warning("can't find question {} in list".format(newq))
    return None


def ReadExpandList(location):
    with open(location, 'r', encoding="utf-8") as mylist:
        for line in mylist:
            if line:
                originq_text, _, q = line.split("\t")
                q = q.strip()
                originq = SearchQuestion(originq_text.strip())
                if originq is None:
                    continue
                newquestion = NewQuestion(originq.questionid, q )
                newquestion.answerid = originq.answerid
                Questions.append(newquestion)

    print("\n".join([str(q) for q in Questions]))
    print("size of Questions: {}".format(len(Questions)))



#if the input file has only 1 column that is keyword column, so the output has the cat1 and cat2
#if the input file has 3 columns, that is sku/Q/A. (for SKU related)
#otherwise, the input file should be the standard questionair format.
if __name__ == "__main__":

    if len(sys.argv) < 4:
        print("""Usage: python3 qa_expandqa.py  [inputqa] [qseedlist] [seed_expand] [outputqa] 
                 Example: src/tools/qa_expandqa.py ../../temp/brand.csv ../../temp/w1.txt ../../temp/what.txt ../../temp/brand.result.csv
""")
        exit(1)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    ReadBrandFAQ(sys.argv[1])
    ReadMyList(sys.argv[2])
    ReadExpandList(sys.argv[3])

    ExpandBrandFAQ()

    WriteBrandFAQ(sys.argv[4])
    WriteBrandFAQ_Extra(sys.argv[4] + ".new.csv")

