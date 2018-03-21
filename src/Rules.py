
import copy
from datetime import datetime
from utils import *

# import FeatureOntology
# usage: to output rules list, run:
#       python Rules.py > rules.txt

from LogicOperation import CheckPrefix as LogicOperation_CheckPrefix
from LogicOperation import SeparateOrBlocks as LogicOperation_SeparateOrBlocks
import FeatureOntology

RuleGroupDict = {}


class RuleGroup(object):
    idCounter = 0
    def __init__(self, FileName):
        Rule.idCounter += 1
        self.ID = Rule.idCounter
        self.FileName = FileName
        self.RuleList = []
        self.MacroDict = {}
        self.UnitTest = []
        self.LoadedFromDB = False

    def __lt__(self, other):
        return self.ID < other.ID


class UnitTestNode(object):
    # def __init__(self):
    #     self.FileName = ''
    #     self.RuleName = ''
    #     self.TestSentence = ''

    def __init__(self, RuleName, TestTentence):
        self.RuleName = RuleName
        self.TestSentence = TestTentence


def ResetRules(rg):
    del rg.RuleList[:]
    rg.MacroDict = {}  # not sure which one to use yet


# If it is one line, that it is one rule;
# if it has several lines in {} or () block, then it is one rule;
# otherwise (it has multiple lines but not in one block), process the first line,
# return the rest as "remaining"
def SeparateRules(multilineString):
    lines = re.split("\n", multilineString)
    if len(lines) == 1:
        return multilineString, None

    # Move the comment after ";" sign into the first line.
    newlines = []
    for line in lines:
        newline = line.strip()
        if not newline:
            continue
        if newline.startswith("//"):
            if len(newlines) > 0:
                newlines[0] += line
            else:
                newlines.append(newline)
        else:
            newlines.append(newline)

    endlineMatch = re.match("(.*;)\s*(//.*)", newlines[-1])
    if endlineMatch and endlineMatch.lastindex == 2:
        newlines[-1] = endlineMatch[1]
        newlines[0] += endlineMatch[2]

    newString = "\n".join(newlines)

    if newString[0] == "(" and SearchPair(newString[1:], "()") >= len(newString) - 3:  # sometimes there is ";" sign
        return newString, None
    if newString[0] == "{" and SearchPair(newString[1:], "{}") >= len(newString) - 3:
        return newString, None
    if newString[0] == "<" and SearchPair(newString[1:], "<>") >= len(newString) - 3:
        return newString, None
    return lines[0], "\n".join(lines[1:])


class RuleToken(object):
    def __init__(self):
        self.StartChunk = 0
        self.EndChunk = 0
        self.repeat = [1,1]
        self.word = ''
        self.RestartPoint = False
        self.MatchType = -1     #-1:unknown/mixed 0: feature 1:text 2:norm 3:atom
        self.pointer = ''
        self.action = ''
        self.SubtreePointer = ''

    def __str__(self):
        output = ""
        for _ in range(self.StartChunk):
            output += "<"
        output += self.pointer
        t = self.word
        if self.action:
            t = t.replace("]", "ACTION" + self.action + "]")
        output += t
        if self.repeat != [1, 1]:
            output += "*" + str(self.repeat[1])
        for _ in range(self.EndChunk):
            output += ">"
        output += " "  # should be a space. use _ in dev mode.
        return output

class RuleChunk(object):
    def __init__(self):
        self.StartOffset = -1
        self.Length = 0             # how many rule tokens;
        self.StringChunkLength = 0  # how many string tokens this chunk apply to
        self.HeadOffset = -1
        self.HeadConfidence = -1
        self.Action = ''
        self.ChunkLevel = 1


