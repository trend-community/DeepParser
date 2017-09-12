
import logging, re, os, operator
import Tokenization
import copy
#from RuleMacro import ProcessMacro

#import FeatureOntology
#usage: to output rules list, run:
#       python Rules.py > rules.txt

from LogicOperation import CheckPrefix as LogicOperation_CheckPrefix
from LogicOperation import SeparateOrBlocks as LogicOperation_SeparateOrBlocks
import FeatureOntology

_RuleList = []
_ExpertLexicon = []
_MacroList = []
_MacroDict = {}     # not sure which one to use yet
_ruleCounter = 0
RuleFileList = []
UnitTest = {}

def ResetRules():
    global _RuleList, _ExpertLexicon, _MacroList, _MacroDict, _ruleCounter


    del _RuleList[:]
    del _ExpertLexicon[:]
    del _MacroList[:]
    _MacroDict = {}  # not sure which one to use yet
    _ruleCounter = 0


def _SeparateComment(line):
    line = line.strip()
    SlashLocation = line.find("//")
    if SlashLocation < 0:
        return line, ""
    else:
        return line[:SlashLocation].strip(), line[SlashLocation+2:].strip()

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

#If it is one line, that it is one rule;
#if it has several lines in {} or () block, then it is one rule;
# otherwise (it has multiple lines but not in one block), process the first line,
# return the rest as "remaining"
def SeparateRules(multilineString):
    lines = re.split("\n", multilineString)
    if len(lines) == 1:
        return multilineString, None
    if multilineString[0] == "(" and _SearchPair(multilineString[1:], "()") >= len(multilineString)-3: # sometimes there is ";" sign
        return multilineString, None
    if multilineString[0] == "{" and _SearchPair(multilineString[1:], "{}") >= len(multilineString)-3:
        return multilineString, None

    return lines[0], "\n".join(lines[1:])


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

    def SetRule(self, ruleString, ID=1, FileName="_"):
        self.Origin = ruleString
        self.FileName = FileName
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
        self.RuleContent, remaining = SeparateRules(blocks[1])
        self.RuleContent = ProcessMacro(self.RuleContent)
        if self.RuleName.startswith("@") or self.RuleName.startswith("#"):
            return  #stop processing macro.

        try:
            self.Tokens = Tokenize(self.RuleContent)
        except Exception as e:
            logging.error("Failed to tokenize because: " + str(e))
            logging.error("Rulename is: " + self.RuleName)
            self.RuleName = ""
            return
        ProcessTokens(self.Tokens)

        return remaining

    def __str__(self):
        return self.output("details")

    def oneliner(self):
        return self.output("concise")

    # style: concise, or detail
    def output(self, style="concise"):
        output = "//ID:" + str(self.ID)
        if self.IsExpertLexicon:
            output += "[Expert Lexicon]\n"
        elif self.RuleName.startswith("@"):
            output += "[Macro]\n"
        elif self.RuleName.startswith("#"):
            output += "[Macro with parameter]\n"
        else:
            output += "[Rule]\n"

        if style == "concise" :
            if self.comment:
                output += "//" + self.comment + '\n'
            if self.IsExpertLexicon:
                output += self.RuleName + " :: {"
            else:
                output += self.RuleName + " == {"

            if len(self.Tokens) == 0:
                output += self.RuleContent
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
                t = t.replace("]", "[ACTION]" + token.action + "]")
            output += t
            if token.repeat != [1,1]:
                output += "*" + str(token.repeat[1])
            if token.EndTrunk:
                output += ">"
            output += "_"   # should be a space. use _ in dev mode.
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

    Content = Content.strip(";")

    return Content

