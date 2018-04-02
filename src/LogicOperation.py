
from utils import *

#not, and, or
#compare type: word/norm/stem/feature


#   Sometimes it is like:  'a|b|c'
#   sometimes it is like:  a|'b'|c
# so CheckPrefix() is being called from LogicMatch()
from functools import lru_cache
# return -1 if failed. Should throw error?
@lru_cache(200000)
def CheckPrefix(word):
    matchtype = "unknown"
    if len(word) < 2:
        return word, matchtype

    if word[0] == "[" and SearchPair(word[1:], "[]") == len(word) - 2:
        word = word[1:-1]   #remove redundant []
        if word == "":
            return "", matchtype

    prefix = ""
    if word[0] == "!":
        prefix = "!"
        word = word[1:]

    lastlocation = len(word) -1
    if word[0] == "\"" and word.find("\"", 1) == lastlocation :  # word  comparison
        word = word.strip("\"")
        matchtype = "text"      # case insensitive
    elif word[0] == "'" and word.find("'", 1) == lastlocation :
        word = word.strip("'")
        matchtype = "norm"      # case insensitive
    elif word[0] == "/" and word.find("/", 1) == lastlocation :
        word = word.strip("/")
        matchtype = "atom"      # case insensitive

    return prefix+word, matchtype


#Usage:  [] <[A] [B] [^2.S=x]>  //usage ^2 to point to the 2nd token of the rule.
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


def LocateStrTokenOfPointer(StrTokenList, StrPosition,RuleTokens, RulePosition, Pointer):
    x = StrTokenList.head
    StrPointerToken = ''
    while x:
        if x.TempPointer == Pointer:
            StrPointerToken = x
            break       # the TempPointer is already set (the reference is on right side of the rule)
        x = x.next

    if not StrPointerToken:

        RulePointerPos = GetNumberPointer(Pointer)
        if RulePointerPos <= 0:
            RulePointerPos = RulePosition
            #logging.debug("Testing pointer" + Pointer)
            while RulePointerPos >= 0:
                if RuleTokens[RulePointerPos].pointer:
                    if RuleTokens[RulePointerPos].pointer == Pointer:
                        break   #found pointer!
                RulePointerPos -= 1

            if RulePointerPos < 0:
                RulePointerPos = RulePosition
                while RulePointerPos < len(RuleTokens):
                    if RuleTokens[RulePointerPos].pointer:
                        if RuleTokens[RulePointerPos].pointer == Pointer:
                            break  # found pointer!
                    RulePointerPos += 1
                if RulePointerPos >= len(RuleTokens):
                    logging.error("LocateStrTokenOfPointer Can't find specified pointer " + Pointer + " in rule:")
                    logging.error(jsonpickle.dumps(RuleTokens))
                    raise RuntimeError("Can't find specified pointer in rule!")
        # Now we have the pointer location in Rule
        Offset = RulePointerPos - RulePosition  #might be positive, or negative

        StrPointerPos = StrPosition+Offset
        StrPointerToken = StrTokenList.get(StrPointerPos)

    return StrPointerToken


# Unification: <['^V-' ] [不] ^V[V|V0|v]> // Test: 学不学习； 侃不侃大山
#In rule, start from RulePosition, seach for pointer:
#   Start from left side, if not found, seach right side.
# After that is found, use the offset to locate the token in StrTokens
#  compare the pointertoken to the current token (both in StrTokens),
#   return the compare result.
# Update: ^N : 香味   0
#           ^-N: PointerIsSuffix  味  1   ^N-: PointerIsPrefix  香     2
#           -^-N: '-味'          臭味  3   ^N--:  '香-'          香气   4
#           ^-N-: '味-'          味道  5   -^N-:  '-香'          夜来香  6