class Rule:
    idCounter = 0
    def __init__(self):
        Rule.idCounter += 1
        self.ID = Rule.idCounter
        self.FileName = ''
        self.RuleName = ''
        self.Origin = ''
        self.RuleContent = ''
        self.Tokens = []
        self.StrTokenLength = -1
        self.Chunks = []
        self.comment = ''
        self.norms = []

    def SetStrTokenLength(self):
        VirtualTokenNum = 0  #Those "^V=xxx" is virtual token that does not apply to real string token
        for t in self.Tokens:
            if t.SubtreePointer:
                VirtualTokenNum += 1
        self.StrTokenLength = len(self.Tokens) - VirtualTokenNum

    def __lt__(self, other):
        return (self.FileName, self.Origin, self.ID) < (other.FileName, other.Origin, other.ID)

    def SetRule(self, ruleString, MacroDict=None, ID=1):
        self.Origin = ruleString.strip()
        code, comment = SeparateComment(ruleString)
        if not code:
            return
        codeblocks = [x.strip() for x in re.split("::", code)]
        if len(codeblocks) != 2:
            codeblocks = [x.strip() for x in code.split("==", 2)]
            if len(codeblocks) != 2:
                logging.debug(" not separated by :: or == ")
                logging.debug("string:" + ruleString)
                return

        RuleBlocks = re.match("(.+)==(.+)$", ruleString, re.DOTALL)
        if not RuleBlocks:
            RuleBlocks = re.match("(.+)::(.+)$", ruleString, re.DOTALL)
        if not RuleBlocks or RuleBlocks.lastindex != 2:
            raise RuntimeError("This rule can't be correctly parsed:\n\t" + ruleString)

        if ID != 1:
            self.ID = ID
        self.RuleName = RuleBlocks.group(1).strip()
        if self.RuleName.startswith("@") or self.RuleName.startswith("#"):
            RuleContent = ProcessMacro(codeblocks[1],
                                       MacroDict)  # Process the whole code, not to worry about comment and unit test
            if code.endswith(";"):
                RuleContent = RuleContent[:-1]
            self.RuleContent = RuleContent
            self.comment = comment
            return  # stop processing macro.

        remaining = ''
        try:
            RuleContent, remaining = SeparateRules(RuleBlocks.group(2).strip())
            if remaining:
                self.Origin = self.Origin.replace(remaining, '').strip()
            RuleCode, self.comment = SeparateComment(RuleContent)
            if not RuleCode:
                self.RuleContent = ""
                if self.comment:
                    if remaining:
                        remaining += self.comment
                    else:
                        remaining = self.comment
                return remaining  # stop processing if the RuleCode is null

            self.RuleContent = ProcessMacro(RuleCode, MacroDict)

            self.Tokens = Tokenize(self.RuleContent)
        except Exception as e:
            logging.error("Failed to setrule because: " + str(e))
            logging.error("Rulename is: " + self.RuleName)
            self.RuleName = ""
            self.RuleContent = ""
            return remaining
        ProcessTokens(self.Tokens)

        if self.Tokens[0].StartChunk:
            UniversalToken = RuleToken()
            UniversalToken.word = '[]'    #make it universal
            self.Tokens = [UniversalToken] + self.Tokens

        self.SetStrTokenLength()
        return remaining

    def __str__(self):
        return self.output("details")

    # def oneliner(self):
    #     return self.output("concise")

    # style: concise, or detail
    def output(self, style="concise"):
        output = "//ID:" + str(self.ID)
        if self.RuleName.startswith("@"):
            output += "[Macro]\n"
        elif self.RuleName.startswith("#"):
            output += "[Macro with parameter]\n"
        else:
            output += "[Rule]\n"

        if style == "concise":
            output += self.RuleName + " == {"

            if len(self.Tokens) == 0:
                output += self.RuleContent
        else:
            output += "[RuleName]=" + self.RuleName + '\n'
            output += "\t[Origin Content]=\n" + self.RuleContent + '\n'
            output += "\t[Compiled Content]=\n{"
        for token in self.Tokens:
            output += str(token)
        output += "};"

        if self.Chunks:
            output += "\n//" + jsonpickle.dumps(self.Chunks)

        if style != "concise":
            if self.comment:
                output += " " + self.comment

        output += '\n'
        return output

    # body is the part that being used to identify this specific rule. It is also that part to match the rule.
    def body(self):
        return "".join(t.word for t in self.Tokens)

    # if there is same body of rule in db (for the same rulefileid), then use the same rule id, remove the existing rulenodes and rulechunks for it. create new ones;
    #    update the verifytime, and status.
    # if there is no same body, create everything.
    def DBSave(self, rulefileid):
        cur = DBCon.cursor()
        strsql = "SELECT ID from ruleinfo where rulefileid=? AND body=?  limit 1"
        cur.execute(strsql, [rulefileid, self.body()])
        resultrecord = cur.fetchone()
        if resultrecord:
            resultid = resultrecord[0]
            strsql = "UPDATE ruleinfo set status=1, verifytime=DATETIME('now') where ID=?"
            cur.execute(strsql, [resultid,])
            strsql = "DELETE from rulenodes where ruleid=?"
            cur.execute(strsql, [resultid, ])
            strsql = "DELETE from rulechunks where ruleid=?"
            cur.execute(strsql, [resultid, ])
        else:
            strsql = "INSERT into ruleinfo (rulefileid, name, body, strtokenlength, tokenlength, status, norms, comment, createtime, verifytime) " \
                            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"
            cur.execute(strsql, [rulefileid, self.RuleName, self.body(), self.StrTokenLength, len(self.Tokens), 1, '/'.join([x.replace("/", IMPOSSIBLESTRINGSLASH) if x else '' for x in self.norms]), self.comment])
            resultid = cur.lastrowid

        for i in range(len(self.Tokens)):
            strsql = "INSERT into rulenodes (ruleid, sequence, matchbody, action, pointer, subtreepointer) values(?, ?, ?, ?, ?, ?)"
            cur.execute(strsql, [resultid, i, self.Tokens[i].word, self.Tokens[i].action, self.Tokens[i].pointer, self.Tokens[i].SubtreePointer])
        for i in range(len(self.Chunks)):
            strsql = "INSERT into rulechunks (ruleid, chunklevel, startoffset, length, stringchunklength, headoffset, action) values(?, ?, ?, ?, ?, ?, ?)"
            cur.execute(strsql, [resultid, self.Chunks[i].ChunkLevel, self.Chunks[i].StartOffset,
                                 self.Chunks[i].Length, self.Chunks[i].StringChunkLength,
                                 self.Chunks[i].HeadOffset, self.Chunks[i].Action
                                 ])
        cur.close()
        return resultid


    #For head (son) node, only apply negative action, and
    #   features after "NEW".
    # update on Feb 4: Only "X++" is for new node. The rest is for Son
    @staticmethod
    def ExtractParentSonActions( actinstring):

        if "+++" in actinstring:    # if there is +++, then all are parentaction.
            return actinstring, ""

        actions = set(actinstring.split())

        #SonActionString = " ".join([a for a in actions if a[-2:] != "++"   or a == '+++' ])
        ParentActions = [a for a in actions if a[-2:] == "++" and a != '+++']
        ParentActions.extend( [a for a in actions if a[0:2] == "^^"]        )

        SonActions = list(actions - set(ParentActions))

        return " ".join(sorted(ParentActions)), " ".join(sorted(SonActions))


    def CompileChunk(self):
        rulebody = ''
        for token in self.Tokens:
            rulebody += str(token)

        if rulebody.count('<') > 4 :
            logging.warning("This rule has more than 4 chunks:")
            logging.warning(rulebody)

        # TODO: leave these 3 for future usage.
        Chunk2_3_1 = re.match("(.*)<(.*)<(.+)>(.*)<(.+)>(.*)<(.+)>(.*)>(.*)", rulebody)
        # Chunk2_3_2 = re.match("(.*)<(.*)<(.+)>(.*)<(.+)>(.*)>(.*)<(.+)>(.*)", rulebody)
        # Chunk2_3_3 = re.match("(.*)<(.+)>(.*)<(.*)<(.+)>(.*)<(.+)>(.*)>(.*)", rulebody)

        Chunk2_2 = re.match("(.*)<(.*)<(.+)>(.*)<(.+)>(.*)>(.*)", rulebody)
        Chunk2_1 = re.match("(.*)<(.*)<(.+)>(.*)>(.*)", rulebody)
        Chunk1_3 = re.match("(.*)<(.+)>(.*)<(.+)>(.*)<(.+)>(.*)", rulebody)
        Chunk1_2 = re.match("(.*)<(.+)>(.*)<(.+)>(.*)", rulebody)
        Chunk1_1 = re.match("(.*)<(.+)>(.*)", rulebody)

        if Chunk2_3_1:
            tokencount_1 = Chunk2_3_1.group(1).count('[')
            tokencount_2 = Chunk2_3_1.group(2).count('[')
            tokencount_3 = Chunk2_3_1.group(3).count('[')
            tokencount_4 = Chunk2_3_1.group(4).count('[')
            tokencount_5 = Chunk2_3_1.group(5).count('[')
            tokencount_6 = Chunk2_3_1.group(6).count('[')
            tokencount_7 = Chunk2_3_1.group(7).count('[')
            tokencount_8 = Chunk2_3_1.group(8).count('[')
            c1 = self.CreateChunk(tokencount_1 + tokencount_2, tokencount_3)
            self.Chunks.append(c1)
            c2 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3 + tokencount_4, tokencount_5)
            self.Chunks.append(c2)
            c3 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5 + tokencount_6, tokencount_7)
            self.Chunks.append(c3)

            c = RuleChunk()
            c.ChunkLevel = 2
            c.StartOffset = tokencount_1
            c.Length = tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6 + 1 + tokencount_8
            # check the part before first inner chuck.
            VirtualTokenNum = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2,
                                                                     HeadOffset=0)
            # check the part after first inner chuck, before second inner chuck.
            VirtualTokenNum += self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                                      Length=tokencount_4,
                                                                      HeadOffset=tokencount_2 + 1)
            # check the part after second inner chuck.
            VirtualTokenNum += self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5,
                                                                      Length=tokencount_6,
                                                                      HeadOffset=tokencount_2 + 1 + tokencount_4 + 1)
            # check the part after third inner chuck.
            VirtualTokenNum += self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5 + tokencount_6 + tokencount_7,
                                                                      Length=tokencount_8,
                                                                      HeadOffset=tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6 + 1)

            if c.HeadOffset == -1:
                c.HeadConfidence = 1
                if   "++" in c1.Action or ("^^." in c2.Action and "^^." in c3.Action ):
                    c.HeadOffset = tokencount_2
                elif "++" in c2.Action or ("^^." in c1.Action and "^^." in c3.Action ):
                    c.HeadOffset = tokencount_2 + 1 + tokencount_4
                elif "++" in c3.Action or ("^^." in c1.Action and "^^." in c2.Action ):
                    c.HeadOffset = tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6
                else:
                    logging.error(" There is no ++ for anyt tokens.  Can't determined the head!")
                    logging.error(str(self))
                    logging.error(jsonpickle.dumps(c))

            c.StringChunkLength = c.Length - VirtualTokenNum

            self.Chunks.append(c)
        elif Chunk2_2:
            tokencount_1 = Chunk2_2.group(1).count('[')
            tokencount_2 = Chunk2_2.group(2).count('[')
            tokencount_3 = Chunk2_2.group(3).count('[')
            tokencount_4 = Chunk2_2.group(4).count('[')
            tokencount_5 = Chunk2_2.group(5).count('[')
            tokencount_6 = Chunk2_2.group(6).count('[')
            c1 = self.CreateChunk(tokencount_1+tokencount_2, tokencount_3)
            self.Chunks.append(c1)
            c2 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3 + tokencount_4 , tokencount_5)
            self.Chunks.append(c2)

            c = RuleChunk()
            c.ChunkLevel = 2
            c.StartOffset = tokencount_1
            c.Length = tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6

            #check the part before first inner chuck.
            VirtualTokenNum = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2, HeadOffset=0)

            #check the part after first inner chuck, before second inner chuck.
            VirtualTokenNum += self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset + tokencount_2 + tokencount_3, Length=tokencount_4, HeadOffset=tokencount_2 + 1)

            #check the part after second inner chuck.
            VirtualTokenNum += self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5, Length=tokencount_6, HeadOffset = tokencount_2 + 1 + tokencount_4 + 1)

            if c.HeadOffset == -1:
                c.HeadConfidence = 1
                if   "^^." in c2.Action or "++" in c1.Action:
                    c.HeadOffset = tokencount_2
                elif "^^." in c1.Action or "++" in c2.Action:
                    c.HeadOffset = tokencount_2 + 1 + tokencount_4
                else:
                    logging.error(" There is no ^^. or ++ for both tokens.  Can't determined the head!")
                    logging.error(str(self))
                    logging.error(jsonpickle.dumps(c))

            c.StringChunkLength = c.Length - VirtualTokenNum

            self.Chunks.append(c)
        elif Chunk2_1:
            tokencount_1 = Chunk2_1.group(1).count('[')
            tokencount_2 = Chunk2_1.group(2).count('[')
            tokencount_3 = Chunk2_1.group(3).count('[')
            tokencount_4 = Chunk2_1.group(4).count('[')
            c1 = self.CreateChunk(tokencount_1+tokencount_2, tokencount_3)
            self.Chunks.append(c1)

            c = RuleChunk()
            c.ChunkLevel = 2
            c.StartOffset = tokencount_1
            c.Length = tokencount_2 + 1 + tokencount_4

            #check the part before inner chuck.
            VirtualTokenNum = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2, HeadOffset=0)

            #check the part after inner chuck.
            VirtualTokenNum += self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset + tokencount_2 + tokencount_3, Length=tokencount_4, HeadOffset=tokencount_2 + 1)

            if c.HeadOffset == -1:
                c.HeadConfidence = 1
                c.HeadOffset = tokencount_2
                if "^^." not in c1.Action and "++" not in c1.Action:
                    c.HeadConfidence = 0
                    logging.debug("Can't find head in scattered tokens. must be the inner chuck, but it does not have ^^ or ++.")
                    logging.debug(str(self))
                    logging.debug(jsonpickle.dumps(c))

            c.StringChunkLength = c.Length - VirtualTokenNum
            self.Chunks.append(c)

        elif Chunk1_3:
            tokencount_1 = Chunk1_3.group(1).count('[')
            tokencount_2 = Chunk1_3.group(2).count('[')
            c1 = self.CreateChunk(tokencount_1, tokencount_2)
            self.Chunks.append(c1)

            tokencount_3 = Chunk1_3.group(3).count('[')
            tokencount_4 = Chunk1_3.group(4).count('[')
            c2 = self.CreateChunk(tokencount_1+tokencount_2+tokencount_3, tokencount_4)
            self.Chunks.append(c2)

            tokencount_5 = Chunk1_3.group(5).count('[')
            tokencount_6 = Chunk1_3.group(6).count('[')
            c3 = self.CreateChunk(tokencount_1+tokencount_2+tokencount_3+tokencount_4+tokencount_5, tokencount_6)
            self.Chunks.append(c3)

        elif Chunk1_2:
            tokencount_1 = Chunk1_2.group(1).count('[')
            tokencount_2 = Chunk1_2.group(2).count('[')
            c1 = self.CreateChunk(tokencount_1, tokencount_2)
            self.Chunks.append(c1)

            tokencount_3 = Chunk1_2.group(3).count('[')
            tokencount_4 = Chunk1_2.group(4).count('[')
            c2 = self.CreateChunk(tokencount_1+tokencount_2+tokencount_3, tokencount_4)
            self.Chunks.append(c2)

        elif Chunk1_1:
            prefix = Chunk1_1.group(1)
            tokencount_prefix = prefix.count('[')

            inside = Chunk1_1.group(2)
            tokencount_inside = inside.count('[')

            c = self.CreateChunk(tokencount_prefix, tokencount_inside)
            self.Chunks.append(c)

        else:
            logging.debug("There is no chunk in this rule.")

        # sort backward for applying
        self.Chunks.sort(key=lambda x: x.StartOffset, reverse=True)


    def CheckTokensForHeadAndVirtualToken(self, c, StartOffset, Length, HeadOffset = 0):

        VirtualTokenNum = 0  # Those "^V=xxx" is virtual token that does not apply to real string token
        for i in range(Length):
            token = self.Tokens[StartOffset + i]
            if token.SubtreePointer:
                VirtualTokenNum += 1

            if "H" in token.action.split():
                c.HeadConfidence = 5
                c.HeadOffset = HeadOffset + i
                c.Action, token.action = self.ExtractParentSonActions(token.action)
                token.action += " ^.H"
            elif token.pointer == "^H":
                if c.HeadConfidence < 5:
                    c.HeadConfidence = 4
                    c.HeadOffset = HeadOffset + i
                    c.Action, token.action = self.ExtractParentSonActions(token.action)
            elif  "^^." in token.action or "++" in token.action:
                if c.HeadConfidence < 4:
                    c.HeadConfidence = 3
                    c.HeadOffset = HeadOffset + i
                    c.Action, token.action = self.ExtractParentSonActions(token.action)
            elif not token.action:
                if c.HeadConfidence < 3:
                    c.HeadConfidence = 2
                    c.HeadOffset = HeadOffset + i
                    c.Action, token.action = self.ExtractParentSonActions(token.action)
            elif "^." not in token.action:
                if c.HeadConfidence < 2:
                    c.HeadConfidence = HeadOffset + 1
                    c.HeadOffset = i
                    c.Action, token.action = self.ExtractParentSonActions(token.action)

        return VirtualTokenNum


    def CreateChunk(self, StartOffset, Length, ChunkLevel = 1):
        c = RuleChunk()
        c.StartOffset = StartOffset
        c.Length = Length
        VirtualTokenNum = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset,
                           Length=Length, HeadOffset=0)

        if c.HeadOffset == -1:
            logging.warning("Can't find head in this rule:")
            logging.warning(self.Origin)
            logging.warning(str(self))

        c.StringChunkLength = c.Length - VirtualTokenNum
        c.ChunkLevel = ChunkLevel
        return c


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
                node = RuleToken()
                node.word = RuleContent[StartPosition:EndOfToken]
                TokenList.append(node)
                # i = EndOfToken
                if i == len(RuleContent):
                    break
        else:
            if not StartToken:
                StartToken = True
                StartPosition = i

        for pair in Pairs:
            if RuleContent[i] == pair[0] and (i == 0 or RuleContent[i - 1] != "\\"):  # escape:
                # StartPosition = i
                end = SearchPair(RuleContent[i + 1:], pair)
                if end >= 0:
                    StartToken = False
                    EndOfToken = i + 2 + end + SearchToEnd(RuleContent[i + 1 + end + 1:])
                    node = RuleToken()
                    node.word = RuleContent[StartPosition:EndOfToken + 1]
                    TokenList.append(node)
                    i = EndOfToken
                    break
                else:
                    logging.error("Can't find paired content in rule")
                    logging.error(RuleContent)
                    raise RuntimeError("rule compilation error")

        i += 1

    if StartToken:  # wrap up the last one
        EndOfToken = i
        node = RuleToken()
        node.word = RuleContent[StartPosition:EndOfToken]
        TokenList.append(node)

    return TokenList