# Note: this tokenization is for tokenizing rule,
#       which is different from tokenizing the normal language.
# ignore { }
# For " [ ( ， find the couple tag ) ] " as token. Otherwise,
SignsToIgnore = "{};"
Pairs = ['[]', '()', '""', '\'\'', '//']

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
            if RuleContent[i] == pair[0] and (i==0 or RuleContent[i-1] != "\\"): #escape:
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
            node.RestartPoint = True
        else:
            node.RestartPoint = False

        node.repeat = [1,1]
        if node.word.endswith("?"):
            node.word = node.word.rstrip("?")
            node.repeat = [0, 1]
        if node.word.endswith("*"):
            node.word = node.word.rstrip("*")
            node.repeat = [0, 3]

        repeatMatch = re.match("(.*[\]\"')])(\d+)\*(\d+)$", node.word)
        if repeatMatch:
            node.word = repeatMatch.group(1)
            node.repeat = [int(repeatMatch.group(2)), int(repeatMatch.group(3))]

        repeatMatch = re.match("(.+)\*(\d*)$", node.word)
        if not repeatMatch:
            repeatMatch = re.match("(.*[\])\"'])(\d+)$", node.word)
        if repeatMatch:
            node.word = repeatMatch.group(1)
            repeatMax = 3           #default as 3
            if repeatMatch.group(2):
                repeatMax = int(repeatMatch.group(2))
            node.repeat = [0, repeatMax]

        pointerMatch = re.match("\^(\w*)\[(.+)\]$", node.word)
        if pointerMatch:
            node.word = "[" + pointerMatch.group(2) + "]"
            node.pointer = pointerMatch.group(1)

        pointerMatch = re.match("\^(.+)$", node.word)
        if pointerMatch:
            node.word = "[" + pointerMatch.group(1) + "]"
            node.pointer = ''
        #
        # actionMatch = re.match("\[(.+):(.+)\]$", node.word)
        # if actionMatch:
        #     ActionIndex = FindLastColonWithoutSpecialCharacter(node.word)
        #     if ActionIndex>0:
        #         action = node.word[ActionIndex + 1:-1]
        #         word_wo_action = "[" + node.word[1:ActionIndex] + "]"
        #
        #         if "(" not in word_wo_action and ":" in word_wo_action:
        #                 orblocks = re.split("\]\|\[", node.word)
        #                 new_word = "(" + "])|([".join(orblocks) + ")"
        #                 node.word = new_word
        #         else:
        #             node.action = action
        #             node.word = word_wo_action
        #     else:   # [CM:Done]|[COLN|JM]
        #         if "(" not in node.word and "]|[" in node.word :
        #             orblocks = re.split("\]\|\[", node.word)
        #             new_word = "(" + "])|([".join(orblocks) + ")"
        #             node.word = new_word
        #
        # actionMatch_complicate = re.match("(.+)|\[(.+):(.+)\]]")
        if "(" not in node.word and ":" in node.word:
            orblocks = re.split("\|\[", node.word)
            if len(orblocks)>1:
                node.word = "(" + ")|([".join(orblocks) + ")"  # will be tokenize later.
            else:
                orblocks = re.split("\]\|", node.word)
                if len(orblocks) > 1:
                    node.word = "(" + "])|(".join(orblocks) + ")"  # will be tokenize later.
                else:   #no "()" sign, and no "|" sign
                    actionMatch = re.match("\[(.+):(.+)\]$", node.word)
                    if actionMatch:
                        node.word = "[" + actionMatch.group(1) + "]"
                        node.action = actionMatch.group(2)

        priorityMatch = re.match("^\[(\d+) (.+)\]$", node.word)
        if priorityMatch:
            node.word = "[" + priorityMatch.group(2) + "]"
            node.priority = int(priorityMatch.group(1))

# Avoid [(AS:action)|sjfa]
#Good character in action:
#     ^.M $
#Bad characters in action:
#     )?':
def FindLastColonWithoutSpecialCharacter(string):
    index = len(string) - 2
    while index>=0:
        if string[index] == ":":
            return index
        if string[index].isalnum() or \
            string[index] in "^. $,>+-":
            index -=1
        else:
#            logging.warning("not a ligit action: " + string[index] + " in " + string )
            return -1
    return -1

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
    #return -1

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
        modified = False
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                if i>0 and string[i-1] == "|":
                    endofpair = _SearchPair(string[i+1:], pair, Reverse)
                    if endofpair >= 0:
                        if Reverse:
                            i -= endofpair +1
                        else:
                            i += endofpair +1 # TODO: verify to +1
                        modified = True
                    else:
                        raise Exception("Can't find a pair in _SearchToEnd()")
                        #return -1   # error. stop the searching immediately.
        if string[i] in SignsToIgnore:
            return i-direction
        if string[i].isspace():
            return i-direction

        # if string[i] in "[(":   #start of next token
        #     return i-direction
        if not modified:
            for pair in Pairs:
                if string[i] == pair[targetTagIndex]:
                    return i-direction
        i += direction
    return i


# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or any non-alnum (\W)
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
                        raise Exception("Can't find a pair in _SearchToEnd()")
                        #return 0   # error. stop the searching immediately.
        if re.match("\W", string[i]):
            return i-direction
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                return i-direction
        i += direction

    if i<0:
        i = 0
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
    if RuleFileName not in RuleFileList:
        RuleFileList.append(RuleFileName)

    with open(RuleLocation, encoding="utf-8") as dictionary:
        rule = ""
        for line in dictionary:
            # commentLocation = line.find("//")
            # if commentLocation>=0:
            #     line = line[:commentLocation]   #remove anything after //

            line = line.strip()
            if not line:
                continue

            if line.find("::")>=0 or line.find("==") >= 0:
                if rule:
                    InsertRuleInList(rule, RuleFileName)
                    rule = ""
            rule += "\n" + line

        if rule:
            InsertRuleInList(rule, RuleFileName)

