
from utils import *

#not, and, or
#compare type: word/norm/stem/feature


#   Sometimes it is like:  'a|b|c'
#   sometimes it is like:  a|'b'|c
# so CheckPrefix() is being called from LogicMatch()
from functools import lru_cache
# return -1 if failed. Should throw error?
@lru_cache(100000)
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
#    elif word[0] == "." and word.find(".", 1) == lastlocation :
    elif word[0] == "." and word[-1] == ".":
        word = word.strip(".")
        matchtype = "fuzzy"      # fuzzy checking: can be text/norm/atom, can be multiple nodes.

    return prefix+word, matchtype


#Usage:  [] <[A] [B] [^2.S=x]>  //usage ^2 to point to the 3rd token of the rule.
def GetNumberPointer(Pointer):
    PointerContent = Pointer[1:]
    if len(PointerContent) == 0:    #[^.O]  when nothing is given, then it is the first.
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
            #logging.info("LocateStrTokenOfPointer: Searching along the rule tokens to find pointer {}".format(Pointer))
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
               and( (PointerType == 0 and StrPointerToken.norm == strToken.norm)
                or (PointerType == 1 and StrPointerToken.norm.endswith(  strToken.norm))
                or (PointerType == 2 and StrPointerToken.norm.startswith(strToken.norm))
                or (PointerType == 3 and StrPointerToken.norm.endswith(  strToken.norm[-1]))
                or (PointerType == 4 and StrPointerToken.norm.startswith(strToken.norm[0])  )
                or (PointerType == 5 and StrPointerToken.norm.endswith(  strToken.norm[0]))
                or (PointerType == 6 and StrPointerToken.norm.startswith(strToken.norm[-1])  )
                                   )
    elif matchtype == "atom":
        return strToken.atom and StrPointerToken.atom \
               and( (PointerType == 0 and StrPointerToken.atom == strToken.atom)
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


#Note: here SubtreePointer does not have "^"
def FindPointerNode(StrTokenList, StrPosition, RuleTokens, RulePosition, SubtreePointer):
    StrPointerRootToken = None

    #tree = Pointer.split(".")
    if "." in SubtreePointer:
        pointer, relations = SubtreePointer.split(".", 1)
    else:
        pointer, relations = [SubtreePointer, ""]

    pointer = "^" + pointer

    if pointer == "^~":     #THIS pointer
        StrPointerRootToken = StrTokenList.get(StrPosition)
    else:
    #rootPointer = "^" + tree[0]
        x = StrTokenList.head
        while x:
            if x.TempPointer == pointer:
                StrPointerRootToken = x
                break
            x = x.next

    if not StrPointerRootToken:
        logging.error("FindPointerNode Can't find specified pointer " + pointer + " in rule:")
        logging.error(" ".join([str(r) for r in RuleTokens]))
        logging.info("At this point, StrTokenList={}".format(jsonpickle.dumps(StrTokenList)))
        #return None
        raise RuntimeError("Can't find specified pointer in rule!")

    if relations:
        return _FindSubtree(StrPointerRootToken, relations.split("."))
    else:
        return StrPointerRootToken


def _FindSubtree(root, pointers):
    for son in root.sons:
        if son.UpperRelationship == pointers[0]:
            if len(pointers) > 1:
                return _FindSubtree(son, pointers[1:])
            else:
                return son

    #if come to here, then no relation is found. need to get the head node and continue the search
    for son in root.sons:
        if son.UpperRelationship == "H" :   #this is head
            return _FindSubtree(son, pointers)

    #if come to here, then no relation and no head is found.
    #logging.debug("This string has no relation of:" + str(pointers))
    return None


# = {}
#hitcount = 0
def LogicMatch_notpointer(StrToken, RuleToken, PrevText, PrevNorm, PrevAtom):
    # global hitcount
    # # AndFeatures, OrFeatureGroups, NotFeatures, AndText, NotTexts
    # if (StrToken.ID, RuleToken.ID) in LogicMatch_notpointer_Cache:
    #     hitcount += 1
    #     return LogicMatch_notpointer_Cache[(StrToken.ID, RuleToken.ID)]
    #
    # LogicMatch_notpointer_Cache[(StrToken.ID, RuleToken.ID)] = False
    if RuleToken.AndFeatures:
        for f in RuleToken.AndFeatures:
            if f not in StrToken.features:
                return False

    if RuleToken.AndText:
        if "^" in RuleToken.AndText:
            pass    #being processed in PointerMatch
        else:
            if StrToken.Head0Text and not RuleToken.FullString:
                word = StrToken.Head0Text
                if not LogicMatchText(RuleToken.AndText, word):
                    return False
            else:
                if RuleToken.AndTextMatchtype == "text":
                    if not LogicMatchText(RuleToken.AndText, StrToken.text):
                        return False
                elif RuleToken.AndTextMatchtype == "norm":
                    if not LogicMatchText(RuleToken.AndText, StrToken.norm):
                        return False
                elif RuleToken.AndTextMatchtype == "atom":
                    if not LogicMatchText(RuleToken.AndText, StrToken.atom):
                        return False
                elif RuleToken.AndTextMatchtype == "fuzzy":
                    if not( PrevText.endswith(RuleToken.AndText)
                            or PrevNorm.endswith(RuleToken.AndText)
                            or PrevAtom.endswith(RuleToken.AndText)  ):
                        return False
                else:
                    logging.error("AndTextMatchtype is {} , please check the rule".format(RuleToken.AndTextMatchtype))
                    raise RuntimeError("Unknown TextMatch type")
                    #return False

    for OrFeatureGroup in RuleToken.OrFeatureGroups:
        CommonOrFeatures = OrFeatureGroup.intersection(StrToken.features)
        if len(CommonOrFeatures) == 0:
            return False  # we need at least one common features.

    for f in RuleToken.NotFeatures:
        if f in StrToken.features:
            return False

    if RuleToken.NotTexts:
        if RuleToken.FullString and StrToken.Head0Text:
            word = StrToken.Head0Text
        else:
            if RuleToken.NotTextMatchtype == "text":
                word = StrToken.text
            elif RuleToken.NotTextMatchtype == "norm":
                word = StrToken.norm
            elif RuleToken.AndTextMatchtype == "atom":
                word = StrToken.atom
            else:
                logging.debug("Not ready to use FUZZY comparison in NotText.")
                word = StrToken.norm    #backward compatible only
        for NotText in RuleToken.NotTexts:
            if LogicMatchText(NotText, word):
                return False

    #LogicMatch_notpointer_Cache[(StrToken.ID, RuleToken.ID)] = True
    return True


#Being called after each rule applying (assume the StrToken is modified)
# def Clear_LogicMatch_notpointer_Cache():
#     LogicMatch_notpointer_Cache.clear()


def LogicMatch(StrTokenList, StrPosition, RuleToken, RuleTokens, RulePosition):
    if not RuleToken.word and not RuleTokens[RulePosition].SubtreePointer:  # for the comparison of "[]", can match anything
        RuleToken.MatchedNodeID = StrTokenList.get(StrPosition).ID
        return True

    if RuleTokens[RulePosition].SubtreePointer:
        SubtreePointer = RuleTokens[RulePosition].SubtreePointer
        #logging.debug("Start looking for Subtree: " + SubtreePointer)
        strToken = FindPointerNode(StrTokenList, StrPosition, RuleTokens, RulePosition, SubtreePointer=SubtreePointer)
        if not strToken:
            #logging.debug("there is no such pointer.")
            return False
    else:
        strToken = StrTokenList.get(StrPosition)

    # #strToken.signature = pickle.dumps({"w": strToken.text, "f": strToken.features})
    # if (strToken.signature, RuleToken.word) in Cache.LogicalMatchCache:
    #     # logging.warning("\t\thit the LogicalMatch_Cache!")
    #     # logging.warning(" " + str(strToken) + " in rule token" + str(RuleToken))
    #     return Cache.LogicalMatchCache[(strToken.signature, RuleToken.word)]

    if not strToken:
        logging.error("In LogicMatch(): Can't find strToken!")
        return False

    if RuleToken.AndText and "^" in RuleToken.AndText:
            #This is a pointer! unification comparison.
            if not PointerMatch(StrTokenList, StrPosition, RuleTokens, RulePosition,
                                Pointer=RuleToken.AndText, matchtype=RuleToken.AndTextMatchtype):
                return False

    RuleToken.MatchedNodeID = strToken.ID

    if RuleToken.AndTextMatchtype == "fuzzy":
        PrevText = "".join([StrTokenList.get(i).text.lower() for i in range(StrPosition)])
        PrevNorm = "".join([StrTokenList.get(i).norm.lower() for i in range(StrPosition)])
        PrevAtom = "".join([StrTokenList.get(i).atom.lower() for i in range(StrPosition)])
    else:
        PrevText = ''
        PrevNorm = ''
        PrevAtom = ''
    return LogicMatch_notpointer(strToken, RuleToken, PrevText, PrevNorm, PrevAtom)


@lru_cache(100000)
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
