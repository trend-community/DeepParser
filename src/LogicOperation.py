import logging, re
import FeatureOntology

#not, and, or
#type: word/norm/stem
def LogicMatch(rule, strtoken, matchtype="word"):
    if not re.search('\|| |!', rule):
        if matchtype == "stem" and strtoken.lexicon:
            word = strtoken.lexicon.stem
        elif matchtype == "norm" and strtoken.lexicon:
            word = strtoken.lexicon.norm
        else:
            word = strtoken.word
        if rule == word:
            return True
        else:
            return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatch(AndBlock, strtoken, matchtype)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatch(rule[1:], strtoken, matchtype)
        else:
            Result = False
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(OrBlock, strtoken, matchtype)

    return Result


def LogicMatchFeatures(rule, strtoken):

    if not rule:
        return False

    if not re.search('\|| |!', rule):
        if -1 in strtoken.lexicon.features:
            strtoken.lexicon.features.remove(-1)
        featureID = FeatureOntology.GetFeatureID(rule)
        if featureID == -1:
            return LogicMatch(rule, strtoken)
        else:
            if featureID and featureID in strtoken.lexicon.features:
                return True
            else:
                return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatchFeatures(AndBlock, strtoken)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatchFeatures(rule[1:], strtoken)
        else:
            Result = False
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(OrBlock, strtoken)

    return Result