def PointerMatch(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer, matchtype='norm'):

    if re.match("-\^(.+)-", Pointer):
        P = "^"+Pointer[2:-1]
        PointerType = 6
    elif re.match("\^-(.+)-", Pointer):
        P = "^"+Pointer[2:-1]
        PointerType = 5
    elif re.match("\^(.+)--", Pointer):
        P = "^"+Pointer[1:-2]
        PointerType = 4
    elif re.match("-\^-(.+)", Pointer):
        P = "^"+Pointer[3:]
        PointerType = 3
    elif re.match("\^(.+)-", Pointer):
        P = "^"+Pointer[1:-1]
        PointerType = 2
    elif re.match("\^-(.+)", Pointer):
        P = "^"+Pointer[2:]
        PointerType = 1
    else:
        P = "^"+Pointer[1:] # should be ^N
        PointerType = 0

    StrPointerToken = LocateStrTokenOfPointer(StrTokenList, StrPosition, RuleTokens, RulePosition, P)

    strToken = StrTokenList.get(StrPosition)

    if matchtype == "text":
        return strToken.text and StrPointerToken.text \
               and( (PointerType == 0 and StrPointerToken.text == strToken.text)
                or (PointerType == 1 and StrPointerToken.text.endswith(  strToken.text))
                or (PointerType == 2 and StrPointerToken.text.startswith(strToken.text))
                or (PointerType == 3 and StrPointerToken.text.endswith(  strToken.text[-1]))
                or (PointerType == 4 and StrPointerToken.text.startswith(strToken.text[0])  )
                or (PointerType == 5 and StrPointerToken.text.endswith(  strToken.text[0]))
                or (PointerType == 6 and StrPointerToken.text.startswith(strToken.text[-1])  )
                                   )
    elif matchtype == "norm":
        return strToken.norm and StrPointerToken.norm \
               and( (PointerType == 0 and StrPointerToken.norm == StrTokenList.get(StrPosition).norm)
                or (PointerType == 1 and StrPointerToken.norm.endswith(  strToken.norm))
                or (PointerType == 2 and StrPointerToken.norm.startswith(strToken.norm))
                or (PointerType == 3 and StrPointerToken.norm.endswith(  strToken.norm[-1]))
                or (PointerType == 4 and StrPointerToken.norm.startswith(strToken.norm[0])  )
                or (PointerType == 5 and StrPointerToken.norm.endswith(  strToken.norm[0]))
                or (PointerType == 6 and StrPointerToken.norm.startswith(strToken.norm[-1])  )
                                   )
    elif matchtype == "atom":
        return strToken.atom and StrPointerToken.atom \
               and( (PointerType == 0 and StrPointerToken.atom == StrTokenList.get(StrPosition).atom)
                or (PointerType == 1 and StrPointerToken.atom.endswith(  strToken.atom))
                or (PointerType == 2 and StrPointerToken.atom.startswith(strToken.atom))
                or (PointerType == 3 and StrPointerToken.atom.endswith(  strToken.atom[-1]))
                or (PointerType == 4 and StrPointerToken.atom.startswith(strToken.atom[0])  )
                or (PointerType == 5 and StrPointerToken.atom.endswith(  strToken.atom[0]))
                or (PointerType == 6 and StrPointerToken.atom.startswith(strToken.atom[-1])  )
                                   )
    else:
        logging.error("Rule token:" + str(RuleTokens[RulePosition]))
        raise RuntimeError("The matchtype should be text/norm/atom. Please check syntax!")


#Note: here Pointer (subtreepointer) does not have "^"
def FindPointerNode(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer):
    StrPointerRootToken = None

    tree = Pointer.split(".")

    rootPointer = "^" + tree[0]
    x = StrTokenList.head
    while x:
        if x.TempPointer == rootPointer:
            StrPointerRootToken = x
            break
        x = x.next
    if not StrPointerRootToken:
        logging.error("FindPointerNode Can't find specified pointer " + Pointer + " in rule:")
        logging.error(" ".join([str(r) for r in RuleTokens]))
        raise RuntimeError("Can't find specified pointer in rule!")

    if len(tree)>1:
        return FindSubtree(StrPointerRootToken, tree[1:])
    else:
        return StrPointerRootToken