def InsertRuleInList(string, RuleFileName = "_"):
    global _RuleList, _ExpertLexicon, _MacroDict
    node = Rule()
    remaining = node.SetRule(string, FileName = RuleFileName)
    if node.RuleName:
        if node.RuleName.startswith("@") or node.RuleName.startswith("#"):
            if node.RuleName in _MacroDict:
                logging.warning("This macro name " + node.RuleName + " is already used for Macro " + str(_MacroDict[node.RuleName]) \
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
 #                       return
                _RuleList.append(node)

    if remaining:
        if node.IsExpertLexicon:
            fakeString = node.RuleName + "_" + str(node.ID) + " :: " + remaining
        else:
            fakeString = node.RuleName + "_" + str(node.ID) + " == " + remaining
        InsertRuleInList(fakeString)

    testLocation = node.comment.find("test:")
    if testLocation < 0:
        testLocation = node.comment.find("TEST:")
    if testLocation >= 0:
        TestSentence = node.comment[testLocation + 5:].strip()
        if TestSentence != "":
            UnitTest.update({node.RuleName: TestSentence})


def _ExpandRuleWildCard_List(OneList):
    Modified = False
    for rule in OneList:
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
                    newrule.FileName = rule.FileName
                    for tokenindex_pre in range(tokenindex):
                        newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                    for tokenindex_this in range(repeat_num):
                        new_node = copy.copy(rule.Tokens[tokenindex])
                        new_node.repeat = [1, 1]
                        newrule.Tokens.append(new_node)
                    NextIsStart = False
                    NextIsRestart = False
                    NextIsPointer = False
                    if repeat_num == 0: # this token is removed. some features need to copy to others
                        origin_node = rule.Tokens[tokenindex]
                        if origin_node.StartTrunk:
                            NextIsStart = True
                        if origin_node.EndTrunk:
                            lastToken = newrule.Tokens[-1]
                            lastToken.EndTrunk = True
                        if origin_node.RestartPoint:
                            NextIsRestart = True
                        if hasattr(origin_node, "pointer"):
                            NextIsPointer = True
                            NextPointer = origin_node.pointer
                    for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
                        new_node = copy.copy(rule.Tokens[tokenindex_post])
                        if tokenindex_post == tokenindex+1:
                            if NextIsStart:
                                new_node.StartTrunk = True
                            if NextIsRestart:
                                new_node.RestartPoint = True
                            if NextIsPointer and NextPointer :
                                new_node.pointer = NextPointer
                        newrule.Tokens.append(new_node)
                    OneList.append(newrule)
                    Expand = True
            if Expand:
                break
        if Expand:
            OneList.remove(rule)
            Modified = True
            
    return Modified


def ExpandRuleWildCard():
    
    Modified = _ExpandRuleWildCard_List(_RuleList)
    Modified = Modified or _ExpandRuleWildCard_List(_ExpertLexicon)

    if Modified:
        logging.info("\tExpandRuleWildCard next level.")
        ExpandRuleWildCard()    #recursive call itself to finish all.

def ExpandParenthesisAndOrBlock():
    Modified = _ExpandParenthesis(_RuleList)
    Modified = Modified or _ExpandParenthesis(_ExpertLexicon)
    Modified = Modified or _ExpandOrBlock(_RuleList)
    Modified = Modified or _ExpandOrBlock(_ExpertLexicon)
    
    if Modified:
        logging.warning("ExpandParenthesisAndOrBlock to next level")
        ExpandParenthesisAndOrBlock()


def _ExpandParenthesis(OneList):
    Modified = False
    for rule in OneList:
        if len(rule.RuleName) > 400:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + rule.RuleName)
            continue
        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            if (token.word.startswith("(") and len(token.word) == 2+_SearchPair(token.word[1:], ["(", ")"])) \
                    or (token.word.startswith("[(") and len(token.word) == 4+_SearchPair(token.word[2:], ["(", ")"])):
                #logging.warning("Parenthesis:\n\t" + token.word + "\n\t rulename: " + rule.RuleName )
                parenthesisIndex = token.word.find("(")
                try:
                    subTokenlist = Tokenize(token.word[parenthesisIndex+1:-parenthesisIndex-1])
                except Exception as e:
                    logging.error("Failed to tokenize because: " + str(e))
                    logging.error("Rule name: " + rule.RuleName)
                    continue

                if subTokenlist:
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
                newrule.FileName = rule.FileName
                for tokenindex_pre in range(tokenindex):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                for subtoken in subTokenlist:
                    newrule.Tokens.append(subtoken)
                for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
                OneList.append(newrule)
                Expand = True
                #logging.warning("\tExpand Parentheses is true, because of " + rule.RuleName)
                break
        if Expand:
            OneList.remove(rule)
            Modified = True

    return Modified
    # if Modified:
    #     logging.info("\tExpandParenthesis next level.")
    #     ExpandParenthesis()    #recursive call itself to finish all.


