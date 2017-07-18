# coding: utf-8
from __future__ import unicode_literals
import logging, re
#import Tokenization, FeatureOntology

_RuleList = []

def SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0].strip(), " ".join(blocks[1:])


class Rule:
    def __init__(self):
        self.RuleName = ''
        self.Origin = ''
        self.RuleContent = ''
        self.Tokens = []
        self.MatchString = ''
        self.Actions = {}

    def __str__(self):
        return self.Tokens.__str__()

    def SetRule(self, ruleString):
        self.Origin = ruleString
        code, __ = SeparateComment(ruleString)
        blocks = [x.strip() for x in re.split("=", code)]
        if len(blocks) <> 2:
            logging.info(" not separated by =")
            return
        self.RuleName = blocks[0]
        self.RuleContent = blocks[1]
        self.Tokens = Tokenize(self.RuleContent)


# Note: this tokenization is for tokenizing rule,
#       which is different from tokenizing the normal language.
# ignore {, < > }
# For " [ (  find the couple sign ) ] " as token. Otherwise,
SignsToIgnore = "{<>}"
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
                TokenList.append(RuleContent[StartPosition:EndOfToken])
                i = EndOfToken
                if i == len(RuleContent):
                    break
        else:
            if not StartToken:
                StartToken = True
                StartPosition = i

        for pair in Pairs:
            if RuleContent[i] == pair[0]:
                StartPosition = i
                end = SearchPair(RuleContent[StartPosition+1:], pair)
                if end > 0:
                    StartToken = False
                    EndOfToken = StartPosition+1+end + SearchToEnd(RuleContent[StartPosition+1+end:])
                    TokenList.append(RuleContent[StartPosition:EndOfToken])
                    i = EndOfToken
                    break
        i += 1
    return TokenList

# return -1 if failed. Should throw error?
def SearchPair(string, tagpair):
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

def SearchToEnd(string):
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


def LoadRules(RuleLocation):
    global _RuleList
    with open(RuleLocation) as dictionary:
        for line in dictionary:
            node = Rule()
            node.SetRule(line)
            if node.RuleName:
                _RuleList.append(node)




#LoadRules("../data/rule.txt")

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    target = """PassiveSimpleING = {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};"""
    rule = Rule()
    rule.SetRule(target)
    print rule.RuleContent
    print rule.Tokens

    target = """
V_NN1_de_NN2_exception4 =
{
   	[s xiangW|和|同|与|跟]
   		[DE quantifier]?
   	[s N|PRP|PRPP]
   	[yiyangW !negationM:Reset]
   	[的|滴]
   	[N]
};
"""
    rule = Rule()
    rule.SetRule(target)
    print rule.RuleContent
    print rule.Tokens

