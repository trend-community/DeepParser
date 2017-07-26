
import logging, re
import Tokenization

#import FeatureOntology

_RuleList = []
_ExpertLexicon = []
_MacroList = []
_MacroDict = {}     # not sure which one to use yet
_ruleCounter = 0

def _SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0].strip(), " ".join(blocks[1:])

def SeparateComment(multiline):
    blocks = [x.strip() for x in re.split("\n", multiline) ]
    content = ""
    comment = ""
    for block in blocks:
        _content, _comment = _SeparateComment(block)
        content += "\n" + _content
        comment += " " + _comment
    return content, comment

class Rule:
    def __init__(self):
        global _ruleCounter
        _ruleCounter += 1
        self.ID = _ruleCounter
        self.RuleName = ''
        self.Origin = ''
        self.RuleContent = ''
        self.Tokens = []
        self.MatchString = ''
        self.Actions = {}
        self.IsExpertLexicon = False

    def SetRule(self, ruleString, ID=1):
        self.Origin = ruleString
        code, __ = SeparateComment(ruleString)
        blocks = [x.strip() for x in re.split("=", code)]
        if len(blocks) != 2:
            logging.info(" not separated by =")
            blocks = [x.strip() for x in re.split("::", code)]
            if  len(blocks) == 2:
                self.IsExpertLexicon = True
            else:
                return
        if ID != 1:
            self.ID = ID
        self.RuleName = blocks[0]
        self.RuleContent = blocks[1]
        try:
            self.Tokens = Tokenize(self.RuleContent)
        except Exception as e:
            logging.info("Failed to tokenize because: " + str(e))
            self.RuleName = ""
            return
        self.ProcessTokens()

    def ProcessTokens(self):
        for node in self.Tokens:
            #logging.info("\tnode word:" + node.word)
            if node.word.startswith("<"):
                node.word = node.word.lstrip("<")
                node.StartTrunk = True
            else:
                node.StartTrunk = False
            if node.word.endswith(">"):
                node.word = node.word.rstrip(">")
                node.EndTrunk = True
            else:
                node.EndTrunk = False

            node.repeat = [1,1]
            if node.word.endswith("?"):
                node.word = node.word.rstrip("?")
                node.repeat = [0, 1]
            if node.word.endswith("*"):
                node.word = node.word.rstrip("*")
                node.repeat = [0, 3]
            repeatMatch = re.match("(.*)\*(\d)*$", node.word)
            if not repeatMatch:
                repeatMatch = re.match("(.*)(\d)+$", node.word)
            if repeatMatch:
                node.word = repeatMatch[1]
                repeatMax = 3           #default as 3
                if repeatMatch[2]:
                    repeatMax = int(repeatMatch[2])
                node.repeat = [0, repeatMax]

            actionMatch = re.match("^\[(.*):(.*)\]$", node.word)
            if actionMatch:
                node.word = "[" + actionMatch[1] + "]"
                node.action = actionMatch[2]

            pointerMatch = re.match("^\^(.*?)\[(.*)\]$", node.word)
            if pointerMatch:
                node.word = "[" + pointerMatch[2] + "]"
                node.pointer = pointerMatch[1]

    def __str__(self):
        output = "[ID]=" + str(self.ID)
        output += "\t[RuleName]=" + self.RuleName
        output += "\t[Origin Content]=\n" + self.RuleContent
        output += "\n\t[Compiled Content]=\n{"
        for token in self.Tokens:
            if token.StartTrunk:
                output += "<"
            if hasattr(token, 'pointer'):
                output += "^" + token.pointer
            t = token.word
            if hasattr(token, 'action'):
                t = t.replace("]", ":" + token.action + "]")
            output += t
            if token.repeat != [1,1]:
                output += "*" + str(token.repeat[1])
            if token.EndTrunk:
                output += ">"
            output += " "
        output += "};\n"

        return output

    def oneliner(self):
        output = "[" + str(self.ID) + "]" + self.RuleName
        if self.IsExpertLexicon:
            output += " :: {"
        else:
            output += " = {"
        for token in self.Tokens:
            if token.StartTrunk:
                output += "<"
            if hasattr(token, 'pointer'):
                output += "^" + token.pointer
            t = token.word
            if hasattr(token, 'action'):
                t = t.replace("]", ":" + token.action + "]")
            output += t
            if token.repeat != [1,1]:
                output += "*" + str(token.repeat[1])
            if token.EndTrunk:
                output += ">"
            output += " "
        output += "};\n"

        return output