def _ProcessOrBlock(Content, orIndex):
    if orIndex <= 0 or orIndex >= len(Content):
        raise Exception("Wrong orIndex:" + str(orIndex))
    if Content[orIndex] != '|':
        raise Exception("Wrong orIndex for Content:" + Content[orIndex])

    start = orIndex
    end = orIndex

    try:
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
    except Exception as e:
        logging.info("Failed to process or block because: " + str(e))
        return None, None, None
    return Content[start:end+1], Content[start:orIndex], Content[orIndex+1:end+1]


def _ExpandOrBlock(OneList):
    Modified = False
    #counter = 0
    for rule in OneList:
        if len(rule.RuleName) > 200:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + rule.RuleName)
            continue
        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            orIndex = token.word.find(")|")+1
            if orIndex <= 0:
                orIndex = token.word.find("|(")
                if orIndex <= 0:
                    continue

            originBlock, leftBlock, rightBlock = _ProcessOrBlock(token.word, orIndex)
            if originBlock is None:
                logging.error("ExpandOrBlock: Failed to process or block for: \n" + str(rule))
                continue    #failed to process. might be pair tag issue.

            #left:
            newrule = Rule()
            newrule.Origin = rule.Origin
            newrule.comment = rule.comment
            newrule.IsExpertLexicon = rule.IsExpertLexicon
            newrule.RuleName = rule.RuleName+"_o"+str(tokenindex)
            newrule.RuleContent = rule.RuleContent
            newrule.FileName = rule.FileName
            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
            #
            # newtoken = copy.copy(rule.Tokens[tokenindex])
            # newtoken.word = newtoken.word.replace(originBlock, leftBlock)
            # newrule.Tokens.append(newtoken)

            #Analyze the new word, might be a list of tokens.
            try:
                subTokenlist = Tokenize(token.word.replace(originBlock, leftBlock))
            except Exception as e:
                logging.error("Failed to tokenize because: " + str(e))
                logging.error("when expanding or block:" + leftBlock + " for rule name: " + rule.RuleName)
                continue
            if subTokenlist:
                ProcessTokens(subTokenlist)
                if hasattr(token, "pointer"):
                    subTokenlist[0].pointer = token.pointer
                subTokenlist[0].StartTrunk = token.StartTrunk
                subTokenlist[-1].EndTrunk = token.EndTrunk
                if hasattr(token, "action"):
                    if len(subTokenlist)>1:
                        logging.warning("The block has action before Or expand!")
                    subTokenlist[-1].action = token.action
            for subtoken in subTokenlist:
                newrule.Tokens.append(subtoken)

            for tokenindex_post in range(tokenindex+1, len(rule.Tokens)):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
            OneList.append(newrule)

            # right:
            newrule = Rule()
            newrule.Origin = rule.Origin
            newrule.comment = rule.comment
            newrule.IsExpertLexicon = rule.IsExpertLexicon
            newrule.RuleName = rule.RuleName + "_o" + str(tokenindex)
            newrule.RuleContent = rule.RuleContent
            newrule.FileName = rule.FileName
            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))

            # Analyze the new word, might be a list of tokens.
            try:
                subTokenlist = Tokenize(token.word.replace(originBlock, rightBlock))
            except Exception as e:
                logging.error("Failed to tokenize because: " + str(e))
                logging.error("when expanding or block:" + rightBlock + " for rule name: " + rule.RuleName)
                continue
            if subTokenlist:
                ProcessTokens(subTokenlist)
                if hasattr(token, "pointer"):
                    subTokenlist[0].pointer = token.pointer
                subTokenlist[0].StartTrunk = token.StartTrunk
                subTokenlist[-1].EndTrunk = token.EndTrunk
                if hasattr(token, "action"):
                    if len(subTokenlist) > 1:
                        logging.warning("The block has action before Or expand!")
                    subTokenlist[-1].action = token.action
            for subtoken in subTokenlist:
                newrule.Tokens.append(subtoken)

            for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
            OneList.append(newrule)

            Expand = True
            #logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
            break

        if Expand:
            OneList.remove(rule)
            Modified = True

    return Modified
    # if Modified:
    #     logging.info("\tExpandOrBlock next level.")
    #     ExpandOrBlock()    #recursive call itself to finish all.


