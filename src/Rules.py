import copy, traceback
from datetime import datetime
from utils import *
import utils

# import FeatureOntology
# usage: to output rules list, run:
#       python Rules.py > rules.txt

from LogicOperation import CheckPrefix as LogicOperation_CheckPrefix
from LogicOperation import SeparateOrBlocks as LogicOperation_SeparateOrBlocks
import FeatureOntology

RuleGroupDict = {}
_GlobalMacroDict = {}


# RuleIdenticalNetwork = {}   #(ID, index):set(ruleID)

class RuleGroup(object):
    idCounter = 0

    def __init__(self, FileName):
        Rule.idCounter += 1
        self.ID = Rule.idCounter
        self.FileName = FileName
        self.RuleList = []
        self.MacroDict = {}
        if _GlobalMacroDict:
            self.MacroDict.update(_GlobalMacroDict)
        self.UnitTest = []
        self.LoadedFromDB = False
        self.HashRules = {}
        self.NoHashRules = []
        # self.NormHash = {}  # write to norm.

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


def ResetAllRules():
    global RuleGroupDict
    for rulefile in RuleGroupDict:
        del RuleGroupDict[rulefile].RuleList[:]
    RuleGroupDict.clear()
    _GlobalMacroDict.clear()
    # RuleIdenticalNetwork = {}


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
        newlines[-1] = endlineMatch.group(1)
        newlines[0] += endlineMatch.group(2)

    newString = "\n".join(newlines)

    if newString[0] == "(" and SearchPair(newString[1:], "()") >= len(newString) - 3:  # sometimes there is ";" sign
        return newString, None
    if newString[0] == "{" and SearchPair(newString[1:], "{}") >= len(newString) - 3:
        return newString, None
    if newString[0] == "<" and SearchPair(newString[1:], "<>") >= len(newString) - 3:
        return newString, None
    return lines[0], "\n".join(lines[1:])


class RuleToken(object):
    idCounter = 0

    def __init__(self, orig=None):
        RuleToken.idCounter += 1
        if orig is None:
            self.StartChunk = 0
            self.EndChunk = 0
            self.repeat = [1, 1]
            self.word = ''
            self.RestartPoint = False
            self.MatchType = -1  # -1:unknown/mixed 0: feature 1:text 2:norm 3:atom 4:pnorm (as in Aug 2018, not being used for matching)
            self.pointer = ''
            self.action = ''
            self.SubtreePointer = ''
            self.AndFeatures = set()
            self.OrFeatureGroups = []
            self.NotFeatures = set()
            self.AndText = ''
            self.AndTextMatchtype = ''
            self.NotTexts = set()
            self.NotTextMatchtype = ''
            self.FullString = False
        else:
            self.__dict__ = copy.deepcopy(orig.__dict__)
        self.ID = RuleToken.idCounter

    # def __eq__(self, other):  # only compare the matching part, not the action part.
    #     logging.error("Utilizing the RuleToken __eq__ function!")
    #     if self.word.strip() == other.word.strip():  # can be more complicate, comparint SubtreePointer, AndFeatures, OrFeatureGroups...
    #         return True
    #     else:
    #         return False



    def __str__(self):
        output = ""
        for _ in range(self.StartChunk):
            output += "<"
        output += self.pointer
        if self.SubtreePointer:
            t = "[^" + self.SubtreePointer + "=" + self.word.strip("[|]").replace("<", "\<").replace(">", "\>") + "]"
        else:
            t = "[" + self.word.strip("[|]").replace("<", "\<").replace(">", "\>") + "]"
        if self.action:
            t = t.replace("]", ":action:" + self.action + "]")
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
        self.Length = 0  # how many rule tokens;
        self.StringChunkLength = 0  # how many string tokens this chunk apply to
        self.HeadOffset = -1
        self.HeadConfidence = -1
        self.Action = ''
        self.ChunkLevel = 1