def ProcessTokens(Tokens):
    for node in Tokens:
        node.word = node.word.replace("\\(", IMPOSSIBLESTRINGLP).replace("\\)", IMPOSSIBLESTRINGRP).replace("\\'", IMPOSSIBLESTRINGSQ).replace("\\:", IMPOSSIBLESTRINGCOLN).replace("\\=", IMPOSSIBLESTRINGEQUAL)
        # logging.info("\tnode word:" + node.word)
        while node.word.startswith("<"):
            node.word = node.word[1:]
            node.StartChunk += 1

        while node.word.endswith(">"):
            node.word = node.word[:-1]
            node.EndChunk += 1

        if node.word.startswith("`"):
            node.word = node.word.lstrip("`")
            node.RestartPoint = True

        if node.word.endswith("?"):
            node.word = node.word.rstrip("?")
            node.repeat = [0, 1]
        if node.word.endswith("*"):
            node.word = node.word.rstrip("*")
            node.repeat = [0, 3]

        repeatMatch = re.match("(.*[\]\"')])(\d+)\*(\d+)$", node.word, re.DOTALL)
        if repeatMatch:
            node.word = repeatMatch.group(1)
            node.repeat = [int(repeatMatch.group(2)), int(repeatMatch.group(3))]

        repeatMatch = re.match("(.+)\*(\d*)$", node.word, re.DOTALL)
        if not repeatMatch:
            repeatMatch = re.match("(.*[\])\"'])(\d+)$", node.word, re.DOTALL)
        if repeatMatch:
            node.word = repeatMatch.group(1)
            repeatMax = 3  # default as 3
            if repeatMatch.group(2):
                repeatMax = int(repeatMatch.group(2))
            node.repeat = [0, repeatMax]

        pointerMatch = re.match("(\^\w*)\[(.*)\]$", node.word, re.DOTALL)
        if pointerMatch:
            node.word = "[" + pointerMatch.group(2) + "]"
            node.pointer = pointerMatch.group(1)

        pointerMatch = re.match("\^(.+)$", node.word, re.DOTALL)
        if pointerMatch:
            logging.error("Unknown situation. Pointer not in right place:")
            logging.error(node.word)
            node.word = "[" + pointerMatch.group(1) + "]"
            node.pointer = '^'

        pointerSubtreeMatch = re.search("\[(\^(.+)=)", node.word, re.DOTALL)    # Subtree Pattern
        if pointerSubtreeMatch:
            node.word = node.word.replace(pointerSubtreeMatch.group(1), "")
            node.SubtreePointer = pointerSubtreeMatch.group(2)

        pointerSubtreeMatch = re.search("\[(\^(.+) )", node.word, re.DOTALL)    # Subtree Pattern
        if pointerSubtreeMatch:
            node.word = node.word.replace(pointerSubtreeMatch.group(1), "")
            node.SubtreePointer = pointerSubtreeMatch.group(2)

        if "(" not in node.word and ":" in node.word:
            orblocks = re.split("\|\[", node.word)
            if len(orblocks) > 1:
                node.word = "(" + ")|([".join(orblocks) + ")"  # will be tokenize later.
            else:
                orblocks = re.split("\]\|", node.word)
                if len(orblocks) > 1:
                    node.word = "(" + "])|(".join(orblocks) + ")"  # will be tokenize later.
                else:  # no "()" sign, and no "|" sign
                    # using (.*):, not (.+): , because the word can be blank (means matching everything)
                    actionMatch = re.match("\[(.*):(.+)\]$", node.word, re.DOTALL)
                    if actionMatch:
                        node.word = "[" + actionMatch.group(1) + "]"
                        node.action = actionMatch.group(2)

        if "(" in node.word and ":" in node.word:
            ActionPosition = node.word.find(":")

            if ")" not in node.word[ActionPosition:] and "[" not in node.word[ActionPosition:]:
                logging.info("separate action")
                node.action = node.word[ActionPosition+1:].rstrip("]")
                node.word = node.word[:ActionPosition] + "]"

        if node.word[0] == '[' and ChinesePattern.match(node.word[1]):
            node.word = '[FULLSTRING ' + node.word[1:]   #If Chinese character is not surrounded by quote, then add feature 0.

        node.word = node.word.replace(IMPOSSIBLESTRINGLP, "(").replace(IMPOSSIBLESTRINGRP, ")").replace(IMPOSSIBLESTRINGSQ, "'").replace(IMPOSSIBLESTRINGCOLN, ":").replace(IMPOSSIBLESTRINGEQUAL, "=")
        node.action = node.action.replace(IMPOSSIBLESTRINGLP, "(").replace(IMPOSSIBLESTRINGRP, ")").replace(IMPOSSIBLESTRINGSQ, "'").replace(IMPOSSIBLESTRINGCOLN, ":").replace(IMPOSSIBLESTRINGEQUAL, "=")

