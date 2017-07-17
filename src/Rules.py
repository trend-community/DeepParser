import logging, re
import Tokenization, FeatureOntology

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
        self.Tokens = Tokenization.Tokenize(self.RuleContent)



def LoadRules(RuleLocation):
    global _RuleList
    with open(RuleLocation) as dictionary:
        for line in dictionary:
            node = Rule()
            node.SetRule(line)
            if node.RuleName:
                _RuleList.append(node)




LoadRules("../data/rule.txt")

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    target = """PassiveSimpleING = {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};"""
    rule = Rule()
    rule.SetRule(target)
    print rule.__dict__