# Note: this tokenization is for tokenizing rule,
#       which is different from tokenizing the normal language.
# ignore { }
# For " [ ( ， find the couple tag ) ] " as token. Otherwise,
SignsToIgnore = "{};"
Pairs = ['[]', '()', '""', '\'\'']

def Tokenize(RuleContent):

    i = 0
    TokenList = []
    StartToken = False
    while i < len(RuleContent):
        if RuleContent[i] in SignsToIgnore:
            i += 1
            continue
        if RuleContent[i].isspace():
            if StartToken:
                StartToken = False
                EndOfToken = i
                node = Tokenization.EmptyBase()
                node.word = RuleContent[StartPosition:EndOfToken]
                TokenList.append(node)
                i = EndOfToken
                if i == len(RuleContent):
                    break
        else:
            if not StartToken:
                StartToken = True
                StartPosition = i

        for pair in Pairs:
            if RuleContent[i] == pair[0]:
                #StartPosition = i
                end = _SearchPair(RuleContent[i+1:], pair)
                if end >= 0:
                    StartToken = False
                    EndOfToken = i+1+end + _SearchToEnd(RuleContent[i+1+end:])
                    node = Tokenization.EmptyBase()
                    node.word = RuleContent[StartPosition:EndOfToken]
                    TokenList.append(node)
                    i = EndOfToken
                    break

        i += 1

    if StartToken:       #wrap up the last one
        EndOfToken = i
        node = Tokenization.EmptyBase()
        node.word = RuleContent[StartPosition:EndOfToken]
        TokenList.append(node)

    return TokenList

# return -1 if failed. Should throw error?
def _SearchPair(string, tagpair):
    depth = 0
    i = 0
    while i<len(string):
        if string[i] == tagpair[1]:
            depth -= 1
            if depth == -1: # found!
                return i
        if string[i] == tagpair[0]:
            depth += 1
        i += 1
    logging.error(" Can't find a pair tag!" + string)
    raise Exception(" Can't find a pair tag!" + string)
    return -1

# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or starting of next token (TODO: next token? sure??).
def _SearchToEnd(string):
    if not string:      # if it is empty
        return 0
    i = 1
    while i<len(string):
        if string[i] in SignsToIgnore:
            return i
        if string[i].isspace():
            return i
        for pair in Pairs:
            if string[i] == pair[0]:
                return i
        i += 1
    return i


# a rule is not necessary in one line.
# if the line is end with ";", then this is one rule;
#   sometimes the line does not end with ; but it is still one rule.
# if the line has { but not }, then this is not one rule, continue untile }; is found;
# if the line end with "=", then continue;
#  --- Reorganize it as: ---
# If the line end with "=", then continue;
# otherwise, find "{" and "}" in this line. if there is only "{" but not "}", then continue;
#                  otherwise, conclude one line as a rule.
# continue until };, or a blank line.
def LoadRules(RuleLocation):

    with open(RuleLocation, encoding="utf-8") as dictionary:
        RuleInMultiLines = False
        for line in dictionary:
            line = line.strip()

            if line.startswith("//"):
                continue

            if RuleInMultiLines == False:
                rule = line
                if line.endswith("=") or line.endswith("::"):
                    RuleInMultiLines = True
                else:
                    if line.find("{") >=0 and line.find("}") < 0:
                        RuleInMultiLines = True
            else:
                if line.find("::") >= 0:
                    #first line of this rule. wrap up the previous rule
                    InsertRuleInList(rule)
                    rule = ""

                rule += " " + line
                if line.find("};") >= 0 or line == "":
                    RuleInMultiLines = False

            if RuleInMultiLines == False:
                InsertRuleInList(rule)
                rule = ""

        if rule:
            InsertRuleInList(rule)

def InsertRuleInList(string):
    global _RuleList, _ExpertLexicon, _MacroDict
    node = Rule()
    node.SetRule(string)
    if node.RuleName:
        if node.RuleName.startswith("@"):
            _MacroDict.update({node.RuleName: node})
        else:
            if node.IsExpertLexicon:
                _ExpertLexicon.append(node)
            else:
                _RuleList.append(node)


def OutputRules():
    for rule in _RuleList:
        print(rule.oneliner())
    for rule in _ExpertLexicon:
        print(rule.oneliner())
    for rule in _MacroDict.values():
        print(rule.oneliner())

import os
dir_path = os.path.dirname(os.path.realpath(__file__))
LoadRules(dir_path + "/../../fsa/Y/1800VPy.xml")
LoadRules(dir_path + "/../../fsa/Y/900NPy.xml")
#LoadRules("../data/rule.txt")

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


    OutputRules()