# Avoid [(AS:action)|sjfa]
# Good character in action:
#     ^.M $
# Bad characters in action:
#     )?':
def FindLastColonWithoutSpecialCharacter(string):
    index = len(string) - 2
    while index >= 0:
        if string[index] == ":":
            return index
        if string[index].isalnum() or \
                        string[index] in "^. $,>+-":
            index -= 1
        else:
            #            logging.warning("not a ligit action: " + string[index] + " in " + string )
            return -1
    return -1


# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or any non-alnum (\W)
def _SearchToEnd_OrBlock(string, Reverse=False):
    if not string:  # if it is empty
        return 0
    if Reverse:
        i = len(string) - 1
        targetTagIndex = 1
        direction = -1
    else:
        i = 0
        targetTagIndex = 0
        direction = 1
    while 0 <= i < len(string):
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                if i > 0 and string[i - 1] == "|":
                    endofpair = SearchPair(string[i + 1:], pair, Reverse)
                    if endofpair >= 0:
                        if Reverse:
                            i -= endofpair + 1
                        else:
                            i += endofpair + 1
                    else:
                        raise RuntimeError("Can't find a pair in _SearchToEnd()")
                        # return 0   # error. stop the searching immediately.
        if re.match("\W", string[i]):
            return i - direction
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                return i - direction
        i += direction

    if i < 0:
        i = 0
    return i


def ProcessMacro(ruleContent, MacroDict):
    macros_with_parameters = re.findall("#\w*\(.+\)", ruleContent)
    for macro in macros_with_parameters:
        macroName = re.match("^(#.*)\(", macro).group(0)
        for MacroName in MacroDict:
            if MacroName.startswith(macroName):
                MacroParameters = re.findall("(\d+)=(\$\w+)", MacroName)
                macroParameters = re.findall("(\d+)=?([^,\d)]*)?", macro)
                macroContent = MacroDict[MacroName].RuleContent
                for Parameter_Pair in MacroParameters:
                    for parameter_pair in macroParameters:
                        if Parameter_Pair[0] == parameter_pair[0]:
                            if len(parameter_pair) == 1 or parameter_pair[1] == "NULL":
                                ReplaceWith = ''
                            else:
                                ReplaceWith = parameter_pair[1].strip()
                            macroContent = macroContent.replace(Parameter_Pair[1], ReplaceWith)
                ruleContent = ruleContent.replace(macro, macroContent)
    # return ruleContent

    macros = re.findall("@\w*", ruleContent)
    for macro in sorted(macros, key=lambda x: len(x), reverse=True):
        if macro in MacroDict:
            ruleContent = ruleContent.replace(macro, MacroDict[macro].RuleContent)
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
# -Sept, change to : until the next "==" or "::" is found, give the whole block to "InsetRuleInList"
#   The rule.SetRule() will judge whether it is one whole rule (base on {}), or several rules (or condition),
#       when it will process current rule, and give the rest as "remaining" for next round.
def LoadRules(RuleLocation):
    # global UnitTest, RuleFileList
    global RuleGroupDict

    if RuleLocation.startswith("."):
        RuleLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  RuleLocation)

    RuleFileName = os.path.basename(RuleLocation)
    logging.debug("Start Loading Rule " + RuleFileName)
    rulegroup = RuleGroup(RuleFileName)

    if RuleFileOlderThanDB(RuleLocation):
        rulegroup.LoadedFromDB = True
        LoadRulesFromDB(rulegroup)
    else:
        rulegroup.LoadedFromDB = False
        rule = ""
        try:
            with open(RuleLocation, encoding="utf-8") as RuleFile:
                for line in RuleFile:
                    # commentLocation = line.find("//")
                    # if commentLocation>=0:
                    #     line = line[:commentLocation]   #remove anything after //

                    line = line.strip().replace("：", ":")
                    if not line:
                        continue

                    code, _ = SeparateComment(line)
                    if code.find("::") >= 0 or code.find("==") >= 0:
                        if rule:
                            InsertRuleInList(rule, rulegroup)
                            rule = ""
                    rule += "\n" + line

                if rule:
                    InsertRuleInList(rule, rulegroup)
        except UnicodeError :
            logging.error("Error when processing " + RuleFileName)
            logging.error("Currently rule=" + rule)
        UnitTestFileName = os.path.splitext(RuleLocation)[0] + ".unittest"
        if os.path.exists(UnitTestFileName):
            # First delete the unit test of current file to have clean plate
            del rulegroup.UnitTest[:]
            with open(UnitTestFileName, encoding="utf-8") as RuleFile:
                for line in RuleFile:
                    RuleName, TestSentence = SeparateComment(line)
                    unittest = UnitTestNode(RuleName, TestSentence.strip("//"))
                    rulegroup.UnitTest.append(unittest)

    RuleGroupDict.update({rulegroup.FileName: rulegroup})
    logging.info("Finished Loading Rule " + RuleFileName + " LoadedFromDB:" + str(rulegroup.LoadedFromDB) )
    logging.info("\t Rule Size:" + str(len(rulegroup.RuleList)) )