#Check the rules. If it is a stem, not a feature, but omit quote
#   then we add quote;
# If it is like 'a|b|c', then we change it to 'a'|'b'|'c'
def PreProcess_CheckFeatures():
    for rule in _RuleList:
        for token in rule.Tokens:
            word = token.word
            if len(word) < 2:
                continue
            try:
                if word[0] == "[" and _SearchPair(word[1:], "[]") == len(word)-2:
                    word = word[1:-1]

                word, matchtype = LogicOperation_CheckPrefix(word, 'unknown')
            except Exception as e:
                logging.error("Error for rule:" + rule.RuleName)

            if matchtype == 'stem' :
                if "|" in word:
                    items = re.split("\|", word.lstrip("!"))
                    if word.startswith("!"):
                        token.word = "[!'" + "'|'".join(items) + "']"
                    else:
                        token.word = "['" + "'|'".join(items) + "']"
                elif " " in word:   #'this is a good': separate as multiple token.
                    logging.warning("The rule is: " + str(rule))
                    raise Exception("TODO: separate this as multiple token")

            elif matchtype == 'word':
                if "|" in word:
                    items = re.split("\|", word.lstrip("!"))
                    if word.startswith("!"):
                        token.word = "[!\"" + "\"|\"".join(items) + "\"]"
                    else:
                        token.word = "[\"" + "\"|\"".join(items) + "\"]"
                elif " " in word:  # 'this is a good': separate as multiple token.
                    raise Exception("TODO: separate this as multiple token")

            elif matchtype == 'unknown':
                if not re.search('\|| |!', word):
                    if FeatureOntology.GetFeatureID(word) == -1:
                        logging.warning("Will treat this word as a stem:" + word)
                        token.word = "['" + word + "']"
                elif "|" in word and " " not in word and "[" not in word:
                    # be aware of ['and|or|of|that|which'|PP|CM]
                    try:
                        if word.startswith("!"):
                            prefix = "!"
                            OrBlocks = LogicOperation_SeparateOrBlocks(word[1:])

                        else:
                            prefix = ""
                            OrBlocks = LogicOperation_SeparateOrBlocks(word)
                    except Exception as e:
                        logging.error("Error for rule:" + rule.RuleName)
                        continue    #not to process the rest.

                    token.word = prefix + "["
                    for OrBlock in OrBlocks:
                        _, mtype = LogicOperation_CheckPrefix(OrBlock, "unknown")
                        if mtype == "unknown" and OrBlock[0] != "!" and FeatureOntology.GetFeatureID(OrBlock) == -1:
                            logging.warning("Will treat this as a stem:" + OrBlock)
                            token.word += "'" + OrBlock + "'|"
                        else:
                            token.word += OrBlock + "|"
                    token.word = re.sub("\|$", "]", token.word)


def OutputRules(style="details"):
    print("// ****Rules****")
    print("// * size: " + str(len(_RuleList)) + " *" )
    for rule in  sorted(_RuleList, key=operator.attrgetter('RuleName')):
        print(rule.output(style))

    print("// ****Expert Lexicons****")
    print("// * size: " + str(len(_ExpertLexicon)) + " *" )
    for rule in _ExpertLexicon:
        print(rule.output(style))

    print ("// ****Macros****")
    print("// * size: " + str(len(_MacroDict)) + " *" )
    for rule in _MacroDict.values():
        print(rule.output(style))

    print("// End of Rules/Expert Lexicons/Macros")


# def BuildRuleUnitTest():
#     testLocation = rule.comment.find("test:")
#     if testLocation < 0:
#         testLocation = rule.comment.find("TEST:")
#     if testLocation >= 0:
#         TestSentence = rule.comment[testLocation + 5:].strip()
#         if Tokenization == "":
#             continue


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')

    #LoadRules("../../fsa/Y/900NPy.xml")
    #LoadRules("../../fsa/Y/800VGy.txt")
    #LoadRules("../../fsa/Y/1800VPy.xml")

    #BuildRuleUnitTest() #Do this before the expansion.

    LoadRules("../../fsa/Y/1test_rules.txt")

    ExpandRuleWildCard()
    ExpandParenthesisAndOrBlock()
    ExpandRuleWildCard()
    PreProcess_CheckFeatures()

    OutputRules("concise")
    FeatureOntology.PrintMissingFeatureSet()