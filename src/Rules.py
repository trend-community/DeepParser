
import logging, re, os
import Tokenization
import copy
#from RuleMacro import ProcessMacro

#import FeatureOntology
#usage: to output rules list, run:
#       python Rules.py > rules.txt
from FeatureOntology import PrintMissingFeatureSet

_RuleList = []
_ExpertLexicon = []
_MacroList = []
_MacroDict = {}     # not sure which one to use yet
_ruleCounter = 0

def ResetRules():
    global _RuleList, _ExpertLexicon, _MacroList, _MacroDict, _ruleCounter


    del _RuleList[:]
    del _ExpertLexicon[:]
    del _MacroList[:]
    _MacroDict = {}  # not sure which one to use yet
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
        ProcessTokens(self.Tokens)

    def __str__(self):
        return self.output("details")

    def oneliner(self):
        return self.output("concise")

    # style: concise, or detail
    def output(self, style="concise"):
        output = "//ID:" + str(self.ID)
        output += "[Expert Lexicon]\n" if self.IsExpertLexicon else "[Rule]\n"
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


def RemoveExcessiveSpace(Content):
    #Remove any whitespace around | sign, so it ismade as a word.
    r = re.compile("\s*\|\s*", re.MULTILINE)
    Content = r.sub("|", Content)

    r = re.compile("<\s*", re.MULTILINE)
    Content = r.sub("<", Content)

    r = re.compile("\s*>", re.MULTILINE)
    Content = r.sub(">", Content)

    return Content

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

    RuleContent = RemoveExcessiveSpace(RuleContent)

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
                #i = EndOfToken
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
                    EndOfToken = i+2+end + _SearchToEnd(RuleContent[i+1+end+1:])
                    node = Tokenization.EmptyBase()
                    node.word = RuleContent[StartPosition:EndOfToken+1]
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


def ProcessTokens(Tokens):
    for node in Tokens:
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

        if node.word.startswith("`"):
            node.word = node.word.lstrip("`")
            node.ReStartPoint = True

        node.repeat = [1,1]
        if node.word.endswith("?"):
            node.word = node.word.rstrip("?")
            node.repeat = [0, 1]
        if node.word.endswith("*"):
            node.word = node.word.rstrip("*")
            node.repeat = [0, 3]

        repeatMatch = re.match("(.*\D+)(\d+)\*(\d+)$", node.word)
        if repeatMatch:
            node.word = repeatMatch.group(1)
            node.repeat = [int(repeatMatch.group(2)), int(repeatMatch.group(3))]

        repeatMatch = re.match("(.+)\*(\d*)$", node.word)
        if not repeatMatch:
            repeatMatch = re.match("(.*\D+)(\d+)$", node.word)
        if repeatMatch:
            node.word = repeatMatch.group(1)
            repeatMax = 3           #default as 3
            if repeatMatch.group(2):
                repeatMax = int(repeatMatch.group(2))
            node.repeat = [0, repeatMax]

        pointerMatch = re.match("\^(.*)\[(.+)\]$", node.word)
        if pointerMatch:
            node.word = "[" + pointerMatch.group(2) + "]"
            node.pointer = pointerMatch.group(1)

        pointerMatch = re.match("\^(.+)$", node.word)
        if pointerMatch:
            node.word = "[" + pointerMatch.group(1) + "]"
            node.pointer = ''

        actionMatch = re.match("^\[(.+):(.+)\]$", node.word)
        # if not actionMatch:
        #     actionMatch = re.match("^(.+):(.*)$", node.word)
        if actionMatch:
            node.word = "[" + actionMatch.group(1) + "]"
            node.action = actionMatch.group(2)

        actionMatch = re.match("^\[(\d+) (.+)\]$", node.word)
        if actionMatch:
            node.word = "[" + actionMatch.group(2) + "]"
            node.priority = int(actionMatch.group(1))

# return -1 if failed. Should throw error?
def _SearchPair(string, tagpair, Reverse=False):
    depth = 0
    if Reverse:
        i = len(string)-1
        currentTagIndex = 1
        targetTagIndex = 0
        direction = -1
    else:
        i = 0
        currentTagIndex = 0
        targetTagIndex = 1
        direction = 1
    while 0<=i<len(string):
        if string[i] == tagpair[targetTagIndex]:
            depth -= 1
            if depth == -1: # found!
                return i
        if string[i] == tagpair[currentTagIndex]:
            depth += 1
        i += direction
    logging.error(" Can't find a pair tag " + tagpair[0] + " in:" + string)
    raise Exception(" Can't find a pair tag!" + string)
    return -1

# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or starting of next token (TODO: next token? sure??).
def _SearchToEnd(string, Reverse=False):
    if not string:      # if it is empty
        return 0
    if Reverse:
        i = len(string)-1
        targetTagIndex = 1
        direction = -1
    else:
        i = 0
        targetTagIndex = 0
        direction = 1
    while 0<=i<len(string):
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                if i>0 and string[i-1] == "|":
                    endofpair = _SearchPair(string[i+1:], pair, Reverse)
                    if endofpair >= 0:
                        if Reverse:
                            i -= endofpair +1
                        else:
                            i += endofpair +1 # TODO: verify to +1
                    else:
                        raise "Can't find a pair in _SearchToEnd()"
                        return 0   # error. stop the searching immediately.
        if string[i] in SignsToIgnore:
            return i-direction
        if string[i].isspace():
            return i-direction
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                return i-direction
        i += direction
    return i


# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or starting of next token (TODO: next token? sure??).
def _SearchToEnd_OrBlock(string, Reverse=False):
    if not string:      # if it is empty
        return 0
    if Reverse:
        i = len(string)-1
        targetTagIndex = 1
        direction = -1
    else:
        i = 0
        targetTagIndex = 0
        direction = 1
    while 0<=i<len(string):
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                if i>0 and string[i-1] == "|":
                    endofpair = _SearchPair(string[i+1:], pair, Reverse)
                    if endofpair >= 0:
                        if Reverse:
                            i -= endofpair +1
                        else:
                            i += endofpair +1
                    else:
                        raise "Can't find a pair in _SearchToEnd()"
                        return 0   # error. stop the searching immediately.
        if re.match("\W", string[i]):
            return i-direction
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                return i-direction
        i += direction
    return i


def ProcessMacro(ruleContent):
    macros_with_parameters = re.findall("#\w*\(.+\)", ruleContent)
    for macro in macros_with_parameters:
        macroName = re.match("^(#.*)\(", macro)[0]
        for MacroName in _MacroDict:
            if MacroName.startswith(macroName):
                MacroParameters = re.findall("(\d+)=(\$\w+)", MacroName)
                macroParameters = re.findall("(\d+)=?(\w+)?", macro)
                macroContent = _MacroDict[MacroName].RuleContent
                for Parameter_Pair in MacroParameters:
                    for parameter_pair in macroParameters:
                        if Parameter_Pair[0] == parameter_pair[0]:
                            if len(parameter_pair) == 1 or parameter_pair[1] == "NULL":
                                ReplaceWith = ''
                            else:
                                ReplaceWith = parameter_pair[1]
                            macroContent = macroContent.replace(Parameter_Pair[1], ReplaceWith)
                ruleContent = ruleContent.replace(macro, macroContent)
    #return ruleContent

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
    RuleFileName = os.path.basename(RuleLocation)
    try:
        RuleFileID = int(re.findall('^\d+', RuleFileName)[0])
    except IndexError:
        logging.error("Rule Filename must start with a number!")
        raise

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
                    InsertRuleInList(rule, RuleFileID)
                    rule = ""
            rule += " " + line

        if rule:
            InsertRuleInList(rule, RuleFileID)

def InsertRuleInList(string, RuleFileID = 1):
    global _RuleList, _ExpertLexicon, _MacroDict
    node = Rule()
    node.FileID = RuleFileID
    node.SetRule(string)
    if node.RuleName:
        if node.RuleName.startswith("@") or node.RuleName.startswith("#"):
            if node.RuleName in _MacroDict:
                logging.warning("This rule name " + node.RuleName + " is already used for Macro " + _MacroDict[node.RuleName]
                                + " \n but now you have: " + string + "\n\n")
                return
            _MacroDict.update({node.RuleName: node})
        else:
            if node.IsExpertLexicon:
                # It is known that the expert lexicons have multiple "rules" that have "or" relationship.
                #    so no need to check this.
                # for n in _ExpertLexicon:
                #     if n.RuleName == node.RuleName:
                #         logging.warning("This rule name " + node.RuleName + " is already used for Expert Lexicon " + str(n)
                #                         + " \n but now you have: " + string + "\n\n")
                #         return
                _ExpertLexicon.append(node)
            else:
                for n in _RuleList:
                    if n.RuleName == node.RuleName:
                        logging.warning(
                            "This rule name " + node.RuleName + " is already used for Rule " + str(n)
                            + " \n but now you have: " + string + "\n\n")
                        return
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
                        newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                    for tokenindex_this in range(repeat_num):
                        new_node = copy.copy(rule.Tokens[tokenindex])
                        new_node.repeat = [1, 1]
                        newrule.Tokens.append(new_node)
                    for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
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

# def ExpandParenthesisAndOrBlock():
#     Modified = _ExpandParenthesis()
#     Modified = Modified or _ExpandOrBlock()
#     if Modified:
#         logging.info("ExpandParenthesisAndOrBlock to next level")
#         ExpandParenthesisAndOrBlock()