def RuleFileOlderThanDB(RuleLocation):
    return False
    cur = DBCon.cursor()
    RuleFileName = os.path.basename(RuleLocation)
    strsql = "select ID, verifytime from rulefiles where filelocation=?"
    cur.execute(strsql, [RuleFileName,])
    resultrecord = cur.fetchone()
    cur.close()

    if not resultrecord or not resultrecord[1]:
        return False

    FileDBTime = resultrecord[1]    #utc time.
    FileDiskTime = datetime.utcfromtimestamp(os.path.getmtime(RuleLocation)).strftime('%Y-%m-%d %H:%M:%S')

    logging.info("Disk:" + str(FileDiskTime + "  DB:" + str(FileDBTime)))
    return FileDiskTime < FileDBTime

    # strsql = "f(rulefileid, comment, body, status, norms, createtime, verifytime) VALUES(?, ?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"
    # cur.execute(strsql, [rulefileid, self.comment, self.body(), 1, '/'.join([x if x else '' for x in self.norms])])
    # resultid = cur.lastrowid
    # for i in range(len(self.Tokens)):
    #     strsql = "INSERT into rulenodes (ruleid, sequence, matchbody, action) values(?, ?, ?, ?)"
    #     cur.execute(strsql, [resultid, i, self.Tokens[i].word, self.Tokens[i].action])
    # for i in range(len(self.Chunks)):
    #     strsql = "INSERT into rulechunks (ruleid, chunklevel, startoffset, length, stringchunklength, headoffset, action) values(?, ?, ?, ?, ?, ?, ?)"
    #     cur.execute(strsql, [resultid, self.Chunks[i].ChunkLevel, self.Chunks[i].StartOffset,
    #                          self.Chunks[i].Length, self.Chunks[i].StringChunkLength,
    #                          self.Chunks[i].HeadOffset, self.Chunks[i].Action
    #                          ])


def LoadRulesFromDB(rulegroup):
    cur = DBCon.cursor()
    strsql = "select ID from rulefiles where filelocation=?"
    cur.execute(strsql, [rulegroup.FileName,])
    resultrecord = cur.fetchone()
    if not resultrecord:
        logging.error("Trying to load rules from DB for :" + rulegroup.FileName)
        return False
    rulefileid = resultrecord[0]

    #order by tokenlength desc, and by hits desc.
    strsql = "SELECT id, name, strtokenlength, norms, comment from ruleinfo where rulefileid=? order by tokenlength desc"
    cur.execute(strsql, [rulefileid, ])
    rows = cur.fetchall()
    for row in rows:
        rule = Rule()
        rule.FileName = rulegroup.FileName
        rule.ID = int(row[0])
        rule.RuleName = row[1]
        rule.StrTokenLength = int(row[2])
        rule.norms = [x.replace(IMPOSSIBLESTRINGSLASH, "/") if x else None for x in row[3].split("/")]
        rule.comment = row[4]

        strsql = "SELECT matchbody, action, pointer, subtreepointer from rulenodes where ruleid=? order by sequence"
        cur.execute(strsql, [rule.ID,])
        noderows = cur.fetchall()
        for noderow in noderows:
            token = RuleToken()
            token.word = noderow[0]
            token.action = noderow[1]
            token.pointer = noderow[2]
            token.SubtreePointer = noderow[3]
            rule.Tokens.append(token)

        strsql = "SELECT chunklevel, startoffset, length, stringchunklength, headoffset, action from rulechunks where ruleid=? "
        cur.execute(strsql, [rule.ID,])
        chunkrows = cur.fetchall()
        for chunkrow in chunkrows:
            chunk = RuleChunk()
            chunk.ChunkLevel = int(chunkrow[0])
            chunk.StartOffset = int(chunkrow[1])
            chunk.Length = int(chunkrow[2])
            chunk.StringChunkLength = int(chunkrow[3])
            chunk.HeadOffset = int(chunkrow[4])
            chunk.Action = chunkrow[5]
            rule.Chunks.append(chunk)

        rulegroup.RuleList.append(rule)


    strsql = "update rulefiles set verifytime=DATETIME('now') where filelocation=?"
    cur.execute(strsql, [rulegroup.FileName,])
    rulegroup.LoadedFromDB = True
    cur.close()
    return True


def InsertRuleInList(string, rulegroup):
    node = Rule()
    node.FileName = rulegroup.FileName  #used in keeping record of the winning rules.
    remaining = node.SetRule(string, rulegroup.MacroDict)
    if node.RuleContent:
        if node.RuleName.startswith("@") or node.RuleName.startswith("#"):
            if node.RuleName in rulegroup.MacroDict:
                logging.warning("This macro name " + node.RuleName + " is already used for Macro " + str(
                    rulegroup.MacroDict[node.RuleName]) \
                                + " \n but now you have: " + string + "\n\n")
                return
            rulegroup.MacroDict.update({node.RuleName: node})
        else:
            rulegroup.RuleList.append(node)

    if remaining:
        RuleName = GetPrefix(node.RuleName) + "_" + str(node.ID)
        if node.RuleContent:    #the last was one rule, so we know the rest should be
            # one rule each line. let's not to call it recursively.
            lines = remaining.splitlines()
            counter = 0
            for line in lines:
                code, _ = SeparateComment(line)
                if code:
                    lineRuleName = RuleName + "_" + str(counter)
                    fakeString = lineRuleName + " == " + line
                    try:
                        InsertRuleInList(fakeString, rulegroup)
                    except RecursionError as e:
                        logging.error("Failed to process:" + string + "\n remaining is:" + remaining)
                        logging.error(str(e))
                        raise
                    counter += 1
        else:
            code, _ = SeparateComment(remaining)
            if  code:
                RuleName = GetPrefix(node.RuleName) + "_" + str(node.ID)

                fakeString = RuleName + " == " + remaining
                try:
                    InsertRuleInList(fakeString, rulegroup)
                except RecursionError as e:
                    logging.error("Failed to process:" + string + "\n remaining is:" + remaining)
                    logging.error(str(e))
                    raise

    SearchMatch = re.compile('test:(.+?)//', re.IGNORECASE | re.MULTILINE)
    # s = SearchMatch.findall(node.comment+"//")
    for TestSentence in SearchMatch.findall(node.comment + "//"):
        unittest = UnitTestNode(node.RuleName, TestSentence)
        rulegroup.UnitTest.append(unittest)
        # testLocation = node.comment.find("test:")
        # if testLocation < 0:
        #     testLocation = node.comment.find("TEST:")
        # if testLocation >= 0:
        #     TestSentence = node.comment[testLocation + 5:].strip()
        #     if TestSentence != "":
        #         UnitTest.update({node.RuleName: TestSentence})


def _ExpandRuleWildCard_List(OneList):
    Modified = False
    for rule in OneList:
        Expand = False
        # for token in rule.Tokens:
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            if token.repeat != [1, 1]:
                for repeat_num in range(token.repeat[0], token.repeat[1] + 1):
                    newrule = Rule()
                    newrule.FileName = rule.FileName
                    newrule.Origin = rule.Origin
                    newrule.comment = rule.comment
                    newrule.RuleName = rule.RuleName + "_" + str(repeat_num)
                    newrule.RuleContent = rule.RuleContent
                    for tokenindex_pre in range(tokenindex):
                        newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                    for tokenindex_this in range(repeat_num):
                        new_node = copy.copy(rule.Tokens[tokenindex])
                        new_node.repeat = [1, 1]
                        if tokenindex_this != 0 and rule.Tokens[tokenindex].StartChunk != 0:
                            new_node.StartChunk = 0 # in the copies, only the first one can be StartChunk
                        if tokenindex_this != repeat_num-1 and rule.Tokens[tokenindex].EndChunk != 0:
                            new_node.EndChunk = 0   # in the copies, only the last one can be EndChunk
                        newrule.Tokens.append(new_node)

                    NextIsStart = False
                    NextIsRestart = False
                    NextIsPointer = False
                    origin_node = None
                    if repeat_num == 0:  # this token is removed. some features need to copy to others
                        origin_node = rule.Tokens[tokenindex]
                        if origin_node.StartChunk:
                            NextIsStart = True
                        if origin_node.EndChunk:
                            lastToken = newrule.Tokens[-1]
                            lastToken.EndChunk = origin_node.EndChunk
                        if origin_node.RestartPoint:
                            NextIsRestart = True
                        if origin_node.pointer:
                            NextIsPointer = True
                            NextPointer = origin_node.pointer
                    for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                        new_node = copy.copy(rule.Tokens[tokenindex_post])
                        if tokenindex_post == tokenindex + 1:
                            if NextIsStart:
                                new_node.StartChunk = origin_node.StartChunk
                            if NextIsRestart:
                                new_node.RestartPoint = True
                            if NextIsPointer and NextPointer:
                                new_node.pointer = NextPointer
                        newrule.Tokens.append(new_node)

                    newrule.SetStrTokenLength()
                    OneList.append(newrule)
                    Expand = True
            if Expand:
                break
        if Expand:
            OneList.remove(rule)
            Modified = True

    return Modified


