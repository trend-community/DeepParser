import Rules
from utils import *
import os
PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
XLocation = os.path.dirname(PipeLineLocation) + "/"

sixngram = "6ngramMain.txt"
fivengram = "5ngramKG.txt"
segmentslash = XLocation + "segmentslash.txt"
mainlex = XLocation + "main2017.txt"

Rules.LoadRules(XLocation, sixngram)
Rules.LoadRules(XLocation, fivengram)

ruleDict = Rules.RuleGroupDict

with open(segmentslash, 'w',encoding='utf-8') as file:
    for rule in ruleDict.keys():
        rulelist = ruleDict.get(rule).RuleList
        for node in rulelist:
            output = ""
            for token in node.Tokens:
                word = token.word
                if "FULLSTRING" in word:
                    word = word.replace("FULLSTRING","")
                    word = word.strip()
                if word:
                    word = word.replace("'", "")
                    word = word.strip()
                    if word == "/":
                        continue
                    else:
                        output += word + "/"

            if output:
                output = output[:-1]
                file.write(output +"\n")

    with open(mainlex, encoding='utf-8') as inputfile:
        for line in inputfile:
            line = line.strip()
            if line.startswith("//"):
                continue
            else:
                if line:
                    if "//" in line:
                        line = line[0:line.index("//")]
                    if "/" in line:
                        line = line.strip()
                        file.write(line+"\n")