def FindSubtree(root, pointers):
    for son in root.sons:
        if son.UpperRelationship == pointers[0]:
            if len(pointers) > 1:
                return FindSubtree(son, pointers[1:])
            else:
                return son

    #if come to here, then no relation is found. need to get the head to continue
    for son in root.sons:
        if son.UpperRelationship == "H" or son.UpperRelationship == "":   #this is head
            return FindSubtree(son, pointers)

    #if come to here, then no relation and no head is found.
    #logging.debug("This string has no relation of:" + str(pointers))
    return None



def LogicMatch(StrTokenList, StrPosition, RuleToken, RuleTokens, RulePosition):
    if not RuleToken.word:  # for the comparison of "[]", can match anything
        return True

    if RuleTokens[RulePosition].SubtreePointer:
        SubtreePointer = RuleTokens[RulePosition].SubtreePointer
        #logging.debug("Start looking for Subtree: " + SubtreePointer)
        strToken = FindPointerNode(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer=SubtreePointer)
        if not strToken:
            #logging.debug("there is no such pointer.")
            return False
    else:
        strToken = StrTokenList.get(StrPosition)

    if not strToken:
        logging.error("In LogicMatch(): Can't find strToken!")
        return False

    if RuleToken.word in strToken.FailedRuleTokens:
        return False

    #AndFeatures, OrFeatureGroups, NotFeatures, AndText, NotTexts
    if RuleToken.AndFeatures:
        for f in RuleToken.AndFeatures:
            if f not in strToken.features:
                strToken.FailedRuleTokens.add(RuleToken.word)
                return False

        # CommonAndFeatutures = RuleToken.AndFeatures.intersection(strToken.features)
        # if len(CommonAndFeatutures) < len(RuleToken.AndFeatures):
        #     return False

    if RuleToken.AndText:
        #ruletext, matchtype = CheckPrefix(RuleToken.AndText)
        if  strToken.Head0Text and not RuleToken.FullString:
            word = strToken.Head0Text
        else:
            if RuleToken.AndTextMatchtype == "text":
                word = strToken.text
            elif RuleToken.AndTextMatchtype == "norm":
                word = strToken.norm
            else:
                word = strToken.atom
        if not LogicMatchText(RuleToken.AndText, word):
            strToken.FailedRuleTokens.add(RuleToken.word)
            return False

    for OrFeatureGroup in RuleToken.OrFeatureGroups:
        CommonOrFeatures = OrFeatureGroup.intersection(strToken.features)
        if len(CommonOrFeatures) == 0:
#            strToken.FailedRuleTokens.add(RuleToken.word)
            return False    #we need at least one common features.

    for f in RuleToken.NotFeatures:
        if f in strToken.features:
#                strToken.FailedRuleTokens.add(RuleToken.word)
            return False
    # CommonNotFeatures = RuleToken.NotFeatures.intersection(strToken.features)
    # if len(CommonNotFeatures) > 0:
    #     return False    #can't have any of NotFeatures

    if RuleToken.NotTexts:
        #ruletext, matchtype = CheckPrefix(RuleToken.NotText)
        if RuleToken.FullString and strToken.Head0Text:
            word = strToken.Head0Text
        else:
            if RuleToken.NotTextMatchtype == "text":
                word = strToken.text
            elif RuleToken.NotTextMatchtype == "norm":
                word = strToken.norm
            else:
                word = strToken.atom
        for NotText in RuleToken.NotTexts:
            if LogicMatchText(NotText, word):
    #            strToken.FailedRuleTokens.add(RuleToken.word)
                return False

    return True

