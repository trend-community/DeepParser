import logging, re
import FeatureOntology

#not, and, or
#type: word/norm/stem

def CheckPrefix(word, matchtype):
    if word.startswith("\""):  # word  comparison
        word = word.strip("\"")
        matchtype = "word"      # case insensitive
    elif word.startswith("'"):
        word = word.strip("\'")
        matchtype = "stem"      # case insensitive
    elif word.startswith("/"):
        word = word.strip("/")
        matchtype = "norm"      # case insensitive
    return word, matchtype

def LogicMatch(rule, strToken, matchtype="unknown"):

    if not rule:  # "[]", not sure what that is.
        return False

    rule, matchtype = CheckPrefix(rule, matchtype)
    if matchtype == "unknown":
        return LogicMatchFeatures(rule, strToken)

    if not re.search('\|| |!', rule):
        if matchtype == "stem" and strToken.lexicon:
            word = strToken.lexicon.stem
        elif matchtype == "norm" and strToken.lexicon:
            word = strToken.lexicon.norm
        else:
            word = strToken.word
        if rule.lower() == word:
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
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(OrBlock, strToken, matchtype)

    return Result


def LogicMatchFeatures(rule, strToken):

    if not rule:
        return True # for the comparison of "[]", can match anything

    rule, matchtype = CheckPrefix(rule, 'feature')
    if matchtype != "feature":
        return LogicMatch(rule, strToken, matchtype)

    if not re.search('\|| |!', rule):
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
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(OrBlock, strToken)

    return Result