class Rule:
    idCounter = 0

    def __init__(self, orig=None):
        Rule.idCounter += 1
        if orig is None:
            self.FileName = ''
            self.RuleName = ''
            self.Origin = ''
            self.RuleContent = ''
            self.Tokens = []
            self.TokenLength = 0
            self.StrTokenLength = -1
            self.Chunks = []
            self.comment = ''
            self.norms = []
            self.Priority = 0   #default is 0. (Top) is 1. (Bottom) is -1.
            self.WindowLimit = 0     #default 0 means none.  Only used for graph.
            self.LengthLimit = 0    #default 0 means none. Only used for graph.(for now, as Sept 1, 2018)
        else:
            self.__dict__ = copy.deepcopy(orig.__dict__)
        self.ID = Rule.idCounter

    def SetStrTokenLength(self):
        VirtualTokenNum = 0  # Those "^V=xxx" is virtual token that does not apply to real string token
        for t in self.Tokens:
            if t.SubtreePointer:
                VirtualTokenNum += 1
        self.TokenLength = len(self.Tokens)
        self.StrTokenLength = self.TokenLength - VirtualTokenNum

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

        #Note: codeblocks can't be used to set rule, because I need the origin comment (of each line) to set Test for each rule.

        RuleBlocks = re.match("(.+?)==(.+)$", ruleString, re.DOTALL)
        if not RuleBlocks:
            RuleBlocks = re.match("(.+?)::(.+)$", ruleString, re.DOTALL)
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

        # SampleRule1a(Top >SampleRule1) ; SampleRule5(Bottom >SampleRule3 >SampleRule4)
        PriorityMatch = re.match("(.*)\((.*)\)$", self.RuleName)

        if PriorityMatch:
            logging.info("Rule {} Priority: {}".format(PriorityMatch.group(1), PriorityMatch.group(2)))
            self.RuleName = PriorityMatch.group(1).strip()
            if PriorityMatch.group(2).lower() == "top":
                self.Priority = 1
            if PriorityMatch.group(2).lower() == "bottom":
                self.Priority = -1
            #TODO: work on the ">SampleRule3 >SampleRule4" this kind of rules.

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

            self.RuleContent = RemoveExcessiveSpace(ProcessMacro(RuleCode, MacroDict))
            # PriorityMatch = re.match("(/d*) (.*)", self.RuleContent)  #comment out on Sept 1: leave the priority in RuleName part as in the spec.
            # if PriorityMatch:
            #     self.Priority = int(PriorityMatch.group(1))
            #     self.RuleContent = PriorityMatch.group(2)

            WindowMatch = re.match("win=(.*?) (.*)$", self.RuleContent, re.IGNORECASE)
            if WindowMatch:     #win=15, or win=cl (CL, clause) fow window size.
                self.WindowLimit = int(WindowMatch.group(1))
                self.RuleContent = WindowMatch.group(2).strip()

            LengthMatch = re.match("len=(.*?) (.*)$", self.RuleContent, re.IGNORECASE)
            if LengthMatch:     #len=5  # the sentence length must be small or equal to 5.
                self.LengthLimit = int(LengthMatch.group(1))
                self.RuleContent = LengthMatch.group(2).strip()

            self.Tokens = Tokenize(self.RuleContent)
        except Exception as e:
            logging.error("Failed to setrule because: " + str(e))
            logging.error("Rulename is: " + self.RuleName)
            self.RuleName = ""
            self.RuleContent = ""
            return remaining
        ProcessTokens(self.Tokens)

        if len(self.Tokens) == 0:
            logging.error("There is no rule set for:" + self.RuleName)
            self.RuleName = ""
            self.RuleContent = ""
            return remaining

        if self.Tokens[0].StartChunk:
            UniversalToken = RuleToken()
            UniversalToken.word = '[]'  # make it universal
            self.Tokens = [UniversalToken] + self.Tokens

        self.SetStrTokenLength()
        return remaining

    def __str__(self):
        return self.output("details")

    # def oneliner(self):
    #     return self.output("concise")

    # style: concise, or detail
    def output(self, style="concise"):
        output = "//ID:{} Priority:{}".format(self.ID, self.Priority)
        if self.RuleName.startswith("@"):
            output += "[Macro]\n"
        elif self.RuleName.startswith("#"):
            output += "[Macro with parameter]\n"
        else:
            output += "[Rule]\n"

        if style == "concise":
            output += self.RuleName + " == {"

            if len(self.Tokens) == 0:
                # logging.error("This rule does not have ruletoken:" + self.RuleContent + " " + self.comment)
                # mostly for the Macro.
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
        return "/".join(t.word + t.SubtreePointer for t in self.Tokens)

    # if there is same body of rule in db (for the same rulefileid), then use the same rule id, remove the existing rulenodes and rulechunks for it. create new ones;
    #    update the verifytime, and status.
    # if there is no same body, create everything.
    def DBSave(self, rulefileid):
        cur = utils.DBCon.cursor()
        strsql = "SELECT ID from ruleinfo where rulefileid=? AND body=?  limit 1"
        cur.execute(strsql, [rulefileid, self.body()])
        resultrecord = cur.fetchone()
        if resultrecord:
            self.ID = resultrecord[0]
            strsql = "UPDATE ruleinfo set status=1, verifytime=DATETIME('now') where ID=?"
            cur.execute(strsql, [self.ID, ])
            strsql = "DELETE from rulenode_features where rulenodeid in (SELECT ID from rulenodes where ruleid=?)"
            cur.execute(strsql, [self.ID, ])
            strsql = "DELETE from rulenode_orfeatures where rulenodeid in (SELECT ID from rulenodes where ruleid=?)"
            cur.execute(strsql, [self.ID, ])
            strsql = "DELETE from rulenodes where ruleid=?"
            cur.execute(strsql, [self.ID, ])
            strsql = "DELETE from rulechunks where ruleid=?"
            cur.execute(strsql, [self.ID, ])
            strsql = "DELETE from ruleinfo where id=?"
            cur.execute(strsql, [self.ID, ])

        strsql = "INSERT into ruleinfo (rulefileid, name, body, strtokenlength, tokenlength, status, " \
                 "priority, windowlimit, lengthlimit, " \
                 "norms, origin, comment, createtime, verifytime) " \
                 "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"
        cur.execute(strsql, [rulefileid, self.RuleName, self.body(), self.StrTokenLength, self.TokenLength, 1,
                             self.Priority, self.WindowLimit, self.LengthLimit,
                             '/'.join([x.replace("/", IMPOSSIBLESTRINGSLASH) if x else '' for x in self.norms]),
                             self.Origin, self.comment])
        self.ID = cur.lastrowid

        strsql_node = "INSERT into rulenodes (ruleid, sequence, matchbody, action, pointer, subtreepointer, andtext, andtextmatchtype, nottextmatchtype) values(?, ?, ?, ?, ?, ?, ?, ?, ?)"
        strsql_node_feature = "INSERT into rulenode_features (rulenodeid, featureid, type) values(?,?,?)"
        strsql_node_text = "INSERT into rulenode_texts (rulenodeid, text, type) values(?,?,?)"
        strsql_node_orfeature = "INSERT into rulenode_orfeatures (rulenodeid, featureid, groupid) values(?,?,?)"
        try:
            for i in range(self.TokenLength):
                cur.execute(strsql_node, [self.ID, i, self.Tokens[i].word, self.Tokens[i].action, self.Tokens[i].pointer,
                                          self.Tokens[i].SubtreePointer,
                                          self.Tokens[i].AndText, self.Tokens[i].AndTextMatchtype,
                                          self.Tokens[i].NotTextMatchtype])
                nodeid = cur.lastrowid
                for fid in self.Tokens[i].AndFeatures:
                    cur.execute(strsql_node_feature, [nodeid, fid, 1])
                for gid in range(len(self.Tokens[i].OrFeatureGroups)):
                    for fid in self.Tokens[i].OrFeatureGroups[gid]:
                        cur.execute(strsql_node_orfeature, [nodeid, fid, gid])
                for fid in self.Tokens[i].NotFeatures:
                    cur.execute(strsql_node_feature, [nodeid, fid, 3])
                for NotText in self.Tokens[i].NotTexts:
                    cur.execute(strsql_node_text, [nodeid, NotText, 2])
        except sqlite3.Error as e:
            logging.error(e)
            logging.error(traceback.format_exc())
            logging.info("DBSeve: {}".format(self))
        strsql_chunk = "INSERT into rulechunks (ruleid, chunklevel, startoffset, length, stringchunklength, headoffset, action) values(?, ?, ?, ?, ?, ?, ?)"
        for i in range(len(self.Chunks)):
            cur.execute(strsql_chunk, [self.ID, self.Chunks[i].ChunkLevel, self.Chunks[i].StartOffset,
                                       self.Chunks[i].Length, self.Chunks[i].StringChunkLength,
                                       self.Chunks[i].HeadOffset, self.Chunks[i].Action
                                       ])
        cur.close()

    # For head (son) node, only apply negative action, and
    #   features after "NEW".
    # update on Feb 4: Only "X++" is for new node. The rest is for Son
    @staticmethod
    def ExtractParentSonActions(actinstring):

        # if "+++" in actinstring:    # if there is +++, then all are parentaction.
        #     return actinstring, ""    #May 2nd, not to apply this rule.
        ieaction = ''
        iepairmatch = re.search("(#.*#)", actinstring)
        if iepairmatch:
            ieaction = " " + iepairmatch.group(1)    #extract IE pair action.
            actinstring = actinstring.replace(iepairmatch.group(1), '')

        actions = set(actinstring.split())

        # SonActionString = " ".join([a for a in actions if a[-2:] != "++"   or a == '+++' ])
        ParentActions = [a for a in actions if a[-2:] == "++"]
        ParentActions.extend([a for a in actions if a[0:2] == "^^"])

        SonActions = list(actions - set(ParentActions))

        return " ".join(sorted(ParentActions)), " ".join(sorted(SonActions)) + ieaction

    def CompileChunk(self):
        rulebody = ''
        for token in self.Tokens:
            rulebody += str(token)
        rulebody = rulebody.replace("\<", IMPOSSIBLESTRINGLESS).replace("\>", IMPOSSIBLESTRINGGREATER)

        if rulebody.count('<') > 4:
            logging.warning("This rule has more than 4 chunks:")
            logging.warning(rulebody)

        # TODO: leave these 3 for future usage.
        Chunk2_3_1 = re.match("(.*) <(.*)<(.+)>(.*) <(.+)>(.*) <(.+)>(.*)>(.*)", rulebody)
        # Chunk2_3_2 = re.match("(.*)<(.*)<(.+)>(.*)<(.+)>(.*)>(.*)<(.+)>(.*)", rulebody)
        # Chunk2_3_3 = re.match("(.*)<(.+)>(.*)<(.*)<(.+)>(.*)<(.+)>(.*)>(.*)", rulebody)

        Chunk2_2 = re.match("(.*) <(.*)<(.+)>(.*) <(.+)>(.*)>(.*)", rulebody)
        Chunk2_1 = re.match("(.*) <(.*)<(.+)>(.*)>(.*)", rulebody)
        Chunk1_3 = re.match("(.*) <(.+)>(.*) <(.+)>(.*) <(.+)>(.*)", rulebody)
        Chunk1_2 = re.match("(.*) <(.+)>(.*) <(.+)>(.*)", rulebody)
        Chunk1_1 = re.match("(.*) <(.+)>(.*)", rulebody)

        if Chunk2_3_1:  # "(.*)<(.*)<(.+)>(.*)<(.+)>(.*)<(.+)>(.*)>(.*)"
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
            c3 = self.CreateChunk(
                tokencount_1 + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5 + tokencount_6, tokencount_7)
            self.Chunks.append(c3)

            c = RuleChunk()
            c.ChunkLevel = 2
            c.StartOffset = tokencount_1
            c.Length = tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6 + 1 + tokencount_8
            # check the part before first inner chuck.
            VirtualTokenNum1 = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2,
                                                                     HeadOffset=0, EnableLowCHead=False)
            # check the part after first inner chuck, before second inner chuck.
            VirtualTokenNum2 = self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                                      Length=tokencount_4,
                                                                      HeadOffset=tokencount_2 + 1, EnableLowCHead=False)
            # check the part after second inner chuck.
            VirtualTokenNum3 = self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5,
                                                                      Length=tokencount_6,
                                                                      HeadOffset=tokencount_2 + 1 + tokencount_4 + 1, EnableLowCHead=False)
            # check the part after third inner chuck.
            VirtualTokenNum4 = self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5 + tokencount_6 + tokencount_7,
                                                                      Length=tokencount_8,
                                                                      HeadOffset=tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6 + 1, EnableLowCHead=False)

            if c.HeadOffset == -1:
                if "^^." not in c3.Action:
                    c.HeadConfidence = 3
                    c.HeadOffset = tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6 - VirtualTokenNum1 - VirtualTokenNum2 - VirtualTokenNum3
                    c3.Action += " H ^.H "  # add Head for the chunk.

                if "^^." not in c2.Action:
                    c.HeadConfidence = 3
                    c.HeadOffset = tokencount_2 + 1 + tokencount_4 - VirtualTokenNum1 - VirtualTokenNum2
                    c2.Action += " H ^.H "  # add Head for the chunk.
                elif "^^." not in c1.Action:
                    c.HeadConfidence = 3
                    c.HeadOffset = tokencount_2 - VirtualTokenNum1
                    c1.Action += " H ^.H "  # add Head for the chunk.

            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c,
                                                       StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5 + tokencount_6 + tokencount_7,
                                                       Length=tokencount_8,
                                                       HeadOffset=tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6 + 1,
                                                       EnableLowCHead=False)
            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c,
                                                       StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5,
                                                       Length=tokencount_6,
                                                       HeadOffset=tokencount_2 + 1 + tokencount_4 + 1,
                                                       EnableLowCHead=True)
            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c,
                                                       StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                       Length=tokencount_4,
                                                       HeadOffset=tokencount_2 + 1, EnableLowCHead=True)

            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2,
                                                  HeadOffset=0, EnableLowCHead=True)

            if c.HeadOffset == -1:
                logging.error("Failed to find Head in this rule:{}".format(self))

            c.StringChunkLength = c.Length - VirtualTokenNum1 - VirtualTokenNum2 - VirtualTokenNum3 - VirtualTokenNum4

            self.Chunks.append(c)
        elif Chunk2_2:  # "(.*)<(.*)<(.+)>(.*)<(.+)>(.*)>(.*)"
            tokencount_1 = Chunk2_2.group(1).count('[')
            tokencount_2 = Chunk2_2.group(2).count('[')
            tokencount_3 = Chunk2_2.group(3).count('[')
            tokencount_4 = Chunk2_2.group(4).count('[')
            tokencount_5 = Chunk2_2.group(5).count('[')
            tokencount_6 = Chunk2_2.group(6).count('[')
            c1 = self.CreateChunk(tokencount_1 + tokencount_2, tokencount_3)
            self.Chunks.append(c1)
            c2 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3 + tokencount_4, tokencount_5)
            self.Chunks.append(c2)

            c = RuleChunk()
            c.ChunkLevel = 2
            c.StartOffset = tokencount_1
            c.Length = tokencount_2 + 1 + tokencount_4 + 1 + tokencount_6

            # check the part before first inner chuck.
            VirtualTokenNum1 = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2,
                                                                     HeadOffset=0, EnableLowCHead=False)

            # check the part after first inner chuck, before second inner chuck.
            VirtualTokenNum2 = self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                                      Length=tokencount_4, HeadOffset=tokencount_2 + 1, EnableLowCHead=False)

            # check the part after second inner chuck.
            VirtualTokenNum3 = self.CheckTokensForHeadAndVirtualToken(c,
                                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5,
                                                                      Length=tokencount_6,
                                                                      HeadOffset=tokencount_2 + 1 + tokencount_4 + 1, EnableLowCHead=False)

            if c.HeadOffset == -1:
                if "^^." not in c2.Action:
                    c.HeadConfidence = 3
                    c.HeadOffset = tokencount_2 + 1 + tokencount_4 - VirtualTokenNum1 - VirtualTokenNum2
                    c2.Action += " H ^.H "  # add Head for the chunk.
                elif "^^." not in c1.Action:
                    c.HeadConfidence = 3
                    c.HeadOffset = tokencount_2 - VirtualTokenNum1
                    c1.Action += " H ^.H "  # add Head for the chunk.

            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c,
                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5,
                                                      Length=tokencount_6,
                                                      HeadOffset=tokencount_2 + 1 + tokencount_4 + 1,
                                                      EnableLowCHead=True)
            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c,
                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                      Length=tokencount_4, HeadOffset=tokencount_2 + 1, EnableLowCHead=True)
            if c.HeadOffset == -1:
                self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset,
                                                     Length=tokencount_2, HeadOffset=0, EnableLowCHead=True)

            if c.HeadOffset == -1:
                logging.error("Failed to find Head in this rule:{}".format(self))

            c.StringChunkLength = c.Length - VirtualTokenNum1 - VirtualTokenNum2 - VirtualTokenNum3

            self.Chunks.append(c)
        elif Chunk2_1:  # "(.*)<(.*)<(.+)>(.*)>(.*)"
            tokencount_1 = Chunk2_1.group(1).count('[')
            tokencount_2 = Chunk2_1.group(2).count('[')
            tokencount_3 = Chunk2_1.group(3).count('[')
            tokencount_4 = Chunk2_1.group(4).count('[')
            c1 = self.CreateChunk(tokencount_1 + tokencount_2, tokencount_3)
            self.Chunks.append(c1)

            c = RuleChunk()
            c.ChunkLevel = 2
            c.StartOffset = tokencount_1
            c.Length = tokencount_2 + 1 + tokencount_4

            # check the part before inner chuck.
            VirtualTokenNum1 = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2,
                                                     HeadOffset=0, EnableLowCHead=False)

            # check the part after inner chuck.
            VirtualTokenNum2 = self.CheckTokensForHeadAndVirtualToken(c,
                                                      StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                      Length=tokencount_4, HeadOffset=tokencount_2 + 1, EnableLowCHead=False)

            if c.HeadOffset == -1:
                if "^^." not in c1.Action:
                    c.HeadConfidence = 3
                    c.HeadOffset = tokencount_2-VirtualTokenNum1
                    c1.Action += " H ^.H "  # add Head for the head token.


            if c.HeadOffset == -1:
                # check the part after inner chuck.
                self.CheckTokensForHeadAndVirtualToken(c,
                                                       StartOffset=c.StartOffset + tokencount_2 + tokencount_3,
                                                       Length=tokencount_4, HeadOffset=tokencount_2 + 1,
                                                       EnableLowCHead=True)

            if c.HeadOffset == -1:
                # check the part before inner chuck.
                self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset, Length=tokencount_2,
                                                        HeadOffset=0, EnableLowCHead=True)

            if c.HeadOffset == -1:
                logging.error("Failed to find Head in this rule:{}".format(self))

            c.StringChunkLength = c.Length - VirtualTokenNum1 - VirtualTokenNum2
            self.Chunks.append(c)

        elif Chunk1_3:  # "(.*)<(.+)>(.*)<(.+)>(.*)<(.+)>(.*)"
            tokencount_1 = Chunk1_3.group(1).count('[')
            tokencount_2 = Chunk1_3.group(2).count('[')
            c1 = self.CreateChunk(tokencount_1, tokencount_2)
            self.Chunks.append(c1)

            tokencount_3 = Chunk1_3.group(3).count('[')
            tokencount_4 = Chunk1_3.group(4).count('[')
            c2 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3, tokencount_4)
            self.Chunks.append(c2)

            tokencount_5 = Chunk1_3.group(5).count('[')
            tokencount_6 = Chunk1_3.group(6).count('[')
            c3 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3 + tokencount_4 + tokencount_5,
                                  tokencount_6)
            self.Chunks.append(c3)

        elif Chunk1_2:  # "(.*)<(.+)>(.*)<(.+)>(.*)"
            tokencount_1 = Chunk1_2.group(1).count('[')
            tokencount_2 = Chunk1_2.group(2).count('[')
            c1 = self.CreateChunk(tokencount_1, tokencount_2)
            self.Chunks.append(c1)

            tokencount_3 = Chunk1_2.group(3).count('[')
            tokencount_4 = Chunk1_2.group(4).count('[')
            c2 = self.CreateChunk(tokencount_1 + tokencount_2 + tokencount_3, tokencount_4)
            self.Chunks.append(c2)

        elif Chunk1_1:  # "(.*)<(.+)>(.*)"
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

        # # add default relation ship.
        # leave this to runtime, node.ApplyDefaultUpperRelationship()
        # for token in self.Tokens:
        #     if token.SubtreePointer:  # ignore the token that already has relation.
        #         continue
        #     if token.word != "[]" and "^" not in token.action:
        #         # if "+++" in chunk.Action:         #Can't identify whether it is in +++ or not
        #         #     self.Tokens[i].action += " ^.x"
        #         # else:
        #             token.action += " ^.X"

        for chunk in self.Chunks:
            if chunk.StringChunkLength == 1:  # remove single node chunk. remove "H" in this single node.
                headtoken = self.Tokens[chunk.StartOffset + chunk.HeadOffset]
                headaction = headtoken.action.split()
                while "H" in headaction:
                    headaction.pop(headaction.index("H"))
                while "^.H" in headaction:
                    headaction.pop(headaction.index("^.H"))
                headaction += chunk.Action.split()

                headtoken.action = " ".join(headaction)

                self.Chunks.pop(self.Chunks.index(chunk))


    def CheckTokensForVirtualToken(self, StartOffset, Length):
        VirtualTokenNum = 0  # Those "^V=xxx" is virtual token that does not apply to real string token
        for i in range(Length):
            token = self.Tokens[StartOffset + i]
            if token.SubtreePointer:
                VirtualTokenNum += 1

        return VirtualTokenNum


    def CheckTokensForHeadAndVirtualToken(self, c, StartOffset, Length, HeadOffset=0, EnableLowCHead = True):
        VirtualTokenNum = 0  # Those "^V=xxx" is virtual token that does not apply to real string token
        if Length == 0:
            return 0

        for i in range(Length):
            token = self.Tokens[StartOffset + i]
            if token.SubtreePointer:
                VirtualTokenNum += 1
                continue  # VirtualToken will NOT be head.

            if "H" in token.action.split():
                c.HeadConfidence = 5
                c.HeadOffset = HeadOffset + i
                c.Action, token.action = self.ExtractParentSonActions(token.action)
            elif token.pointer == "^H":
                if c.HeadConfidence < 5:
                    c.HeadConfidence = 4
                    c.HeadOffset = HeadOffset + i
                    c.Action, token.action = self.ExtractParentSonActions(token.action)

        if c.HeadConfidence < 3 and EnableLowCHead:
            for i in range(Length):
                token = self.Tokens[StartOffset + i]
                if token.SubtreePointer:
                    continue  # VirtualToken will NOT be head.

                elif "^^." in token.action or "++" in token.action:
                    if c.HeadConfidence < 4:
                        c.HeadConfidence = 3
                        c.HeadOffset = HeadOffset + i
                        c.Action, token.action = self.ExtractParentSonActions(token.action)

                elif not token.action:
                    if c.HeadConfidence < 3:
                        c.HeadConfidence = 2
                        c.HeadOffset = HeadOffset + i
                        c.Action, token.action = self.ExtractParentSonActions(token.action)
                elif "^.H" in token.action or "^." not in token.action:
                    if c.HeadConfidence < 3:
                        c.HeadConfidence = 1
                        c.HeadOffset = HeadOffset + i
                        c.Action, token.action = self.ExtractParentSonActions(token.action)

        if c.HeadConfidence > 0:
            self.Tokens[StartOffset + c.HeadOffset - HeadOffset].action += " H ^.H "  # add Head for the head token.
            for i in range(StartOffset, StartOffset + c.HeadOffset - HeadOffset):
                token = self.Tokens[i]
                if token.SubtreePointer:
                    c.HeadOffset -= 1  # this number will be used to specify which node's property to copy to the chunk node.

        return VirtualTokenNum

    def CreateChunk(self, StartOffset, Length, ChunkLevel=1):
        c = RuleChunk()
        c.StartOffset = StartOffset
        c.Length = Length
        VirtualTokenNum = self.CheckTokensForHeadAndVirtualToken(c, StartOffset=c.StartOffset,
                                                                 Length=Length, HeadOffset=0)

        if c.HeadOffset == -1:
            if not self.RuleName.startswith("CleanRule"):
                logging.warning("Can't find head in this rule:")
                logging.warning("\tSet to the last token")
                logging.warning(self.Origin)
                logging.warning(str(self))
            c.HeadOffset = c.Length

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

    #RuleContent = RemoveExcessiveSpace(RuleContent)

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
        node.word = node.word.replace("\\(", IMPOSSIBLESTRINGLP).replace("\\)", IMPOSSIBLESTRINGRP).replace("\\'",
                                      IMPOSSIBLESTRINGSQ).replace("\\:", IMPOSSIBLESTRINGCOLN).replace("\\=", IMPOSSIBLESTRINGEQUAL)
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

        ActionPosition = node.word.find(":")
        if ActionPosition > 0:
            if ")" not in node.word[ActionPosition:] and "[" not in node.word[ActionPosition:]:
                node.action = node.word[ActionPosition + 1:].rstrip("]")
                node.word = node.word[:ActionPosition] + "]"

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

        # Note: unification would be quoted, such as <['^V-' ] [不] ^V[V|V0|v]>
        # so it won't be pointer or subtree pointer.
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

        pointerSubtreeMatch = re.search("\[(\^(.+)=)", node.word, re.DOTALL)  # Subtree Pattern
        if pointerSubtreeMatch:
            node.word = node.word.replace(pointerSubtreeMatch.group(1), "")
            node.SubtreePointer = pointerSubtreeMatch.group(2)

        pointerSubtreeMatch = re.search("\[(\^(.+?) )", node.word, re.DOTALL)  # Subtree Pattern
        if pointerSubtreeMatch:
            node.word = node.word.replace(pointerSubtreeMatch.group(1), "")
            node.SubtreePointer = pointerSubtreeMatch.group(2)

        pointerSubtreeMatch = re.search("\[(\^(\S+))\]", node.word, re.DOTALL)  # Subtree Pattern
        if pointerSubtreeMatch:
            node.word = node.word.replace(pointerSubtreeMatch.group(1), "")
            node.SubtreePointer = pointerSubtreeMatch.group(2)

        if node.SubtreePointer:  # remove all the "^" sign inside the SubtreePointer
            node.SubtreePointer = node.SubtreePointer.replace("^", "")

        orQuoteMatch = re.search("(['\"/])(\S*\|\S*?)\\1", node.word, re.DOTALL)
        if orQuoteMatch:
            expandedQuotes = ExpandQuotedOrs(orQuoteMatch.group(2), orQuoteMatch.group(1))
            node.word = node.word.replace(orQuoteMatch.group(2), expandedQuotes)

        notOrMatch = re.findall("!(\S*\|\S*)", node.word, re.DOTALL)
        if notOrMatch:
            for match in notOrMatch:
                expandAnd = ExpandNotOrToAndNot(match)
                node.word = node.word.replace(match, expandAnd)

        notOrMatch = re.findall("!\(\S*?\)\|(\S*)", node.word, re.DOTALL)
        if notOrMatch:
            for match in notOrMatch:
                expandAnd = ExpandNotOrToAndNot(match)
                node.word = node.word.replace("|" + match, " !" + expandAnd)

        notOrMatch = re.findall("!([^() ]*)\|(\(\S*?\))", node.word, re.DOTALL)
        if notOrMatch:
            for match in notOrMatch:
                expandAnd = ExpandNotOrToAndNot(match.group(1))
                node.word = node.word.replace(match.group(0) + "|", expandAnd + " !")

        notOrMatch = re.findall("!\(([^() ]*\|[^() ]*)\)", node.word, re.DOTALL)
        if notOrMatch:
            for match in notOrMatch:
                expandAnd = ExpandNotOrToAndNot(match)
                node.word = node.word.replace("(" + match + ")", expandAnd)

        if node.word and len(node.word) > 1 and node.word[0] == '[' and ChinesePattern.match(node.word[1]):
            node.word = '[FULLSTRING ' + node.word[
                                         1:]  # If Chinese character is not surrounded by quote, then add feature 0.

        node.word = node.word.replace(IMPOSSIBLESTRINGLP, "(").replace(IMPOSSIBLESTRINGRP, ")").replace(
            IMPOSSIBLESTRINGSQ, "'").replace(IMPOSSIBLESTRINGCOLN, ":").replace(IMPOSSIBLESTRINGEQUAL, "=").replace(
            "\>", ">").replace("\<", "<")
        node.action = node.action.replace(IMPOSSIBLESTRINGLP, "(").replace(IMPOSSIBLESTRINGRP, ")").replace(
            IMPOSSIBLESTRINGSQ, "'").replace(IMPOSSIBLESTRINGCOLN, ":").replace(IMPOSSIBLESTRINGEQUAL, "=")