def ExpandRuleWildCard():
    Modified = False
    for RuleFile in RuleGroupDict:
        rg = RuleGroupDict[RuleFile]
        if rg.LoadedFromDB:
            continue
        Modified = _ExpandRuleWildCard_List(rg.RuleList) or Modified

    if Modified:
        logging.info("ExpandRuleWildCard next level.")
        ExpandRuleWildCard()  # recursive call itself to finish all.


def ExpandParenthesisAndOrBlock():
    Modified = False
    for RuleFile in RuleGroupDict:
        rg = RuleGroupDict[RuleFile]
        if rg.LoadedFromDB:
            continue

        logging.info("\tExpandParenthesisAndOrBlock in " + RuleFile + ": Size of RuleList:" + str(len(rg.RuleList)))
        Modified = _ExpandParenthesis(rg.RuleList) or Modified
        Modified = _ExpandOrBlock(rg.RuleList) or Modified

    if Modified:
        logging.info("ExpandParenthesisAndOrBlock to next level")
        ExpandParenthesisAndOrBlock()


def _RemoveExcessiveParenthesis(token):
    StartParenthesesPosition = token.word.find("(")
    if StartParenthesesPosition < 0:
        return False
    if StartParenthesesPosition > 0 and \
        token.word[StartParenthesesPosition-1] == "'" and token.word[StartParenthesesPosition+1] == "'":
        logging.info("ignore this parentheses:" + str(token))
        return False
    EndParenthesesPosition = StartParenthesesPosition + 1 + SearchPair(token.word[StartParenthesesPosition+1:], "()")
    if EndParenthesesPosition == StartParenthesesPosition:   #not paired
        logging.warning("The parenthesis are not paired:" + token.word + " in this token:\n" + str(token) )
        return False

    if "]" in token.word[StartParenthesesPosition:EndParenthesesPosition] \
        or ":" in token.word[StartParenthesesPosition:EndParenthesesPosition]:
        return False    #not excessive, if ]: in parenthesis.

    if (StartParenthesesPosition == 0 or token.word[StartParenthesesPosition-1] not in  "|!") \
        and (EndParenthesesPosition == len(token.word) or token.word[EndParenthesesPosition+1] != "|"):
        if StartParenthesesPosition>0:
            before = token.word[:StartParenthesesPosition]
        else:
            before = ""
        if EndParenthesesPosition<len(token.word):
            after = token.word[EndParenthesesPosition+1:]
        else:
            after = ""

        logging.info("Removing excessive parenthesis in: " + token.word)
        token.word = before + token.word[StartParenthesesPosition+1:EndParenthesesPosition] + after
        logging.info("\t\t as: " + token.word)
        return True
    else:
        return False

def _ExpandParenthesis(OneList):
    Modified = False
    RemovedExcessive = False
    for rule in OneList:
        if len(rule.RuleName) > 400:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + rule.RuleName)
            continue
        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            if  _RemoveExcessiveParenthesis(rule.Tokens[tokenindex]):
                RemovedExcessive = True
            token = rule.Tokens[tokenindex]

            if (token.word.startswith("(") and len(token.word) == 2 + SearchPair(token.word[1:], "()")) \
                    or (token.word.startswith("[(") and len(token.word) == 4 + SearchPair(token.word[2:], "()")):
                # logging.warning("Parenthesis:\n\t" + token.word + "\n\t rulename: " + rule.RuleName )
                parenthesisIndex = token.word.find("(")
                try:
                    subTokenlist = Tokenize(token.word[parenthesisIndex + 1:-parenthesisIndex - 1])
                except Exception as e:
                    logging.error("Failed to _ExpandParenthesis.tokenize because: " + str(e))
                    logging.error("Rule name: " + rule.RuleName)
                    continue

                if subTokenlist:
                    ProcessTokens(subTokenlist)
                    subTokenlist[0].pointer = token.pointer
                    subTokenlist[0].StartChunk = token.StartChunk
                    subTokenlist[-1].EndChunk = token.EndChunk

                newrule = Rule()
                newrule.FileName = rule.FileName
                newrule.Origin = rule.Origin
                newrule.comment = rule.comment
                newrule.RuleName = rule.RuleName + "_p" + str(tokenindex)
                newrule.RuleContent = rule.RuleContent
                for tokenindex_pre in range(tokenindex):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
                for subtoken in subTokenlist:
                    newrule.Tokens.append(subtoken)
                for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
                newrule.SetStrTokenLength()
                OneList.append(newrule)
                Expand = True
                # logging.warning("\tExpand Parentheses is true, because of " + rule.RuleName)
                break
        if Expand:
            OneList.remove(rule)
            Modified = True

    if RemovedExcessive:
        Modified = True
    return Modified
    # if Modified:
    #     logging.info("\tExpandParenthesis next level.")
    #     ExpandParenthesis()    #recursive call itself to finish all.


def _ProcessOrBlock(Content, orIndex):
    if orIndex <= 0 or orIndex >= len(Content):
        raise RuntimeError("Wrong orIndex:" + str(orIndex))
    if Content[orIndex] != '|':
        raise RuntimeError("Wrong orIndex for Content:" + Content[orIndex])

    start = orIndex
    end = orIndex

    try:
        for pair in Pairs:
            if Content[orIndex + 1] == pair[0]:
                end = end + 2 + SearchPair(Content[orIndex + 2:], pair)
        if end == orIndex:  # the next character is not pair, so it is a normal word
            end = end + 2 + _SearchToEnd_OrBlock(Content[orIndex + 2:])

        for pair in Pairs:
            if Content[orIndex - 1] == pair[1]:
                start = SearchPair(Content[:orIndex - 1], pair, Reverse=True)
        if start == orIndex:  # the next character is not pair, so it is a normal word
            start = _SearchToEnd_OrBlock(Content[:orIndex - 1], Reverse=True)
    except Exception as e:
        logging.info("Failed to process or block because: " + str(e))
        return None, None, None

    originBlock = Content[start:end + 1]
    leftBlock = Content[start:orIndex]
    rightBlock = Content[orIndex + 1:end + 1]

    #if left/right block is enclosed by (), and it is part of one token , then the () can be removed:
    # write out in log as confirmation.
    if Content[0] == "[" and SearchPair(Content[1:], "[]") == len(Content)-2:
        if leftBlock[0] == "(" and SearchPair(leftBlock[1:], "()") == len(leftBlock) - 2:
            #logging.debug("New kind of removing (): Removing them from " + leftBlock + " in :\n" + Content)
            leftBlock = leftBlock[1:-1]
        if rightBlock[0] == "(" and SearchPair(rightBlock[1:], "()") == len(rightBlock) - 2:
            #logging.debug("New kind of removing (): Removing them from " + rightBlock + " in :\n" + Content)
            rightBlock = rightBlock[1:-1]
    else:
        if "[" not in originBlock :
            if leftBlock[0] == "(" and SearchPair(leftBlock[1:], "()") == len(leftBlock) - 2:
                #logging.debug("Extra New kind of removing (): Removing them from " + leftBlock + " in :\n" + Content)
                leftBlock = leftBlock[1:-1]
            if rightBlock[0] == "(" and SearchPair(rightBlock[1:], "()") == len(rightBlock) - 2:
                #logging.debug("Extra New kind of removing (): Removing them from " + rightBlock + " in :\n" + Content)
                rightBlock = rightBlock[1:-1]

    return originBlock, leftBlock, rightBlock