def ExpandParenthesis():
    Modified = False
    for rule in _RuleList:
        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            if token.word.startswith("(") and token.word.endswith(")"):
                #logging.warning("Parenthesis:\n\t" + token.word + "\n\t rulename: " + rule.RuleName )
                subTokenlist = Tokenize(token.word[1:-1])
                if not subTokenlist:
                    print("empty parenthesis: " + token.word + " in " + str(rule))
                    raise "empty parenthesis"
                    #continue
                ProcessTokens(subTokenlist)
                if hasattr(token, "pointer"):
                    subTokenlist[0].pointer = token.pointer
                subTokenlist[0].StartTrunk = token.StartTrunk
                subTokenlist[-1].EndTrunk = token.EndTrunk

                newrule = Rule()
                newrule.Origin = rule.Origin
                newrule.comment = rule.comment
                newrule.IsExpertLexicon = rule.IsExpertLexicon
                newrule.RuleName = rule.RuleName+"_p"+str(tokenindex)
                newrule.RuleContent = rule.RuleContent
                for tokenindex_pre in range(tokenindex):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                for subtoken in subTokenlist:
                    newrule.Tokens.append(subtoken)
                for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
                _RuleList.append(newrule)
                Expand = True
                break
        if Expand:
            _RuleList.remove(rule)
            Modified = True

    #return Modified
    if Modified:
        logging.info("\tExpandParenthesis next level.")
        ExpandParenthesis()    #recursive call itself to finish all.


def _ProcessOrBlock(Content, orIndex):
    if orIndex <= 0 or orIndex >= len(Content):
        raise "Wrong orIndex:" + str(orIndex)
    if Content[orIndex] != '|':
        raise "Wrong orIndex for Content:" + Content[orIndex]

    start = orIndex
    end = orIndex

    for pair in Pairs:
        if Content[orIndex+1] == pair[0]:
            end = end + 2 + _SearchPair(Content[orIndex+2:], pair)
    if end == orIndex:  # the next character is not pair, so it is a normal word
        end = end + 2 + _SearchToEnd_OrBlock(Content[orIndex+2:])

    for pair in Pairs:
        if Content[orIndex-1] == pair[1]:
            start = _SearchPair(Content[:orIndex-1], pair, Reverse=True)
    if start == orIndex:  # the next character is not pair, so it is a normal word
        start = _SearchToEnd_OrBlock(Content[:orIndex-1], Reverse=True)



    return Content[start:end+1], Content[start:orIndex], Content[orIndex+1:end+1]

def ExpandOrBlock():
    Modified = False
    counter = 0
    print("Before running, there are " + str(len(_RuleList)) + " in rulelist")
    for rule in _RuleList:

        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            orIndex = token.word.find(")|")+1
            if orIndex <= 0:
                orIndex = token.word.find("|(")
                if orIndex <= 0:
                    continue

            counter += 1
            print(counter)
            
            originBlock, leftBlock, rightBlock = _ProcessOrBlock(token.word, orIndex)

            #left:
            newrule = Rule()
            newrule.Origin = rule.Origin
            newrule.comment = rule.comment
            newrule.IsExpertLexicon = rule.IsExpertLexicon
            newrule.RuleName = rule.RuleName+"_o"+str(tokenindex)
            newrule.RuleContent = rule.RuleContent
            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
            newtoken = copy.copy(rule.Tokens[tokenindex])
            newtoken.word = newtoken.word.replace(originBlock, leftBlock)
            newrule.Tokens.append(newtoken)
            for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
            _RuleList.append(newrule)

            # right:
            newrule = Rule()
            newrule.Origin = rule.Origin
            newrule.comment = rule.comment
            newrule.IsExpertLexicon = rule.IsExpertLexicon
            newrule.RuleName = rule.RuleName + "_o" + str(tokenindex)
            newrule.RuleContent = rule.RuleContent
            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
            newtoken = copy.copy(rule.Tokens[tokenindex])
            newtoken.word = newtoken.word.replace(originBlock, rightBlock)
            newrule.Tokens.append(newtoken)
            for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
            _RuleList.append(newrule)

            Expand = True
            break

        if Expand:
            _RuleList.remove(rule)
            Modified = True

    if Modified:
        logging.info("\tExpandOrBlock next level.")
        ExpandOrBlock()    #recursive call itself to finish all.


def OutputRules(style="details"):
    print("// ****Rules****")
    for rule in _RuleList:
        print(rule.output(style))

    print("// ****Expert Lexicons****")
    for rule in _ExpertLexicon:
        print(rule.output(style))

    print ("// ****Macros****")
    for rule in _MacroDict.values():
        print(rule.output(style))

    print("// End of Rules/Expert Lexicons/Macros")


#LoadRules(dir_path + "/../data/rule.txt")

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    # import os
    #
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # LoadRules(dir_path + "/../../fsa/Y/900NPy.xml")
    # LoadRules(dir_path + "/../../fsa/Y/1800VPy.xml")
    #LoadRules("../../fsa/Y/900NPy.xml")
    #LoadRules("../../fsa/Y/800VGy.txt")

    LoadRules("../../fsa/Y/1test_rules.txt")

    ExpandRuleWildCard()
    ExpandOrBlock()
    ExpandParenthesis()
    ExpandRuleWildCard()

    ExpandRuleWildCard()

    OutputRules("details")
    PrintMissingFeatureSet()