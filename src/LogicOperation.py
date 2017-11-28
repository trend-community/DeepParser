import jsonpickle
import FeatureOntology
from utils import *
import utils
#not, and, or
#compare type: word/norm/stem/feature


#   Sometimes it is like:  'a|b|c'
#   sometimes it is like:  a|'b'|c
# so CheckPrefix() is being called from both LogicMatch() and LogicMatchFeatures()
from functools import lru_cache
# return -1 if failed. Should throw error?
@lru_cache(100000)
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
        matchtype = "text"      # case insensitive
    elif word[0] == "'" and SearchPair(word[1:], "''") == len(word)-2 :
        word = word.strip("'")
        matchtype = "norm"      # case insensitive
    elif word[0] == "/" and SearchPair(word[1:], "//") == len(word)-2 :
        word = word.strip("/")
        matchtype = "atom"      # case insensitive

    return prefix+word, matchtype


def GetNumberPointer(Pointer):
    PointerContent = Pointer[1:]
    if len(PointerContent) == 0:
        Pos = 0
    else:
        try:
            Pos = int(PointerContent)
        except ValueError:
            Pos = -1
    return Pos


#In rule, start from RulePosition, seach for pointer:
#   Start from left side, if not found, seach right side.
# After that is found, use the offset to locate the token in StrTokens
#  compare the pointertoken to the current token (both in StrTokens),
#   return the compare result.
def PointerMatch(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer, matchtype='norm'):
    if Pointer.startswith('^-'):
        PointerIsSuffix = True
        Pointer = '^' + Pointer[2:]
    else:
        PointerIsSuffix = False
    if Pointer.endswith('-'):
        PointerIsPrefix = True
        Pointer = Pointer[:-1]
    else:
        PointerIsPrefix = False

    RulePointerPos = GetNumberPointer(Pointer)
    if RulePointerPos < 0:

        RulePointerPos = RulePosition

        #logging.debug("Testing pointer" + Pointer)
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
                logging.error(jsonpickle.dumps(RuleTokens[0]))
                raise RuntimeError("Can't find specified pointer in rule!")
    # Now we have the pointer location in Rule
    Offset = RulePointerPos - RulePosition  #might be positive, or negative

    StrPointerPos = StrPosition+Offset
    StrPointerToken = StrTokenList.get(StrPointerPos)
    strToken = StrTokenList.get(StrPosition)

    if matchtype == "text":
        return StrPointerToken.text == strToken.text \
                or (PointerIsPrefix and StrPointerToken.text.startswith(strToken.text)) \
               or (PointerIsSuffix and StrPointerToken.text.endswith(strToken.text)  )
    elif matchtype == "norm":
        return StrPointerToken.norm == StrTokenList.get(StrPosition).norm \
                or (PointerIsPrefix and StrPointerToken.norm.startswith(strToken.norm)) \
               or (PointerIsSuffix and StrPointerToken.norm.endswith(strToken.norm)  )
    elif matchtype == "atom":
        return StrPointerToken.atom == StrTokenList.get(StrPosition).atom \
                or (PointerIsPrefix and StrPointerToken.atom.startswith(strToken.atom)) \
               or (PointerIsSuffix and StrPointerToken.atom.endswith(strToken.atom)  )
    else:
        logging.error("Rule token:" + str(RuleTokens[RulePosition]))
        raise RuntimeError("The matchtype should be text/norm/atom. Please check syntax!")

CombinedPattern = re.compile('[| !]')
def LogicMatch(StrTokenList, StrPosition, rule, RuleTokens, RulePosition, matchtype="unknown", strToken=None):
    if not rule:  # for the comparison of "[]", can match anything
        return True

    if not strToken:
        strToken = StrTokenList.get(StrPosition)

    LogicMatchKey = [strToken, rule]
    rule, matchtype = CheckPrefix(rule, matchtype)
    if matchtype == "unknown":
        return LogicMatchFeatures(StrTokenList, StrPosition, rule, RuleTokens, RulePosition, strToken=strToken)

    if not CombinedPattern.search( rule):
        if rule.startswith("^"):
            #This is a pointer!
            return PointerMatch(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer=rule, matchtype=matchtype)

        if utils.FeatureID_0 not in strToken.features:
            if RuleTokens[RulePosition].word.startswith("0") or RuleTokens[RulePosition].word.startswith("[0"):
                logging.error("Checking feature 0 should be the first task in current rule. should not get to here")
                logging.error(jsonpickle.dumps(RuleTokens[0]))
                raise RuntimeError("Logic Error for checking feature 0")
            else:
                if strToken.Head0Text:
                    word = strToken.Head0Text
                else:
                    word = strToken.text
                #logging.debug("Rule Not 0:" + rule + " of " + RuleTokens[RulePosition].word + " for: " + word)

        else:
#            if RuleTokens[RulePosition].word.startswith("0") or RuleTokens[RulePosition].word.startswith("[0"):
#                logging.debug("Rule 0:" + rule + " of " + RuleTokens[RulePosition].word)
            if matchtype == "text":
                word = strToken.text
            elif matchtype == "norm":
                word = strToken.norm
            else:
                word = strToken.atom

        if rule.lower() == word.lower() \
                or rule.endswith('-') and word.startswith(rule[:-1])\
                or rule.startswith('-') and word.endswith(rule[1:]):
            if word == strToken.Head0Text:
                logging.error("Not an error! word == strToken.Head0Text!" + RuleTokens[RulePosition].word)
                logging.error(str(RuleTokens))
                logging.error(str(StrTokenList))
            return True
        else:
            return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatch(StrTokenList, StrPosition, AndBlock, RuleTokens, RulePosition, matchtype, strToken=strToken)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatch(StrTokenList, StrPosition, rule[1:], RuleTokens, RulePosition, matchtype, strToken=strToken)
        else:
            Result = False
            OrBlocks = SeparateOrBlocks(rule)
            if len(OrBlocks) >= 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(StrTokenList, StrPosition, OrBlock, RuleTokens, RulePosition, matchtype, strToken=strToken)
            else:
                raise RuntimeError("Why OrBlock is none?")

    return Result


# If the rule has not quotes, but it is not a feature,
#   then it is treated as stem.
def LogicMatchFeatures(StrTokenList, StrPosition, rule, RuleTokens, RulePosition, strToken=None):
    if not rule:
        return True # for the comparison of "[]", can match anything

    if not strToken:
        strToken = StrTokenList.get(StrPosition)
    rule, matchtype = CheckPrefix(rule, 'feature')
    if matchtype != "feature":
        return LogicMatch(StrTokenList, StrPosition, rule, RuleTokens, RulePosition, matchtype, strToken=strToken)

    if not re.search('[| !]', rule):
        if -1 in strToken.features:
            strToken.features.remove(-1)
        featureID = FeatureOntology.GetFeatureID(rule)
        if featureID == -1:
            return LogicMatch(StrTokenList, StrPosition, rule, RuleTokens, RulePosition, "norm", strToken=strToken)
        else:
            if featureID and featureID in strToken.features:
                return True
            else:
                return False

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatchFeatures(StrTokenList, StrPosition, AndBlock, RuleTokens, RulePosition, strToken=strToken)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatchFeatures(StrTokenList, StrPosition, rule[1:], RuleTokens, RulePosition, strToken=strToken)
        else:
            Result = False
            OrBlocks = SeparateOrBlocks(rule)
            if len(OrBlocks) >= 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(StrTokenList, StrPosition, OrBlock, RuleTokens, RulePosition, strToken=strToken)
            else:
                raise RuntimeError("Why OrBlock is none?")
    return Result

@lru_cache(100000)
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
