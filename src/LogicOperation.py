
import FeatureOntology
from utils import *

#not, and, or
#compare type: word/norm/stem/feature


#   Sometimes it is like:  'a|b|c'
#   sometimes it is like:  a|'b'|c
# so CheckPrefix() is being called from both LogicMatch() and LogicMatchFeatures()
from functools import lru_cache
# return -1 if failed. Should throw error?
#@lru_cache(100000)
def CheckPrefix(word, matchtype):
    if len(word) < 2:
        return word, matchtype

    if word[0] == "[" and SearchPair(word[1:], "[]") == len(word) - 2:
        word = word[1:-1]   #remove redundant []
        if word == "":
            return "", matchtype

    prefix = ""


    if word[0] == "!":
        prefix = "!"
        word = word.lstrip("!")
    if word[0] == "\"" and SearchPair(word[1:], "\"\"") == len(word)-2 :  # word  comparison
        word = word.strip("\"")
        matchtype = "word"      # case insensitive
    elif word[0] == "'" and SearchPair(word[1:], "''") == len(word)-2 :
        word = word.strip("'")
        matchtype = "stem"      # case insensitive
    elif word[0] == "/" and SearchPair(word[1:], "//") == len(word)-2 :
        word = word.strip("/")
        matchtype = "norm"      # case insensitive

    return prefix+word, matchtype

#In rule, start from RulePosition, seach for pointer:
#   Start from left side, if not found, seach right side.
# After that is found, use the offset to locate the token in StrTokens
#  compare the pointertoken to the current token (both in StrTokens),
#   return the compare result.
def PointerMatch(StrTokens, StrPosition, RuleTokens, RulePosition, Pointer, matchtype='stem'):
    RulePointerPos = RulePosition
    while RulePointerPos >= 0:
        if hasattr(RuleTokens[RulePointerPos], 'pointer'):
            if RuleTokens[RulePointerPos].pointer == Pointer:
                break   #found pointer!
        RulePointerPos -= 1

    if RulePointerPos < 0:
        RulePointerPos = RulePosition
        while RulePointerPos < len(RuleTokens):
            if hasattr(RuleTokens[RulePointerPos], 'pointer'):
                if RuleTokens[RulePointerPos].pointer == Pointer:
                    break  # found pointer!
            RulePointerPos += 1
        if RulePointerPos >= len(RuleTokens):
            logging.error("PointerMatch Can't find specified pointer " + Pointer + " in rule:")
            logging.error(RuleTokens[0].word)
            raise RuntimeError("Can't find specified pointer in rule!")
    # Now we have the pointer location in Rule
    GoneInStrTokens = 0
    Offset = RulePointerPos - RulePosition  #might be positive, or negative

    if Offset < 0:
        for i in range(-Offset):
            while StrTokens[StrPosition - i - GoneInStrTokens].Gone:
                GoneInStrTokens += 1
                if StrPosition - i - GoneInStrTokens < 0:
                    #Logically wrong. There must be a token matched the RulePointerToken
                    # since the RulePointerToken is on the left side.
                    raise EOFError("Reached the start of the String!")
        StrPointerPos = StrPosition+Offset-GoneInStrTokens
    elif Offset>0:
        for i in range(Offset):
            while StrTokens[StrPosition+GoneInStrTokens].Gone:
                GoneInStrTokens += 1
                if StrPosition+GoneInStrTokens > len(StrTokens):
                    return False    #this rule does not fit this sentence.
                    #raise EOFError("Reached the end of the String!")
        StrPointerPos = StrPosition+Offset+GoneInStrTokens
    else:
        logging.error("Rule token:" + str(RuleTokens[RulePosition]))
        raise RuntimeError("Logically the pointer should not be itself. Please check syntax!")

    if matchtype == "stem":
        return StrTokens[StrPointerPos].stem == StrTokens[StrPosition].stem
    elif matchtype == "word":
        return StrTokens[StrPointerPos].word == StrTokens[StrPosition].word
    elif matchtype == "norm":
        return StrTokens[StrPointerPos].norm == StrTokens[StrPosition].norm
    else:
        logging.error("Rule token:" + str(RuleTokens[RulePosition]))
        raise RuntimeError("The matchtype should be stem/word/norm. Please check syntax!")


def LogicMatch(StrTokens, StrPosition, rule, RuleTokens, RulePosition, matchtype="unknown"):
    if not rule:  # "[]", not sure what that is.
        return False

    strToken = StrTokens[StrPosition]
    rule, matchtype = CheckPrefix(rule, matchtype)
    if matchtype == "unknown":
        return LogicMatchFeatures(StrTokens, StrPosition, rule, RuleTokens, RulePosition)

    if not re.search('[| !]', rule):
        if rule.startswith("^"):

            #This is a pointer!
            return PointerMatch(StrTokens, StrPosition, RuleTokens, RulePosition, Pointer=rule, matchtype=matchtype)
            #pass
            #strToken = SearchPointer(StrTokens, StrPosition, Pointer=rule)
        if matchtype == "stem":
            word = strToken.stem
        elif matchtype == "norm":
            word = strToken.norm
        else:
            word = strToken.word

        if rule.lower() == word.lower() \
                or rule.endswith('-') and word.startswith(rule[:-1])\
                or rule.startswith('-') and word.endswith(rule[1:]):
            return True
        else:
            return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatch(StrTokens, StrPosition, AndBlock, RuleTokens, RulePosition, matchtype)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatch(StrTokens, StrPosition, rule[1:], RuleTokens, RulePosition, matchtype)
        else:
            Result = False
            OrBlocks = SeparateOrBlocks(rule)
            if len(OrBlocks) >= 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(StrTokens, StrPosition, OrBlock, RuleTokens, RulePosition, matchtype)
            else:
                raise RuntimeError("Why OrBlock is none?")

    return Result


# If the rule has not quotes, but it is not a feature,
#   then it is treated as stem.
def LogicMatchFeatures(strTokens, StrPosition, rule, RuleTokens, RulePosition):
    if not rule:
        return True # for the comparison of "[]", can match anything

    strToken = strTokens[StrPosition]
    rule, matchtype = CheckPrefix(rule, 'feature')
    if matchtype != "feature":
        return LogicMatch(strTokens, StrPosition, rule, RuleTokens, RulePosition, matchtype)

    if not re.search('[| !]', rule):
        if -1 in strToken.features:
            strToken.features.remove(-1)
        featureID = FeatureOntology.GetFeatureID(rule)
        if featureID == -1:
            return LogicMatch(strTokens, StrPosition, rule, RuleTokens, RulePosition, "stem")
        else:
            if featureID and featureID in strToken.features:
                return True
            else:
                return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatchFeatures(strTokens, StrPosition, AndBlock, RuleTokens, RulePosition)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatchFeatures(strTokens, StrPosition, rule[1:], RuleTokens, RulePosition)
        else:
            Result = False
            OrBlocks = SeparateOrBlocks(rule)
            if len(OrBlocks) >= 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(strTokens, StrPosition, OrBlock, RuleTokens, RulePosition)
            else:
                raise RuntimeError("Why OrBlock is none?")
    return Result

#@lru_cache(100000)
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
