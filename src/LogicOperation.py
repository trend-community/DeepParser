import logging, re
import FeatureOntology

#not, and, or
def LogicMatch(rule, word):
    if rule == word:
        return True

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatch(AndBlock, word)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatch(rule[1:], word)
        else:
            Result = False
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(OrBlock, word)

    return Result


def LogicMatchFeatures(rule, featurelist):
    if not rule:
        return False
    featureID = FeatureOntology.GetFeatureID(rule)
    if featureID and featureID in featurelist:
        return True

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatchFeatures(AndBlock, featurelist)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatchFeatures(rule[1:], featurelist)
        else:
            Result = False
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(OrBlock, featurelist)

    return Result
