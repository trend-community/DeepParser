
import FeatureOntology
from utils import *

#not, and, or
#compare type: word/norm/stem/feature


#   Sometimes it is like:  'a|b|c'
#   sometimes it is like:  a|'b'|c
# so CheckPrefix() is being called from both LogicMatch() and LogicMatchFeatures()
def CheckPrefix(word, matchtype):
    if len(word) < 2:
        return word, matchtype

    if word[0] == "[" and SearchPair(word[1:], "[]") == len(word) - 2:
        word = word[1:-1]   #remove redundant []

    prefix = ""

    if word.startswith("!"):
        prefix = "!"
        word = word.lstrip("!")
    if word.startswith("\"") and SearchPair(word[1:], "\"\"") == len(word)-2 :  # word  comparison
        word = word.strip("\"")
        matchtype = "word"      # case insensitive
    elif word.startswith("'") and SearchPair(word[1:], "''") == len(word)-2 :
        word = word.strip("'")
        matchtype = "stem"      # case insensitive
    elif word.startswith("/") and SearchPair(word[1:], "//") == len(word)-2 :
        word = word.strip("/")
        matchtype = "norm"      # case insensitive

    return prefix+word, matchtype


def LogicMatch(rule, strToken, matchtype="unknown"):
    if not rule:  # "[]", not sure what that is.
        return False

    rule, matchtype = CheckPrefix(rule, matchtype)
    if matchtype == "unknown":
        return LogicMatchFeatures(rule, strToken)

    if not re.search('[| !]', rule):
        if matchtype == "stem" and strToken.lexicon:
            word = strToken.stem
        elif matchtype == "norm" and strToken.lexicon:
            word = strToken.norm
        else:
            word = strToken.word
        if rule.lower() == word.lower():
            return True
        else:
            return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatch(AndBlock, strToken, matchtype)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatch(rule[1:], strToken, matchtype)
        else:
            Result = False
            OrBlocks = SeparateOrBlocks(rule)
            if len(OrBlocks) >= 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(OrBlock, strToken, matchtype)
            else:
                raise RuntimeError("Why OrBlock is none?")

    return Result


# If the rule has not quotes, but it is not a feature,
#   then it is treated as stem.
def LogicMatchFeatures(rule, strToken):
    if not rule:
        return True # for the comparison of "[]", can match anything

    rule, matchtype = CheckPrefix(rule, 'feature')
    if matchtype != "feature":
        return LogicMatch(rule, strToken, matchtype)

    if not re.search('[| !]', rule):
        if -1 in strToken.features:
            strToken.features.remove(-1)
        featureID = FeatureOntology.GetFeatureID(rule)
        if featureID == -1:
            return LogicMatch(rule, strToken, "stem")
        else:
            if featureID and featureID in strToken.features:
                return True
            else:
                return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatchFeatures(AndBlock, strToken)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatchFeatures(rule[1:], strToken)
        else:
            Result = False
            OrBlocks = SeparateOrBlocks(rule)
            if len(OrBlocks) >= 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(OrBlock, strToken)
            else:
                raise RuntimeError("Why OrBlock is none?")
    return Result

def SeparateOrBlocks(OrString):
    if "|" not in OrString:
        return OrString
    OrBlocks = []

    i = 0
    StartToken = False
    #Pairs = ['[]', '()', '""', '\'\'', '//']
    # Pairs is defined in utils.py
    while i < len(OrString):
        if OrString[i] == "|":
            if StartToken:
                StartToken = False
                EndOfToken = i
                OrBlocks.append(OrString[StartPosition:EndOfToken])
                if i == len(OrString):
                    break
        else:
            if not StartToken:
                StartToken = True
                StartPosition = i

        for pair in Pairs:
            if OrString[i] == pair[0] and (i==0 or OrString[i-1] != "\\"): #escape

                end = SearchPair(OrString[i+1:], pair)
                if end >= 0:
                    StartToken = False
                    EndOfToken = i+2+end

                    OrBlocks.append(OrString[StartPosition:EndOfToken])
                    i = EndOfToken
                    break

        i += 1

    if StartToken:       #wrap up the last one
        EndOfToken = i
        OrBlocks.append(OrString[StartPosition:EndOfToken])

    return OrBlocks