# Avoid [(AS:action)|sjfa]
# Good character in action:
#     ^.M $
# Bad characters in action:
#     )?':
# def FindLastColonWithoutSpecialCharacter(string):
#     index = len(string) - 2
#     while index >= 0:
#         if string[index] == ":":
#             return index
#         if string[index].isalnum() or \
#                         string[index] in "^. $,>+-":
#             index -= 1
#         else:
#             #            logging.warning("not a ligit action: " + string[index] + " in " + string )
#             return -1
#     return -1  'abc'|'cde'|'dfs' = 'abc'|'cde'

def ExpandQuotedOrs(text, sign):
    if "(" in text:
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Not a task in this ExpandQuotedOrs function for expanding " + text)
        return text
    if sign in text[1:-1]:
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("There is sign " + str(sign) + " inside of text, no need to do expanding:\n {}".format(text))
        return text

    return text.replace("|", sign + "|" + sign)


def ExpandNotOrToAndNot(text):
    if "(" in text:
        logging.debug("Not a task in this ExpandNotOrTo function for expanding " + text)
        return text
    if "!" in text:
        logging.error("there should be no ! in text:" + text)
        raise Exception("There should be no ! for this rule")
    return " !".join(text.split("|"))


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


def LoadGlobalMacro(RuleLocation):
    if RuleLocation.startswith("."):
        RuleLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), RuleLocation)

    rule = ''
    try:
        with open(RuleLocation, encoding="utf-8") as RuleFile:
            for line in RuleFile:
                line = line.strip().replace("：", ":")
                if not line:
                    continue

                code, _ = SeparateComment(line)
                if code.find("::") >= 0 or code.find("==") >= 0:
                    if rule:
                        node = Rule()
                        node.SetRule(rule, _GlobalMacroDict)
                        if node.RuleContent:
                            if node.RuleName.startswith("@") or node.RuleName.startswith("#"):
                                if node.RuleName in _GlobalMacroDict:
                                    logging.warning(
                                        "This macro name " + node.RuleName + " is already used for Macro " + str(
                                            _GlobalMacroDict[node.RuleName]) \
                                        + " \n but now you have: " + rule + "\n\n")
                                    logging.warning("The new one will be used to replace the old one.")
                                _GlobalMacroDict.update({node.RuleName: node})
                            else:
                                logging.error("There should be no rule in this Global Macro File:" + rule)

                        rule = ""
                rule += "\n" + line

            if rule:  # last one
                node = Rule()
                node.SetRule(rule, _GlobalMacroDict)
                if node.RuleContent:
                    if node.RuleName.startswith("@") or node.RuleName.startswith("#"):
                        if node.RuleName in _GlobalMacroDict:
                            logging.warning(
                                "This macro name " + node.RuleName + " is already used for Macro " + str(
                                    _GlobalMacroDict[node.RuleName]) \
                                + " \n but now you have: " + rule + "\n\n")
                            logging.warning("The new one will be used to replace the old one.")
                        _GlobalMacroDict.update({node.RuleName: node})
                    else:
                        logging.error("There should be no rule in this Global Macro File:" + rule)

    except UnicodeError:
        logging.error("Error when processing Global Macro file " + RuleLocation)
        logging.error("Currently rule=" + rule)


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
def LoadRules(RuleFolder, RuleFileName,systemfileolderthanDB, fuzzy=False):
    # global UnitTest, RuleFileList
    global RuleGroupDict

    RuleLocation = os.path.join(RuleFolder, RuleFileName)
    if RuleLocation.startswith("."):
        RuleLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), RuleLocation)

    logging.info("Start Loading Rule " + RuleLocation)
    rulegroup = RuleGroup(RuleFileName)

    # check if feature.txt and global macro is changed before load rules from DB

    if systemfileolderthanDB and RuleFileOlderThanDB(RuleLocation):
        rulegroup.LoadedFromDB = True
        LoadRulesFromDB(rulegroup)

    else:
        rulegroup.LoadedFromDB = False
        rule = ""
        try:
            with open(RuleLocation, encoding="utf-8") as RuleFile:
                for line in RuleFile:
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
        except UnicodeError:
            logging.error("Error when processing " + RuleFileName)
            logging.error("Currently rule=" + rule)
        # UnitTestFileName = os.path.splitext(RuleLocation)[0] + ".unittest"
        # if os.path.exists(UnitTestFileName):
        #     # First delete the unit test of current file to have clean plate
        #     del rulegroup.UnitTest[:]
        #     with open(UnitTestFileName, encoding="utf-8") as RuleFile:
        #         for line in RuleFile:
        #             RuleName, TestSentence = SeparateComment(line)
        #             unittest = UnitTestNode(RuleName, TestSentence.strip("//"))
        #             rulegroup.UnitTest.append(unittest)

        RuleNum_BeforeExpand = len(rulegroup.RuleList)
        while _ExpandRuleWildCard_List(rulegroup.RuleList):
            pass

        Modified = True
        while Modified:
            Modified = _ExpandParenthesis(rulegroup.RuleList)
            Modified = _ExpandOrBlock(rulegroup.RuleList) or Modified

        while _ExpandRuleWildCard_List(rulegroup.RuleList):
            pass

        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList, fuzzy)
        _PreProcess_CompileHash(rulegroup)
        rulegroup.RuleList = sorted(rulegroup.RuleList, key=lambda x: (x.Priority, x.TokenLength, x.RuleName), reverse=True)
        if not utils.DisableDB:
            _OutputRuleDB(rulegroup)
        for r in rulegroup.RuleList:
            if r.norms:
                norms = "".join(r.norms)
                rulegroup.HashRules[norms] = r
            else:
                rulegroup.NoHashRules.append(r)
        RuleNum_AfterExpand = len(rulegroup.RuleList)
        logging.info("Rules from file:" + str(RuleNum_BeforeExpand) + " \t After expanded:" + str(RuleNum_AfterExpand))

    # BuildIdenticalNetwork(rulegroup)

    RuleGroupDict.update({rulegroup.FileName: rulegroup})

    logging.info("Finished Loading Rule " + RuleFileName + " LoadedFromDB:" + str(rulegroup.LoadedFromDB))
    logging.info("\t Rule Size:" + str(len(rulegroup.RuleList)))

    return


