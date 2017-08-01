
import logging, re
import Tokenization
import copy
#from RuleMacro import ProcessMacro

#import FeatureOntology
#usage: to output rules list, run:
#       python Rules.py > rules.txt


_RuleList = []
_ExpertLexicon = []
_MacroList = []
_MacroDict = {}     # not sure which one to use yet
_ruleCounter = 0

def _SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) if x ]   # remove comment.
    if not blocks:
        return "", ""
    comment = ""
    if len(blocks) > 1:
        comment = " ".join(blocks[1:])
    return blocks[0], comment

def SeparateComment(multiline):
    blocks = [x.strip() for x in re.split("\n", multiline) ]
    content = ""
    comment = ""
    for block in blocks:
        _content, _comment = _SeparateComment(block)
        if _content:
            content += "\n" + _content
        if _comment:
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
        self.comment = ''

    def SetRule(self, ruleString, ID=1):
        self.Origin = ruleString
        code, self.comment = SeparateComment(ruleString)
        blocks = [x.strip() for x in re.split("::", code)]
        if len(blocks) == 2:
            self.IsExpertLexicon = True
        else:
            blocks = [x.strip() for x in re.split("==", code)]
            if  len(blocks) != 2:
                logging.debug(" not separated by :: or == ")
                return
        if ID != 1:
            self.ID = ID
        self.RuleName = blocks[0]
        self.RuleContent = blocks[1]
        self.RuleContent = ProcessMacro(self.RuleContent)
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
        return self.output("details")

    def oneliner(self):
        return self.output("concise")

    # style: concise, or detail
    def output(self, style="concise"):
        output = "//ID:" + str(self.ID) + '\n'
        if style == "concise" :
            if self.comment:
                output += "//" + self.comment + '\n'
            if self.IsExpertLexicon:
                output += self.RuleName + " :: {"
            else:
                output += self.RuleName + " == {"
        else:
            if self.comment:
                output += "//" + self.comment + '\n'
            output += "[RuleName]=" + self.RuleName + '\n'
            output += "\t[Origin Content]=\n" + self.RuleContent + '\n'
            output += "\t[Compiled Content]=\n{"
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
            output += "_"
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
    logging.error(" Can't find a pair tag " + tagpair[0] + " in:" + string)
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


def ProcessMacro(ruleContent):
    macros = re.findall("@\w*", ruleContent)
    for macro in macros:
        if macro in _MacroDict:
            ruleContent = ruleContent.replace(macro, _MacroDict[macro].RuleContent)
        else:
            logging.warning("This macro " + macro + " does not exist.")
    return ruleContent

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
# -July 26, change to "==" or "::".
def LoadRules(RuleLocation):
    with open(RuleLocation, encoding="utf-8") as dictionary:
        rule = ""
        for line in dictionary:
            commentLocation = line.find("//")
            if commentLocation>=0:
                line = line[:commentLocation]   #remove anything after //

            line = line.strip()
            if not line:
                continue

            if line.find("::")>=0 or line.find("==") >= 0:
                if rule:
                    InsertRuleInList(rule)
                    rule = ""
            rule += " " + line

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

def ExpandRuleWildCard():
    Modified = False
    for rule in _RuleList:
        Expand = False
        #for token in rule.Tokens:
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            if token.repeat != [1, 1]:
                for repeat_num in range(token.repeat[0], token.repeat[1]+1):
                    newrule = Rule()
                    newrule.Origin = rule.Origin
                    newrule.comment = rule.comment
                    newrule.IsExpertLexicon = rule.IsExpertLexicon
                    newrule.RuleName = rule.RuleName+"_"+str(repeat_num)
                    newrule.RuleContent = rule.RuleContent
                    for tokenindex_pre in range(tokenindex):
                        new_node = copy.copy(rule.Tokens[tokenindex_pre])
                        newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                    for tokenindex_this in range(repeat_num):
                        new_node = copy.copy(rule.Tokens[tokenindex])
                        new_node.repeat = [1, 1]
                        newrule.Tokens.append(new_node)
                    for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
                        new_node = copy.copy(rule.Tokens[tokenindex_post])
                        newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
                    _RuleList.append(newrule)
                    Expand = True
            if Expand:
                break
        if Expand:
            _RuleList.remove(rule)
            Modified = True

    if Modified:
        logging.info("\tExpandRuleWildCard next level.")
        ExpandRuleWildCard()    #recursive call itself to finish all.
                    


def OutputRules():
    print("//Rules")
    for rule in _RuleList:
        print(rule.output("details"))

    print("//Expert Lexicons")
    for rule in _ExpertLexicon:
        print(rule.output("details"))

    print ("//Macros")
    for rule in _MacroDict.values():
        print(rule.output("details"))

    print("// End of Rules/Expert Lexicons/Macros")


#LoadRules(dir_path + "/../data/rule.txt")

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    # import os
    #
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # LoadRules(dir_path + "/../../fsa/Y/900NPy.xml")
    # LoadRules(dir_path + "/../../fsa/Y/1800VPy.xml")
    LoadRules("../../fsa/Y/900NPy.xml")
    LoadRules("../../fsa/Y/1800VPy.xml")
    ExpandRuleWildCard()
    OutputRules()