#
# def LogicMatch_old(StrTokenList, StrPosition, rule, RuleTokens, RulePosition):
#     if not rule:  # for the comparison of "[]", can match anything
#         return True
#
#     if RuleTokens[RulePosition].SubtreePointer:
#         SubtreePointer = RuleTokens[RulePosition].SubtreePointer
#         #logging.debug("Start looking for Subtree: " + SubtreePointer)
#         strToken = FindPointerNode(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer=SubtreePointer)
#         if not strToken:
#             #logging.debug("there is no such pointer.")
#             return False
#     else:
#         strToken = StrTokenList.get(StrPosition)
#
#     if not strToken:
#         logging.error("In LogicMatch(): Can't find strToken!")
#         return False
#
#     AndBlocks = rule.split()
#     for AndBlock in AndBlocks:
#         Not = False
#         if AndBlock[0] == "!":
#             Not = True
#             AndBlock = AndBlock[1:]
#         ruleblock, matchtype = CheckPrefix(AndBlock)
#         if matchtype == "unknown":
#             if Not == LogicMatchFeatures(ruleblock, strToken.features):
#                 return False
#         elif matchtype in ["text", "norm", "atom"]:
#             if "^" in ruleblock:
#                 #This is a pointer!
#                 if Not == PointerMatch(StrTokenList, StrPosition, RuleTokens, RulePosition, Pointer=ruleblock, matchtype=matchtype):
#                     return False
#
#             if  "FULLSTRING" not in rule  and strToken.Head0Text:
#                 word = strToken.Head0Text
#             else:
#                 if matchtype == "text":
#                     word = strToken.text
#                 elif matchtype == "norm":
#                     word = strToken.norm
#                 else:
#                     word = strToken.atom
#
#             if Not == LogicMatchText(ruleblock, word):
#                 return False
#         else:
#             logging.warning("Suspicous type:" + str(matchtype))
#             return False
#     return True
#

@lru_cache(1000000)
def LogicMatchText(ruletext, stringtext):
    # if (ruletext, stringtext) in LogicMatchText_Cache:
    #     return LogicMatchText_Cache[(ruletext, stringtext)]

    if "|" in ruletext:
        logging.warning("OrBlocks in LogicMatchText:" + ruletext + " ") #should have been split during compilation
        OrBlocks = ruletext.split("|")
        for OrBlock in OrBlocks:
            if LogicMatchText(OrBlock, stringtext):
                return True
    else:
        if ruletext.lower() == stringtext.lower():
            return True
        else:
            if ruletext.endswith('-') or ruletext.startswith('-'):
                if len(ruletext) > 1 and (
                        ruletext.endswith('-') and stringtext.startswith(ruletext[:-1])
                        or ruletext.startswith('-') and stringtext.endswith(ruletext[1:])
                        ):
                    return True

    return False

#
# # If the rule has not quotes, but it is not a feature,
# #   then it is treated as stem.
# # this should have been taken care of by compilation.
# def LogicMatchFeatures(rule, features):
#     if "|" in rule:
#         OrBlocks = rule.split("|")
#         for OrBlock in OrBlocks:
#             featureID = FeatureOntology.GetFeatureID(OrBlock)
#             if featureID in features:
#                 return True
#     else:
#         featureID = FeatureOntology.GetFeatureID(rule)
#         if featureID == -1:
#             logging.warning("Found a feature of rule that is not a feature in feature.txt")
#             logging.warning("rule text:" + rule)
#             logging.warning("This should not happen. Please rewirte the rule for compilation.")
#             return False
#             #return LogicMatch(StrTokenList, StrPosition, rule, RuleTokens, RulePosition, "norm", strToken=strToken)
#         elif featureID == utils.FeatureID_FULLSTRING:
#             return True     #Ignore "FULLSTRING" in feature comparison.
#         else:
#             return featureID in features
#
#     return False
#

@lru_cache(100000)
def SeparateOrBlocks(OrString):
    if "|" not in OrString:
        return [OrString]
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