# def BuildIdenticalNetwork(rg):
#     for rule in rg.RuleList:
#         for i in range( rule.TokenLength-1):
#             if rule.Tokens[i].word == "[]" or rule.Tokens[i].word == "":
#                 continue
#             for comparerule in rg.RuleList:
#                 if comparerule.ID == rule.ID:
#                     continue
#                 if comparerule.TokenLength < i+1:
#                     continue
#                 if comparerule.TokenLength > rule.TokenLength:
#                     continue    #only care for the rules that is shorter.
#                 Identical = True
#                 for j in range(i+1):
#                     if rule.Tokens[j] != comparerule.Tokens[j]:
#                         Identical = False
#                         break
#                 if Identical:
#                     if (rule.ID, i) not in RuleIdenticalNetwork:
#                         RuleIdenticalNetwork[(rule.ID, i)] = set()
#                     RuleIdenticalNetwork[(rule.ID, i)].add(comparerule.ID)




def RuleFileOlderThanDB(RuleLocation):
    #return False
    if utils.DisableDB:
        return False

    cur = utils.DBCon.cursor()
    RuleFileName = os.path.basename(RuleLocation)
    if RuleFileName == "5ngramKG9_top1k.txt":
        RuleFileName = "Q/rule/5ngramKG9_top1k.txt"
    strsql = "select ID, verifytime from rulefiles where filelocation=?"
    cur.execute(strsql, [RuleFileName, ])
    resultrecord = cur.fetchone()
    cur.close()

    if not resultrecord or not resultrecord[1]:
        return False

    FileDBTime = resultrecord[1]  # utc time.
    FileDiskTime = datetime.utcfromtimestamp(os.path.getmtime(RuleLocation)).strftime('%Y-%m-%d %H:%M:%S')

    #    logging.info("Disk:" + str(FileDiskTime + "  DB:" + str(FileDBTime)))
    return FileDiskTime < FileDBTime



