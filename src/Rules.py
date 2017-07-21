
import logging, re
import Tokenization
import unittest
#import FeatureOntology

_RuleList = []

def SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0].strip(), " ".join(blocks[1:])


class Rule:
    def __init__(self):
        self.ID = 0
        self.RuleName = ''
        self.Origin = ''
        self.RuleContent = ''
        self.Tokens = []
        self.MatchString = ''
        self.Actions = {}

    def __str__(self):
        return self.Tokens.__str__()

    def SetRule(self, ruleString, ID=1):
        self.Origin = ruleString
        code, __ = SeparateComment(ruleString)
        blocks = [x.strip() for x in re.split("=", code)]
        if len(blocks) != 2:
            logging.info(" not separated by =")
            return
        self.ID = ID
        self.RuleName = blocks[0]
        self.RuleContent = blocks[1]
        self.Tokens = Tokenize(self.RuleContent)
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

    def __str__(self):
        output = "[ID]=" + str(self.ID)
        output += "\t[Name]=" + self.RuleName
        output += "\t[Origin Content]=\n" + self.RuleContent
        output += "\n\t[Compiled Content]=\n{"
        for token in self.Tokens:
            if token.StartTrunk:
                output += "<"
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
# For " [ (  find the couple sign ) ] " as token. Otherwise,
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
                if end > 0:
                    StartToken = False
                    EndOfToken = i+1+end + _SearchToEnd(RuleContent[StartPosition+1+end:])
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
    raise Exception(" Can't find a pair tag!" + string)
    return -1

def _SearchToEnd(string):
    if not string:      # if it is empty
        return 0
    i = 1
    while i<len(string):
        if string[i] in SignsToIgnore:
            break
        if string[i].isspace():
            break
        for pair in Pairs:
            if string[i] == pair[0]:
                return i
        i += 1
    return i


# a rule is not necessary in one line.
def LoadRules(RuleLocation):
    global _RuleList
    with open(RuleLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = Rule()
            node.SetRule(line)
            if node.RuleName:
                _RuleList.append(node)




LoadRules("../data/rule.txt")

class RuleTest(unittest.TestCase):
    def test_Tokenization(self):
        tokenlist = Tokenize("[a] [b]")
        self.assertEqual(tokenlist[0].word, '[a]')
    def test_SetRule_number(self):
        r = Rule()
        r.SetRule("a=[a]4 [b]* [c]*7 [d]?")
        self.assertEqual(r.Tokens[0].repeat[1], 4)
        self.assertEqual(r.Tokens[1].repeat[1], 3)
        self.assertEqual(r.Tokens[2].repeat[1], 7)
        self.assertEqual(r.Tokens[3].repeat[1], 1)
        self.assertEqual(r.Tokens[3].repeat[0], 0)
    def test_tokenspace(self):
        r = Rule()
        r.SetRule("b=[a b? c:d e]")
        self.assertEqual(r.Tokens[0].word, '[a b? c]')
        self.assertEqual(r.Tokens[0].action, 'd e')



if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    unittest.main()
    target = """PassiveSimpleING = {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};"""
    rule = Rule()
    rule.SetRule(target)
    print(rule)

    target = """
than_VP2(Top) = ^[/than|as/:Sconj] [VG:^.Kid]
"""
    rule = Rule()
    rule.SetRule(target)
    print(rule)
    #
    # for rule in _RuleList:
    #     print(rule)
    #