def _ExpandOrBlock(OneList):
    Modified = False
    # counter = 0
    for rule in OneList:
        if len(rule.RuleName) > 200:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + rule.RuleName)
            continue
        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]
            orIndex = token.word.find(")|") + 1
            if orIndex <= 0:
                orIndex = token.word.find("|(")
                if orIndex <= 0:
                    orIndex = token.word.find("]|[")
                    if orIndex <= 0:
                        continue
                    else:
                        orIndex += 1    #move the pointer from ] to |



            originBlock, leftBlock, rightBlock = _ProcessOrBlock(token.word, orIndex)
            if originBlock is None:
                logging.error("ExpandOrBlock: Failed to process or block for: \n" + str(rule))
                continue  # failed to process. might be pair tag issue.

            # left of |:
            newrule = Rule()
            newrule.FileName = rule.FileName
            newrule.Origin = rule.Origin
            newrule.comment = rule.comment
            newrule.RuleName = rule.RuleName + "_ol" + str(tokenindex)
            newrule.RuleContent = rule.RuleContent
            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))
            #
            # newtoken = copy.copy(rule.Tokens[tokenindex])
            # newtoken.word = newtoken.word.replace(originBlock, leftBlock)
            # newrule.Tokens.append(newtoken)

            # Analyze the new word, might be a list of tokens.
            try:
                subTokenlist = Tokenize(token.word.replace(originBlock, leftBlock))
            except Exception as e:
                logging.error("Failed to _ExpandOrBlock.left.tokenize because: " + str(e))
                logging.error("when expanding or block:" + leftBlock + " for rule name: " + rule.RuleName)
                continue
            if subTokenlist:
                ProcessTokens(subTokenlist)
                subTokenlist[0].pointer = token.pointer
                subTokenlist[0].StartChunk = token.StartChunk
                subTokenlist[-1].EndChunk = token.EndChunk
                if token.action:
                    if len(subTokenlist) > 1:
                        logging.warning("The block has action before Or expand!")
                    subTokenlist[-1].action = token.action
            for subtoken in subTokenlist:
                newrule.Tokens.append(subtoken)

            for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
            newrule.SetStrTokenLength()
            OneList.append(newrule)

            # right of |:
            newrule = Rule()
            newrule.FileName = rule.FileName
            newrule.Origin = rule.Origin
            newrule.comment = rule.comment
            newrule.RuleName = rule.RuleName + "_or" + str(tokenindex)
            newrule.RuleContent = rule.RuleContent
            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))

            # Analyze the new word, might be a list of tokens.
            try:
                subTokenlist = Tokenize(token.word.replace(originBlock, rightBlock))
            except Exception as e:
                logging.error("Failed to _ExpandOrBlock.right.tokenize because: " + str(e))
                logging.error("when expanding or block:" + rightBlock + " for rule name: " + rule.RuleName)
                continue
            if subTokenlist:
                ProcessTokens(subTokenlist)
                subTokenlist[0].pointer = token.pointer
                subTokenlist[0].StartChunk = token.StartChunk
                subTokenlist[-1].EndChunk = token.EndChunk
                if token.action:
                    if len(subTokenlist) > 1:
                        logging.warning("The block has action before Or expand!")
                    subTokenlist[-1].action = token.action
            for subtoken in subTokenlist:
                newrule.Tokens.append(subtoken)

            for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
            newrule.SetStrTokenLength()
            OneList.append(newrule)

            Expand = True
            # logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
            break

        if Expand:
            OneList.remove(rule)
            Modified = True

    return Modified


def _ProcessOrToken(word):
    word = word.strip("[|]")
    spaceseparated = word.split(" ")
    i = 0
    for i in range(len(spaceseparated)):
        if spaceseparated[i].find("'|")>0:
            #this is the piece we need to separate
            break
    if i > 0:
        leftpieces = " ".join(spaceseparated[:i])
    else:
        leftpieces = ""

    if i < len(spaceseparated):
        rightpieces = " ".join(spaceseparated[i+1:])
    else:
        rightpieces = ""

    orlist = spaceseparated[i].split("|")
    normlist = [x for x in orlist if len(x)>2 and x[0]=="'" and x[-1]=="'"]
    notnormlist = set(orlist) - set(normlist)

    if notnormlist:
        orlist = ["|".join(sorted(notnormlist)) ] + normlist
    else:
        orlist = normlist

    return orlist, "["+leftpieces, rightpieces+"]"


#Expand | inside of one token. Should be done after the _ExpandOrBlock and compilation.
# in here, each "or" operator should be one feature or one word.
def _ExpandOrToken(OneList):
    Modified = False
    # counter = 0
    for rule in OneList:
        if len(rule.RuleName) > 200:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + rule.RuleName)
            continue
        Expand = False
        for tokenindex in range(len(rule.Tokens)):
            token = rule.Tokens[tokenindex]

            if token.word.find("|") < 0:
                continue

            #Process  a|b|'c|d|e'|f. Change it to a|b|'c'|'d'|'e'|f
            ormatch = re.match("^(.*')(.*?)('.*)$", token.word)
            if ormatch:
                innerquote = ormatch.group(2)
                if "|" in innerquote and "'" not in innerquote:
                    innerquote2 = innerquote.replace("|", "'|'")
                    token.word = ormatch.group(1) + innerquote2 + ormatch.group(3)
                    logging.debug("or modification: from " + ormatch.group(2) + " to " + innerquote2)

            orIndex = token.word.find("'|") + token.word.find("|'")
            if orIndex < 0:
                continue

            orlist, leftBlock, rightBlock = _ProcessOrToken(token.word)
            if orlist is None:
                logging.error("ExpandOrBlock: Failed to process or block for: \n" + str(rule))
                continue  # failed to process. might be pair tag issue.

            for orpiece in orlist:
                # left of the token:
                newrule = Rule()
                newrule.FileName = rule.FileName
                newrule.Origin = rule.Origin
                newrule.comment = rule.comment
                newrule.RuleName = rule.RuleName + "_ol" + str(tokenindex)
                newrule.RuleContent = rule.RuleContent
                for tokenindex_pre in range(tokenindex):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_pre]))

                #current token
                node = copy.copy(token)
                node.word = leftBlock + " " + orpiece + " " + rightBlock
                newrule.Tokens.append(node)

                # right of the token:
                for tokenindex_post in range(tokenindex + 1, len(rule.Tokens)):
                    newrule.Tokens.append(copy.copy(rule.Tokens[tokenindex_post]))
                newrule.SetStrTokenLength()
                newrule.Chunks = copy.copy(rule.Chunks)
                OneList.append(newrule)

            Expand = True
            # logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
            break   # don't work on the next | in this rule. wait for the next round.

        if Expand:
            OneList.remove(rule)
            Modified = True

    if Modified:
        return _ExpandOrToken(OneList)
    else:
        return False


def PreProcess_CheckFeatures():
    for RuleFile in RuleGroupDict:
        logging.info("PreProcessing " + RuleFile)
        rg = RuleGroupDict[RuleFile]
        if rg.LoadedFromDB:
            continue

        _PreProcess_CheckFeaturesAndCompileChunk(rg.RuleList)

def PreProcess_CompileHash():
    for RuleFile in RuleGroupDict:
        logging.info("PreProcessing " + RuleFile)
        rg = RuleGroupDict[RuleFile]
        if rg.LoadedFromDB:
            continue

        _PreProcess_CompileHash(rg.RuleList)


def SortByLength():
    for RuleFile in RuleGroupDict:
        logging.info("Sorting " + RuleFile)
        rg = RuleGroupDict[RuleFile]
        if rg.LoadedFromDB:
            continue

        rg.RuleList = sorted(rg.RuleList, key = lambda x: len(x.Tokens), reverse=True)


# Check the rules. If it is a stem, not a feature, but omit quote
#   then we add quote;
# If it is like 'a|b|c', then we change it to 'a'|'b'|'c'
def _PreProcess_CheckFeaturesAndCompileChunk(OneList):
    for rule in OneList:
        for token in rule.Tokens:
            #_CheckFeature(token, rule.RuleName)
            token.word = "[" +  _CheckFeature_returnword(token.word) + "]"

        rule.CompileChunk()

    _ExpandOrToken(OneList)


def _PreProcess_CompileHash(OneList):
    for rule in OneList:
        rule.norms = [token.word.split("'")[1] if token.word.count("'") == 2 and token.word.split("'")[0][-1] != "!"
                                                  and "^" not in token.word.split("'")[1] and "-" not in token.word.split("'")[1] else None
                      for token in rule.Tokens if not token.SubtreePointer ]


def _CheckFeature_returnword(word):
    try:
        if len(word) >= 2 and word[0] == "[" and SearchPair(word[1:], "[]") == len(word) - 2:
            word = word[1:-1].strip()

        _, matchtype = LogicOperation_CheckPrefix(word, 'unknown')
    except RuntimeError as e:

        logging.error(str(e))
        return ''

    if not word:
        return ''

    prefix = ""

    if word[0] == "!":
        prefix = "!"
        word = word.lstrip("!")

    if matchtype == 'norm':
        if "|" in word:
            items = re.split("\|", word)
            word =  "'|'".join(items)
#                elif " " in word:  # 'this is a good': separate as multiple token.
#                    raise NotImplementedError("TODO: separate this as multiple token")

    elif matchtype == 'atom':
        if "|" in word:
            items = re.split("\|", word)
            word = "/|/".join(items)
#                elif " " in word:  # 'this is a good': separate as multiple token.
#                    raise NotImplementedError("TODO: separate this as multiple token")

    elif matchtype == 'text':
        if "|" in word:
            items = re.split("\|", word)
            word = "\"|\"".join(items)
#                elif " " in word:  # 'this is a good': separate as multiple token.
#                    raise NotImplementedError("TODO: separate this as multiple token")

    elif matchtype == 'unknown':
        if not re.search('[| !]', word):
            if FeatureOntology.GetFeatureID(word) == -1:
                # logging.warning("Will treat this word as a stem:" + word)
                word = "'" + word + "'"
        elif "|" in word and " " not in word and "[" not in word:
            # be aware of ['and|or|of|that|which'|PP|CM]
            try:
                OrBlocks = LogicOperation_SeparateOrBlocks(word)
            except RuntimeError as e:
                logging.error("Error for rule:" + word )
                logging.error(str(e))
                return  # not to process the rest.

            newword = ""
            for OrBlock in OrBlocks:
                _, mtype = LogicOperation_CheckPrefix(OrBlock, "unknown")
                if mtype == "unknown" and OrBlock[0] != "!" and FeatureOntology.GetFeatureID(OrBlock) == -1:
                    # logging.warning("Will treat this as a stem:" + OrBlock)
                    newword += "'" + OrBlock + "'|"
                else:
                    newword += OrBlock + "|"
            word = newword.rstrip("|")
        elif " " in word and  "[" not in word:
            # be aware of ['and|or|of|that|which'|PP|CM]
            AndBlocks = word.split()
            newword = ""
            for AndBlock in AndBlocks:
                newword += _CheckFeature_returnword(AndBlock) + " "
            word = newword.rstrip(" ")
    return  prefix + word


def OutputRules(rulegroup, style="details"):
    output = "// ****Rules**** " + rulegroup.FileName + "\n"
    output += "// * size: " + str(len(rulegroup.RuleList)) + " *\n"
    #for rule in sorted(rulegroup.RuleList, key=lambda x: (GetPrefix(x.RuleName), x.RuleContent)):
    for rule in rulegroup.RuleList:
        output += rule.output(style) + "\n"

    output += "// ****Macros****\n"
    output += "// * size: " + str(len(rulegroup.MacroDict)) + " *\n"
    for rule in rulegroup.MacroDict.values():
        output += rule.output(style) + "\n"

    output += "// End of Rules/Expert Lexicons/Macros\n"
    return output


def OutputRuleFiles(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FolderLocation)

    for RuleFile in RuleGroupDict:
        rg = RuleGroupDict[RuleFile]
        output = OutputRules(rg, "concise")
        FileLocation = os.path.join(FolderLocation, rg.FileName)
        with open(FileLocation, "w", encoding="utf-8") as writer:
            writer.write(output)

        utoutput = ""
        for unittestnode in rg.UnitTest:
            utoutput += unittestnode.RuleName + "\t// " + unittestnode.TestSentence + "\n"
        utFileLocation = os.path.join(FolderLocation, rg.FileName + ".unittest")
        with open(utFileLocation, "w", encoding="utf-8") as writer:
            writer.write(utoutput)

    OutputRuleDB()

#tablefields and values are lists.
def DBInsertOrGetID(tablename, tablefields, values):
    cur = DBCon.cursor()
    strsql = "SELECT ID from " + tablename + " where " + " AND ".join(field + "=?" for field in tablefields ) + "  limit 1"
    cur.execute(strsql, values)
    resultrecord = cur.fetchone()
    if resultrecord:
        resultid = resultrecord[0]
    else:
        strsql = "INSERT into " + tablename + " (" + ",".join(tablefields) + ") VALUES(" + ",".join("?" for field in tablefields) + ")"
        cur.execute(strsql, values)
        resultid = cur.lastrowid
    cur.close()
    return resultid


#sqlite3 parser.db
### ruleinfo.body is the body part of each token. for unique comparison.
# CREATE TABLE rulechunks   (ID INTEGER PRIMARY KEY AUTOINCREMENT, ruleid INT , chunklevel INT, startoffset INT, length INT, stringchunklength INT, headoffset INT, action TEXT  );
# CREATE TABLE rulefiles    (ID INTEGER PRIMARY KEY AUTOINCREMENT, filelocation TEXT, createtime DATETIME, verifytime DATETIME);
# CREATE TABLE sentences    (ID INTEGER PRIMARY KEY AUTOINCREMENT, sentence TEXT, result TEXT, createtime DATETIME, verifytime DATETIME, CONSTRAINT unique_sentence UNIQUE(sentence) );
# CREATE TABLE rulehits     (sentenceid INT, ruleid INT, createtime DATETIME, verifytime DATETIME, CONSTRAINT unique_hit UNIQUE(sentenceid, ruleid));
# CREATE TABLE rulenodes    (ID INTEGER PRIMARY KEY AUTOINCREMENT, ruleid INT, sequence INT, matchbody TEXT, action TEXT , pointer TEXT, subtreepointer TEXT, CONSTRAINT unique_position UNIQUE(ruleid, sequence));
# CREATE TABLE ruleinfo     (ID INTEGER PRIMARY KEY AUTOINCREMENT, rulefileid INT, name, strtokenlength INT, tokenlength INT, body TEXT, status INT, norms TEXT, comment TEXT, createtime DATETIME, verifytime DATETIME, CONSTRAINT unique_body UNIQUE(rulefileid, body) );
def OutputRuleDB():
    cur = DBCon.cursor()
    for RuleFile in RuleGroupDict:
        rg = RuleGroupDict[RuleFile]
        if rg.LoadedFromDB:     #during the loading, compare file modify time with verifytime in db. If the file is not modified, load the rulegroup from db.
            continue
        strsql = "SELECT ID from rulefiles where filelocation=?  limit 1"
        cur.execute(strsql, [rg.FileName,])
        resultrecord = cur.fetchone()
        if resultrecord:
            rulefileid = resultrecord[0]
            strsql = "update rulefiles set verifytime=DATETIME('now') where ID=?"
            cur.execute(strsql, [rulefileid, ])
        else:
            strsql = "INSERT into rulefiles (filelocation, createtime, verifytime) VALUES(?, DATETIME('now'), DATETIME('now'))"
            cur.execute(strsql, [rg.FileName,])
            rulefileid = cur.lastrowid

        for rule in rg.RuleList:
            rule.DBSave(rulefileid)
            #if there is same body of rule in db (for the same rulefileid), then use the same rule id, remove the existing rulenodes and rulechunks for it. create new ones;
            #    update the verifytime, and status.
            # if there is no same body, create everything.
            #Aftter one iteration, find the rule that the verifytime is old, change status to disable them.

    DBCon.commit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    # LoadRules("../../fsa/Y/900NPy.xml")
    # LoadRules("../../fsa/Y/800VGy.txt")
    # # LoadRules("../../fsa/Y/1800VPy.xml")
    # # LoadRules("../../fsa/Y/100y.txt")
    # # LoadRules("../../fsa/Y/50POSy.xml")
    # # #
    # LoadRules("../../fsa/X/mainX2.txt")
    # LoadRules("../../fsa/X/ruleLexiconX.txt")
    # # #
    #LoadRules("../../fsa/X/0defLexX.txt")
    LoadRules("../../fsa/X/0test.txt")

    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_3_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_4_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_5_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_6_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_7_list.txt")

    #LoadRules("../../fsa/X/10compound.txt")

    # LoadRules("../../fsa/X/180NPx.txt")

    ExpandRuleWildCard()
    ExpandParenthesisAndOrBlock()
    ExpandRuleWildCard()
    PreProcess_CheckFeatures()
    PreProcess_CompileHash()
    SortByLength()

    # print (OutputRules("concise"))
    OutputRuleFiles("../compiled/")
    #print(FeatureOntology.OutputMissingFeatureSet())