def LoadRulesFromDB(rulegroup):
    if utils.DisableDB:
        logging.error("In the config.ini, DisableDB is true, so it is not supposed to LoadrulesFromDB!")
        return False
    cur = utils.DBCon.cursor()
    strsql = "select ID from rulefiles where filelocation=?"
    cur.execute(strsql, [rulegroup.FileName, ])
    resultrecord = cur.fetchone()
    if not resultrecord:
        logging.error("Trying to load rules from DB for :" + rulegroup.FileName)
        return False
    rulefileid = resultrecord[0]

    # order by tokenlength desc, and by hits desc.
    # note: order using hit can have less than 1% benefit. not worth the trouble.
    strsql_rule = """SELECT id, name, strtokenlength, tokenlength, norms, origin, comment,
                    priority, windowlimit, lengthlimit
                    from ruleinfo r  left join rulehits h on r.id=h.ruleid   where rulefileid=? and status=1 group by r.id
                        order by tokenlength desc, count(h.ruleid ) desc """
    # strsql_rule = """SELECT id, name, strtokenlength, norms, origin, comment
    #                 from ruleinfo r    where rulefileid=?
    #                     order by tokenlength desc"""
    strsql_node = """SELECT ID, matchbody, action, pointer, subtreepointer, andtext, andtextmatchtype, nottextmatchtype from rulenodes where ruleid=? order by sequence"""
    #strsql_node_feature = "select featureid from rulenode_features where rulenodeid=? and type=?"
    strsql_node_orfeature = "select featureid from rulenode_orfeatures where rulenodeid=? and groupid=?"
    strsql_countorfeatures = "select count(DISTINCT groupid) from rulenode_orfeatures where rulenodeid=?"
    strsql_node_text = "select text from rulenode_texts where rulenodeid=? and type=?"
    #    strsql_node_text = "INSERT into rulenode_texts (rulenodeid, text, type) values(?,?,?)"
    strsql_chunk = "SELECT chunklevel, startoffset, length, stringchunklength, headoffset, action from rulechunks where ruleid=? "

    cur.execute(strsql_rule, [rulefileid, ])
    rows = cur.fetchall()
    for row in rows:
        rule = Rule()
        rule.FileName = rulegroup.FileName
        rule.ID = int(row[0])
        rule.RuleName = row[1]
        rule.StrTokenLength = int(row[2])
        rule.TokenLength = int(row[3])
        if row[4]:
            rule.norms = [x.replace(IMPOSSIBLESTRINGSLASH, "/") for x in row[4].split("/")]
        else:
            rule.norms = []
        rule.Origin = row[5]
        rule.comment = row[6]
        rule.Priority = row[7]
        rule.WindowLimit = row[8]
        rule.LengthLimit = row[9]

        cur.execute(strsql_node, [rule.ID, ])
        noderows = cur.fetchall()
        for noderow in noderows:
            token = RuleToken()
            nodeid = int(noderow[0])
            token.word = noderow[1]
            if "FULLSTRING" in token.word:
                token.FullString = True
            token.action = noderow[2]
            token.pointer = noderow[3]
            token.SubtreePointer = noderow[4]
            token.AndText = noderow[5]
            token.AndTextMatchtype = noderow[6]
            token.NotTextMatchtype = noderow[7]


            cur.execute(strsql_countorfeatures,[nodeid])
            countrows = cur.fetchall()
            sizefeaturegroup = countrows[0][0]
            # sizefeaturegroup = int(cur.execute(strsql_countorfeatures,[nodeid]))
            for groupid in range(0, sizefeaturegroup):
                cur.execute(strsql_node_orfeature,[nodeid,groupid])
                featurerows = cur.fetchall()
                orfeaturegroup = set()
                for featurerow in featurerows:
                    orfeaturegroup.add(int(featurerow[0]))
                token.OrFeatureGroups.append(orfeaturegroup)

            # cur.execute(strsql_node_feature, [nodeid, 1])
            # featurerows = cur.fetchall()
            # for featurerow in featurerows:
            #     token.AndFeatures.add(int(featurerow[0]))
            # cur.execute(strsql_node_feature, [nodeid, 3])
            # featurerows = cur.fetchall()
            # for featurerow in featurerows:
            #     token.NotFeatures.add(int(featurerow[0]))
            #
            cur.execute("select featureid, type from rulenode_features where rulenodeid=?", [nodeid])
            featurerows = cur.fetchall()
            for featurerow in featurerows:
                if featurerow[1] == 1:
                    token.AndFeatures.add(featurerow[0])
                elif featurerow[1] == 3:
                    token.NotFeatures.add(featurerow[0])
                else:
                    logging.warning("There is other feature type in: {} for this rule {}".format(featurerow, rule))

            cur.execute(strsql_node_text, [nodeid, 2])
            featurerows = cur.fetchall()
            for featurerow in featurerows:
                token.NotTexts.add(featurerow[0])

            rule.Tokens.append(token)

        cur.execute(strsql_chunk, [rule.ID, ])
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
    cur.execute(strsql, [rulegroup.FileName, ])
    rulegroup.LoadedFromDB = True
    cur.close()
    return True


def InsertRuleInList(string, rulegroup):
    node = Rule()
    node.FileName = rulegroup.FileName  # used in keeping record of the winning rules.
    remaining = node.SetRule(string, rulegroup.MacroDict)
    if node.RuleContent:
        if node.RuleName.startswith("@") or node.RuleName.startswith("#"):
            if node.RuleName in rulegroup.MacroDict:
                logging.warning("This macro name " + node.RuleName + " is already used for Macro " + str(
                    rulegroup.MacroDict[node.RuleName]) \
                                + " \n but now you have: " + string + "\n\n")
                logging.warning("The new one will be used to replace the old one.")
            rulegroup.MacroDict.update({node.RuleName: node})
        else:
            rulegroup.RuleList.append(node)

    if remaining:
        RuleName = GetPrefix(node.RuleName) + "_" + str(node.ID)
        if node.RuleContent:  # the last was one rule, so we know the rest should be
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
            if code:
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
        for tokenindex in range(rule.TokenLength):
            token = rule.Tokens[tokenindex]
            if token.repeat != [1, 1]:
                for repeat_num in range(token.repeat[0], token.repeat[1] + 1):
                    newrule = Rule(rule)
                    newrule.RuleName = rule.RuleName + "_" + str(repeat_num)
                    newrule.Tokens.clear()
                    for tokenindex_pre in range(tokenindex):
                        newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_pre]))
                    for tokenindex_this in range(repeat_num):
                        new_node = RuleToken(rule.Tokens[tokenindex])
                        new_node.repeat = [1, 1]
                        if tokenindex_this != 0 and rule.Tokens[tokenindex].StartChunk != 0:
                            new_node.StartChunk = 0  # in the copies, only the first one can be StartChunk
                        if tokenindex_this != repeat_num - 1 and rule.Tokens[tokenindex].EndChunk != 0:
                            new_node.EndChunk = 0  # in the copies, only the last one can be EndChunk
                        newrule.Tokens.append(new_node)

                    NextIsStart = False
                    NextIsRestart = False
                    # NextIsPointer = False
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
                        # if origin_node.pointer:   #20180628: don't remember the requirement of this part. comment out.
                        #     NextIsPointer = True
                        #     NextPointer = origin_node.pointer
                    for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                        new_node = RuleToken(rule.Tokens[tokenindex_post])
                        if tokenindex_post == tokenindex + 1:
                            if NextIsStart:
                                new_node.StartChunk = origin_node.StartChunk
                            if NextIsRestart:
                                new_node.RestartPoint = True
                            # if NextIsPointer and NextPointer:
                            #     new_node.pointer = NextPointer
                            #     logging.error("Some operation of the NextIsPointer:{}".format(rule))
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
            token.word[StartParenthesesPosition - 1] == "'" and token.word[StartParenthesesPosition + 1] == "'":
        logging.debug("_RemoveExcessiveParenthesis: Quoted. Ignore this parentheses:" + str(token))
        return False
    if StartParenthesesPosition > 0 and \
            token.word[StartParenthesesPosition - 1].isalpha():
        logging.debug("_RemoveExcessiveParenthesis: Alpha before it. Ignore this parentheses:" + str(token))
        return False
    EndParenthesesPosition = StartParenthesesPosition + 1 + SearchPair(token.word[StartParenthesesPosition + 1:], "()")
    if EndParenthesesPosition == StartParenthesesPosition:  # not paired
        logging.warning("The parenthesis are not paired:" + token.word + " in this token:\n" + str(token))
        return False

    if "]" in token.word[StartParenthesesPosition:EndParenthesesPosition] \
            or ":" in token.word[StartParenthesesPosition:EndParenthesesPosition]:
        return False  # not excessive, if ]: in parenthesis.

    if (StartParenthesesPosition == 0 or token.word[StartParenthesesPosition - 1] not in "|!") \
            and (EndParenthesesPosition == len(token.word) or token.word[EndParenthesesPosition + 1] != "|"):
        if StartParenthesesPosition > 0:
            before = token.word[:StartParenthesesPosition]
        else:
            before = ""
        if EndParenthesesPosition < len(token.word):
            after = token.word[EndParenthesesPosition + 1:]
        else:
            after = ""

        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Removing excessive parenthesis in: " + token.word)
        token.word = before + token.word[StartParenthesesPosition + 1:EndParenthesesPosition] + after
        # logging.info("\t\t as: " + token.word)
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
        for tokenindex in range(rule.TokenLength):
            if _RemoveExcessiveParenthesis(rule.Tokens[tokenindex]):
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

                newrule = Rule(rule)
                newrule.RuleName = rule.RuleName + "_p" + str(tokenindex)
                newrule.Tokens.clear()
                for tokenindex_pre in range(tokenindex):
                    newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_pre]))
                for subtoken in subTokenlist:
                    newrule.Tokens.append(subtoken)
                for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                    newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_post]))
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

    # if left/right block is enclosed by (), and it is part of one token , then the () can be removed:
    # write out in log as confirmation.
    if Content[0] == "[" and SearchPair(Content[1:], "[]") == len(Content) - 2:
        if leftBlock[0] == "(" and SearchPair(leftBlock[1:], "()") == len(leftBlock) - 2:
            # logging.debug("New kind of removing (): Removing them from " + leftBlock + " in :\n" + Content)
            leftBlock = leftBlock[1:-1]
        if rightBlock[0] == "(" and SearchPair(rightBlock[1:], "()") == len(rightBlock) - 2:
            # logging.debug("New kind of removing (): Removing them from " + rightBlock + " in :\n" + Content)
            rightBlock = rightBlock[1:-1]
    else:
        if "[" not in originBlock:
            if leftBlock[0] == "(" and SearchPair(leftBlock[1:], "()") == len(leftBlock) - 2:
                # logging.debug("Extra New kind of removing (): Removing them from " + leftBlock + " in :\n" + Content)
                leftBlock = leftBlock[1:-1]
            if rightBlock[0] == "(" and SearchPair(rightBlock[1:], "()") == len(rightBlock) - 2:
                # logging.debug("Extra New kind of removing (): Removing them from " + rightBlock + " in :\n" + Content)
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
        for tokenindex in range(rule.TokenLength):
            token = rule.Tokens[tokenindex]

            orIndex = token.word.find(")|") + 1
            if orIndex <= 0:
                orIndex = token.word.find("|(")
                if orIndex <= 0:
                    orIndex = token.word.find("]|[")
                    if orIndex <= 0:
                        continue
                    else:
                        orIndex += 1  # move the pointer from ] to |
            # if (token.word[0] == "!" or token.word[0:2] == "[!") \
            #         and (token.word.find(")|")>0 or token.word.find("|(")>0):
            if re.search("![^ )]*\|\(", token.word) or re.search("!\(.*\)\|", token.word):
                logging.warning(
                    "_ExpandOrBlock: Not Or means Not And in this word:{} in rule {}".format(token.word, rule.RuleName))
                token.word = token.word.replace("|", " !")
                logging.info("\t After modification, the word is: {}".format(token.word))
                Modified = True
                continue

            originBlock, leftBlock, rightBlock = _ProcessOrBlock(token.word, orIndex)
            if originBlock is None:
                logging.error("ExpandOrBlock: Failed to process or block for: \n" + str(rule))
                continue  # failed to process. might be pair tag issue.

            # left of |:
            newrule = Rule(rule)
            newrule.RuleName = rule.RuleName + "_ol" + str(tokenindex)
            newrule.Tokens.clear()

            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_pre]))

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
                if token.SubtreePointer:
                    if len(subTokenlist) > 1:
                        logging.warning("The block has Subtreepointer for multiple subtokens!")
                    subTokenlist[-1].SubtreePointer = token.SubtreePointer

            for subtoken in subTokenlist:
                newrule.Tokens.append(subtoken)

            for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_post]))
            newrule.SetStrTokenLength()
            OneList.append(newrule)

            # right of |:
            newrule = Rule(rule)
            newrule.RuleName = rule.RuleName + "_or" + str(tokenindex)
            newrule.Tokens.clear()

            for tokenindex_pre in range(tokenindex):
                newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_pre]))

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
                if token.SubtreePointer:
                    if len(subTokenlist) > 1:
                        logging.warning("The block has Subtreepointer for multiple subtokens!")
                    subTokenlist[-1].SubtreePointer = token.SubtreePointer
            for subtoken in subTokenlist:
                newrule.Tokens.append(subtoken)

            for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_post]))
            newrule.SetStrTokenLength()
            OneList.append(newrule)

            Expand = True
            # logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
            break

        if Expand:
            OneList.remove(rule)
            Modified = True

    return Modified


# only expand the text, not the feature.
def _ProcessOrToken(word):
    word = word.strip("[|]")
    spaceseparated = word.split()
    i = 0
    for i in range(len(spaceseparated)):
        if spaceseparated[i].find("'|") > 0 or spaceseparated[i].find("/|") > 0 or spaceseparated[i].find("\"|") > 0 \
                or spaceseparated[i].find("|'") > 0 or spaceseparated[i].find("|/") > 0 or spaceseparated[i].find(
            "|\"") > 0:
            # this is the piece we need to separate
            break
    if i > 0:
        leftpieces = " ".join(spaceseparated[:i])
    else:
        leftpieces = ""

    if i < len(spaceseparated):
        rightpieces = " ".join(spaceseparated[i + 1:])
    else:
        rightpieces = ""

    orlist = spaceseparated[i].split("|")
    # textlist = [x for x in orlist if len(x)>2 and (x[0]=="'" and x[-1]=="'" or x[0]=="/" and x[-1]=="/"  or x[0]=="\"" and x[-1]=="\"")]
    # nottextlist = set(orlist) - set(textlist)

    # if nottextlist:
    #     orlist = ["|".join(sorted(nottextlist)) ] + textlist
    # else:
    #     orlist = textlist

    return orlist, "[" + leftpieces, rightpieces + "]"


# Expand | inside of one token without (). Should be done after the _ExpandOrBlock and compilation.
# in here, each "or" operator should be one feature or one word.
# Also Expand !(A B). Should be done after the _ExpandOrBlock and compilation.
# in here, each "or" operator should be one feature or one word.

def _ExpandOrToken(OneList):
    Modified = False
    # counter = 0
    for rule in OneList:
        if len(rule.RuleName) > 200:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + str(rule))
            continue
        Expand = False
        for tokenindex in range(rule.TokenLength):
            orlist = None
            leftBlock = None
            rightBlock = None
            token = rule.Tokens[tokenindex]

            NotAnd = re.search("!\((\S*? .*)\)", token.word)
            if NotAnd:
                orlist, leftBlock, rightBlock = _ProcessOrToken_NotAnd(token.word, NotAnd)

            elif token.word.find("'|") > 0 or token.word.find("/|") > 0 or token.word.find("\"|") > 0 \
                    or token.word.find("|'") > 0 or token.word.find("|/") > 0 or token.word.find("|\"") > 0:
                # only expand the Text .
                orlist, leftBlock, rightBlock = _ProcessOrToken(token.word)
                if orlist is None:
                    logging.error("ExpandOrBlock: Failed to process or block for: \n" + str(rule))
                    continue  # failed to process. might be pair tag issue.

            if orlist:
                for orpiece in orlist:
                    # left of the token:
                    newrule = Rule(rule)
                    newrule.RuleName = rule.RuleName + "_ol" + str(tokenindex)
                    newrule.Tokens.clear()
                    for tokenindex_pre in range(tokenindex):
                        newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_pre]))

                    # current token
                    node = RuleToken(token)
                    node.word = leftBlock + " " + orpiece + " " + rightBlock
                    newrule.Tokens.append(node)

                    # right of the token:
                    for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                        newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_post]))
                    newrule.SetStrTokenLength()
                    newrule.Chunks = copy.deepcopy(rule.Chunks)
                    OneList.append(newrule)

                Expand = True
                # logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
                break  # don't work on the next | in this rule. wait for the next round.

            if token.SubtreePointer.find("|") > 0:
                SubtreePointer = token.SubtreePointer
                SubtreePointerExtra = ''
                ExtraMatch = re.match("(^.*?)([<>+].*)", SubtreePointer)
                if ExtraMatch:
                    SubtreePointer = ExtraMatch.group(1)
                    SubtreePointerExtra = ExtraMatch.group(2)


                for subtreepointer in SubtreePointer.split("|"):
                    # left of the token:
                    newrule = Rule(rule)
                    newrule.RuleName = rule.RuleName + "_ol" + str(tokenindex)
                    newrule.Tokens.clear()
                    for tokenindex_pre in range(tokenindex):
                        newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_pre]))

                    # current token
                    node = RuleToken(token)
                    node.SubtreePointer = subtreepointer + SubtreePointerExtra
                    newrule.Tokens.append(node)

                    # right of the token:
                    for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                        newrule.Tokens.append(RuleToken(rule.Tokens[tokenindex_post]))
                    newrule.SetStrTokenLength()
                    newrule.Chunks = copy.deepcopy(rule.Chunks)
                    OneList.append(newrule)

                Expand = True
                # logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
                break  # don't work on the next | in this rule. wait for the next round.

        if Expand:
            OneList.remove(rule)
            Modified = True

    Modified = _ExpandOrToken_Unification(OneList) | Modified

    if Modified:
        return _ExpandOrToken(OneList)
    else:
        return False


def _ProcessOrToken_NotAnd(word, match):
    word = word.strip("[|]")
    OriginalNotAndWord = match.group(0)
    NotAndString = match.group(1)
    orlist = []
    for x in NotAndString.split(" "):
        oritem = x.strip()
        if oritem:
            if oritem[0] == "!":
                orlist.append(oritem[1:])
            else:
                orlist.append("!" + oritem)

    leftindex = word.find(OriginalNotAndWord)
    leftpieces = word[:leftindex]
    rightpieces = word[leftindex + len(OriginalNotAndWord):]

    return orlist, "[" + leftpieces, rightpieces + "]"


def _ProcessOrToken_Unification(word, match):
    word = word.strip("[|]")
    OriginalUnificationWord = match.group(0)
    UnificationString = match.group(1)
    orlist = UnificationString.split("|")

    leftindex = word.find(OriginalUnificationWord)
    leftpieces = word[:leftindex]
    rightpieces = word[leftindex + len(OriginalUnificationWord):]

    return orlist, "[" + leftpieces, rightpieces + "]"


# Expand %F(per|animal|org|bodyPart|furniture)
def _ExpandOrToken_Unification(OneList):
    Modified = False
    # counter = 0
    for rule in OneList:
        if len(rule.RuleName) > 200:
            logging.error("Rule Name is too long. Stop processing this rule:\n" + str(rule))
            continue
        Expand = False
        for tokenindex in range(rule.TokenLength):
            orlist = None
            leftBlock = None
            rightBlock = None
            token = rule.Tokens[tokenindex]

            Unification = re.search("%F\((.*?)\)", token.word)
            if Unification:
                orlist, leftBlock, rightBlock = _ProcessOrToken_Unification(token.word, Unification)

            if orlist:
                for orpiece in orlist:
                    # left of the token:
                    newrule = Rule(rule)
                    newrule.RuleName = rule.RuleName + "_ol" + str(tokenindex)
                    newrule.Tokens.clear()
                    for tokenindex_pre in range(tokenindex):
                        newtoken = RuleToken(rule.Tokens[tokenindex_pre])
                        newtoken.word = newtoken.word.replace("%F", orpiece)
                        newrule.Tokens.append(newtoken)

                    # current token
                    node = RuleToken(token)
                    node.word = leftBlock + " " + orpiece + " " + rightBlock
                    newrule.Tokens.append(node)

                    # right of the token:
                    for tokenindex_post in range(tokenindex + 1, rule.TokenLength):
                        newtoken = RuleToken(rule.Tokens[tokenindex_post])
                        newtoken.word = newtoken.word.replace("%F", orpiece)
                        newrule.Tokens.append(newtoken)

                    newrule.SetStrTokenLength()
                    newrule.Chunks = copy.deepcopy(rule.Chunks)
                    OneList.append(newrule)

                Expand = True
                # logging.warning("\tExpand OrBlock is true, because of " + rule.RuleName)
                break  # don't work on the next | in this rule. wait for the next round.

        if Expand:
            OneList.remove(rule)
            Modified = True

    return Modified


# Check the rules. If it is a stem, not a feature, but omit quote
#   then we add quote;
# If it is like 'a|b|c', then we change it to 'a'|'b'|'c'
def _PreProcess_CheckFeaturesAndCompileChunk(OneList, fuzzy):
    for rule in OneList:
        for token in rule.Tokens:
            # _CheckFeature(token, rule.RuleName)
            token.word = "[" + _CheckFeature_returnword(token.word, fuzzy) + "]"
        rule.CompileChunk()
    _ExpandOrToken(OneList)


def _PreProcess_CompileHash(rulegroup):
    for rule in rulegroup.RuleList:
        for token in rule.Tokens:  # remove extra [] in match body.
            token.word = token.word.strip("[|]").strip()

            Features = token.word.split()
            for f in Features:
                if f[0] == "!":
                    if "\"" in f or "'" in f or "/" in f :
                        NotText, token.NotTextMatchtype = LogicOperation_CheckPrefix(f[1:])
                        token.NotTexts.add(NotText)
                    else:
                        token.NotFeatures.add(FeatureOntology.GetFeatureID(f[1:]))
                else:
                    if "|" in f:
                        OrFeatureGroup = set(FeatureOntology.GetFeatureID(x) for x in f.split("|"))
                        token.OrFeatureGroups.append(OrFeatureGroup)
                    elif "\"" in f or "'" in f or "/" in f or "." in f:
                        if token.AndText:
                            logging.error("There should be only one text in one token:" + str(rule))
                        token.AndText, token.AndTextMatchtype = LogicOperation_CheckPrefix(f)
                    else:
                        token.AndFeatures.add(FeatureOntology.GetFeatureID(f))

            if utils.FeatureID_FULLSTRING in token.AndFeatures:
                token.AndFeatures.remove(utils.FeatureID_FULLSTRING)
                token.FullString = True

        # rule.norms = [token.word.split("'")[1] if token.word.count("'") == 2 and token.word.split("'")[0][-1] != "!"
        #                                           and "^" not in token.word.split("'")[1] and "-" not in token.word.split("'")[1] else ''
        #               for token in rule.Tokens if not token.SubtreePointer ]
        rule.norms = [
            token.AndText.lower() if token.AndTextMatchtype == 'norm' and "-" not in token.AndText and token.AndText and "^" !=
                                     token.AndText[0] else ''
            for token in rule.Tokens if token.SubtreePointer == '']
        if len("".join(rule.norms)) == 0:
            rule.norms = []

        # if rule.norms and all(rule.norms): #all values are true
        #     logging.info("This rule is all norms:" + str(rule))
        #     logging.info("The norms are:" + "_".join(rule.norms))
        #     logging.info("The norms are:" + str(rule.norms))
        #
        #     #rulegroup.NormHash["".join(rule.norms)] = rule
        #     #rulegroup.RuleList.remove(rule)


def _PreProcess_RuleIDNormalize():
    logging.info("Start _PreProcess_RuleIDNormalize")
    for rulegroup in RuleGroupDict.values():
        for rule in rulegroup.RuleList:
            for token in rule.Tokens:
                if token.SubtreePointer:
                    continue
                for rg2 in RuleGroupDict.values():
                    for r2 in rg2.RuleList:
                        if id(r2) <= id(rule):
                            continue
                        for t2 in r2.Tokens:
                            if token.SubtreePointer is None and t2 == token:
                                t2.ID = token.ID
    logging.info("Done with _PreProcess_RuleIDNormalize")


def _CheckFeature_returnword(word, fuzzy):
    try:
        if len(word) >= 2 and word[0] == "[" and SearchPair(word[1:], "[]") == len(word) - 2:
            word = word[1:-1].strip()
        _, matchtype = LogicOperation_CheckPrefix(word)
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
            word = "'|'".join(items)
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
                if fuzzy:
                    word = ".{}.".format(word)
                    # logging.error("Because of the fuzzy status in DAGFSA_APP, the word is:{}".format(word))
                else:
                    word = "'{}'".format(word)  #use stem for non quoted word.
                    #logging.error("\tNormal fuzzy status. the word is {}".format(word))
        elif "|" in word and " " not in word and "[" not in word and "(" not in word:
            # be aware of ['and|or|of|that|which'|PP|CM]
            try:
                OrBlocks = LogicOperation_SeparateOrBlocks(word)
            except RuntimeError as e:
                logging.error("Error for rule:" + word)
                logging.error(str(e))
                return  # not to process the rest.

            newword = ""
            for OrBlock in OrBlocks:
                _, mtype = LogicOperation_CheckPrefix(OrBlock)
                if mtype == "unknown" and OrBlock[0] != "!" and FeatureOntology.GetFeatureID(OrBlock) == -1:
                    # logging.warning("Will treat this as a stem:" + OrBlock)
                    newword += "'" + OrBlock + "'|"
                else:
                    newword += OrBlock + "|"
            word = newword.rstrip("|")
        elif " " in word and "[" not in word and "(" not in word:
            # be aware of ['and|or|of|that|which'|PP|CM]
            AndBlocks = word.split()
            newword = ""
            for AndBlock in AndBlocks:
                if AndBlock.startswith("%F"):  # for unification extention, leave it to next step (ExpandOrBlock)
                    newword += AndBlock + " "
                else:
                    newword += _CheckFeature_returnword(AndBlock, fuzzy) + " "
            word = newword.rstrip(" ")
    return prefix + word


def OutputRules(rulegroup, style="details"):
    output = "// ****Rules**** " + rulegroup.FileName + "\n"
    output += "// * size: " + str(len(rulegroup.RuleList)) + " *\n"
    # for rule in sorted(rulegroup.RuleList, key=lambda x: (GetPrefix(x.RuleName), x.RuleContent)):
    for rule in rulegroup.RuleList :
        output += rule.output(style) + "\n"

    output += "// ****Macros****\n"
    output += "// * size: " + str(len(rulegroup.MacroDict)) + " *\n"
    for rule in rulegroup.MacroDict.values():
        output += rule.output(style) + "\n"

    output += "// End of Rules/Expert Lexicons/Macros\n"
    return output


def OutputRuleFiles(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), FolderLocation)

    for RuleFile in RuleGroupDict:
        rg = RuleGroupDict[RuleFile]
        output = OutputRules(rg, "concise")
        FileLocation = os.path.join(FolderLocation, rg.FileName)
        DirectoryLocation = os.path.dirname(FileLocation)
        if not os.path.exists(DirectoryLocation):
            os.makedirs(DirectoryLocation)

        with open(FileLocation, "w", encoding="utf-8") as writer:
            writer.write(output)

        utoutput = ""
        for unittestnode in rg.UnitTest:
            utoutput += unittestnode.RuleName + "\t// " + unittestnode.TestSentence + "\n"
        utFileLocation = os.path.join(FolderLocation, rg.FileName + ".unittest")
        with open(utFileLocation, "w", encoding="utf-8") as writer:
            writer.write(utoutput)

    # OutputRuleDB()


def _OutputRuleDB(rulegroup):
    #return  # disable, to avoid locking.
    cur = utils.DBCon.cursor()
    startdatetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    strsql = "SELECT ID from rulefiles where filelocation=?  limit 1"
    cur.execute(strsql, [rulegroup.FileName, ])
    resultrecord = cur.fetchone()
    if resultrecord:
        rulefileid = resultrecord[0]
        strsql = "update rulefiles set verifytime=DATETIME('now') where ID=?"
        cur.execute(strsql, [rulefileid, ])
    else:
        strsql = "INSERT into rulefiles (filelocation, createtime, verifytime) VALUES(?, DATETIME('now'), DATETIME('now'))"
        cur.execute(strsql, [rulegroup.FileName, ])
        rulefileid = cur.lastrowid

    for rule in rulegroup.RuleList:
        rule.DBSave(rulefileid)
        # if there is same body of rule in db (for the same rulefileid), then use the same rule id, remove the existing rulenodes and rulechunks for it. create new ones;
        #    update the verifytime, and status.
        # if there is no same body, create everything.
        # Aftter one iteration, find the rule that the verifytime is old, change status to disable them.

    strsql = "UPDATE ruleinfo set status=-1 where rulefileid=? and verifytime<?"
    cur.execute(strsql, [rulefileid, startdatetime])
    cur.close()
    utils.DBCon.commit()


"""
sqlite3 parser.db
### ruleinfo.body is the body part of each token. for unique comparison.

CREATE TABLE systemfiles    (ID INTEGER PRIMARY KEY AUTOINCREMENT, filelocation TEXT, modifytime DATETIME);
CREATE TABLE rulefiles    (ID INTEGER PRIMARY KEY AUTOINCREMENT, filelocation TEXT, createtime DATETIME, verifytime DATETIME);
CREATE TABLE ruleinfo     (ID INTEGER PRIMARY KEY AUTOINCREMENT, rulefileid INT, name, strtokenlength INT, tokenlength INT, body TEXT, status INT, norms TEXT, origin TEXT, comment TEXT, createtime DATETIME, verifytime DATETIME, CONSTRAINT unique_body UNIQUE(rulefileid, body) );
CREATE TABLE rulechunks   (ID INTEGER PRIMARY KEY AUTOINCREMENT, ruleid INT , chunklevel INT, startoffset INT, length INT, stringchunklength INT, headoffset INT, action TEXT  );
CREATE TABLE rulenodes    (ID INTEGER PRIMARY KEY AUTOINCREMENT, ruleid INT, sequence INT, matchbody TEXT, action TEXT , pointer TEXT, subtreepointer TEXT, andtext TEXT, andtextmatchtype TEXT, nottext TEXT, nottextmatchtype TEXT, CONSTRAINT unique_position UNIQUE(ruleid, sequence));
CREATE TABLE rulehits     (sentenceid INT, ruleid INT, createtime DATETIME, verifytime DATETIME, CONSTRAINT unique_hit UNIQUE(sentenceid, ruleid));
CREATE TABLE rulenode_texts (rulenodeid INT, `text` TEXT, type INT, CONSTRAINT unique_type UNIQUE(rulenodeid, `text`));
CREATE TABLE sentences (ID INTEGER PRIMARY KEY AUTOINCREMENT, sentence TEXT, result BLOB, createtime DATETIME, verifytime DATETIME, CONSTRAINT unique_sentence UNIQUE(sentence) );
CREATE TABLE rulenode_orfeatures (rulenodeid INT, featureid INT, groupid INT, CONSTRAINT unique_type UNIQUE(rulenodeid, featureid));
CREATE TABLE rulenode_features (rulenodeid INT, featureid INT, type INT, CONSTRAINT unique_type UNIQUE(rulenodeid,type,featureid));

"""
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    LoadGlobalMacro('../../fsa/Y/GlobalMacro.txt')
    # LoadRules("../../fsa/Y/900NPy.xml")
    # LoadRules("../../fsa/Y/800VGy.txt")
    # # LoadRules("../../fsa/Y/1800VPy.xml")
    # # LoadRules("../../fsa/Y/100y.txt")
    # # LoadRules("../../fsa/Y/50POSy.xml")
    # # #
    # LoadRules("../../fsa/X/mainX2.txt")
    # LoadRules("../../fsa/X/ruleLexiconX.txt")
    # # #
    # LoadRules("../../fsa/X/0defLexX.txt")
    if utils.DBCon is None:
        utils.InitDB()
    LoadRules('../../fsa/X/', '0test.txt', False)

    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_3_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_4_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_5_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_6_list.txt")
    # LoadRules("../../fsa/X/Q/rule/CleanRule_gram_7_list.txt")

    # LoadRules("../../fsa/X/10compound.txt")

    # LoadRules("../../fsa/X/180NPx.txt")

    # ExpandRuleWildCard()
    # ExpandParenthesisAndOrBlock()
    # ExpandRuleWildCard()
    # PreProcess_CheckFeatures()
    # PreProcess_CompileHash()
    # SortByLength()

    # print (OutputRules("concise"))
    OutputRuleFiles("../compiled/")
    # print(FeatureOntology.OutputMissingFeatureSet())
