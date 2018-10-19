import logging, sys, os, re

def ExtractTerm(term):
    match = re.search("这?(.+)(指的|到底)", term)
    if match:
        t = match.group(1)
    else:
        t = term
    match = re.search("(.+)又", t)
    if match:
        t = match.group(1)
    match = re.search("一下(.+)", t)
    if match:
        t = match.group(1)
    match = re.search("介绍的(.+)", t)
    if match:
        t = match.group(1)
    match = re.search("(个|款)(.+)", t)
    if match:
        t = match.group(2)
    match = re.search("(个|款)(.+)", t)
    if match:
        t = match.group(2)
    match = re.search("(这|那)(.+)", t)
    if match:
        t = match.group(2)
    match = re.search("(说|问|咨询)下?(.+)", t)
    if match:
        t = match.group(2)
    match = re.search("(.+)是", t)
    if match:
        t = match.group(1)
    match = re.search("(.+)有", t)
    if match:
        t = match.group(1)

    if t == term:
        print(t)
    else:
        print("{}->{}".format(term, t))

    return t


#expandquestion is created as:
# select  question from answerfaq where question like "%是什么%" or question like "%什么是%" and shopid=1000001452;
if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    if len(sys.argv) < 2:
        print("Usage: python3 expandquestion.py [questionfile]  ")
        exit(1)

    questiongroups = []
    temp_terms = []
    templates = set()
    originquestion = []
    with open(sys.argv[1], 'r', encoding="utf-8") as questionlist:
        for questiongroup in questionlist:
            if questiongroup.strip():
                questiongroups.append(questiongroup.strip())

    for questiongroup in questiongroups:
        found = False
        questions = questiongroup.split("|||")
        termsinthisquestion = set()
        for question in questions:
            match =  re.match("(.+)什么", question)
            if match:
                term = match.group(1)
                termsinthisquestion.add(term)
                continue
            match =  re.match("个(.+)啥意思", question)
            if match:
                term = match.group(1)
                termsinthisquestion.add(term)
                continue
            match =  re.match("(.+)是", question)
            if match:
                term = match.group(1)
                termsinthisquestion.add(term)
                continue
            match =  re.match("什么是(.+)", question)
            if match:
                term = match.group(1)
                termsinthisquestion.add(term)
        if not termsinthisquestion:
            #temp_terms.append(termsinthisquestion)
            logging.warning("Can't find term from {}".format(questiongroup))
        temp_terms.append(termsinthisquestion)
    terms = []
    for termset in temp_terms:
        termsinthisquestion = set()
        for term in termset:
            # if " " in term:
            #     continue

            termsinthisquestion.add(ExtractTerm(term))
        terms.append(termsinthisquestion)

    for i in range(len(questiongroups)):
        questiongroup = questiongroups[i]
        questions = questiongroup.split("|||")
        for question in questions:
            Found = False
            if not terms[i]:
                continue
            for term in sorted(terms[i], key=len, reverse=True):
                if term in question:
                    template = question.replace(term, "{}")
                    templates.add(template)
                    Found = True
                    break
            if not Found:
                logging.warning("Can't find template from {}".format(question))

    for template in sorted(templates):
        print(template)
    allterms = set()
    for t in terms:
        allterms.update(t)

    for term in sorted(allterms):
        print(term)

    # with open("output.txt")
    #     for template in templates: