import logging, re, requests, jsonpickle, traceback, os
import Tokenization, FeatureOntology, Lexicon
import Rules
from LogicOperation import LogicMatch #, LogicMatchFeatures
from utils import *
import utils
counterMatch = 0

WinningRuleDict = {}
invalidchar_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
PipeLine = []

def MarkWinningTokens(strtokens, rule, StartPosition):
    result = ""
    if strtokens.size >= 3:
        AddSpace = IsAscii(strtokens.get(1).text) and IsAscii(strtokens.get(strtokens.size-2).text) and utils.IsAscii(strtokens.get(int(strtokens.size/2)).text)
    else:
        AddSpace = IsAscii(strtokens.get(1).text)

    p = strtokens.head
    counter = 0
    StopPosition = StartPosition+len(rule.Tokens) - 1
    while p:
        if counter == StartPosition:
            result += "<em>"
        result += p.text
        if counter == StopPosition:
            result += "</em>"
        if AddSpace:
            result += " "
        p = p.next
        counter += 1

    return result.strip()


def StoreWinningRule(strtokens, rule, StartPosition):
    global WinningRuleDict

    if rule.ID in WinningRuleDict:
        _, hits = WinningRuleDict[rule.ID]
        hits.append(MarkWinningTokens(strtokens, rule, StartPosition))
    else:
        WinningRuleDict[rule.ID] = [rule, [MarkWinningTokens(strtokens, rule, StartPosition)]]


def OutputWinningRules():
    output = ""

    for rule, hits in sorted(WinningRuleDict.values()):
        output += '[Rule file]' + rule.FileName +  ' [Rule origin]' + rule.Origin + ' [Hits_num]' + str(len(hits)) + ' [Hits]\t' + str(hits) + "\n"

    return output


#Every token in ruleTokens must match each token in strTokens, from StartPosition.
def HeadMatch(strTokenList, StartPosition, ruleTokens):

    for i in range(len(ruleTokens)):
        try:
            if not LogicMatch(strTokenList, i+StartPosition, ruleTokens[i].word, ruleTokens, i):
                return False  #  this rule does not fit for this string
            if hasattr(ruleTokens[i], "SubtreePointer"):
                i -= 1  #do not skip to next strToken, if this Subtree Rule is matched.
        except RuntimeError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i).word)
            logging.error(e)
            # raise
        except Exception as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i).word )
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i).word )
            logging.error(e)
            raise

    return True


# Apply the features, and other actions.
#TODO: Apply Mark ".M", group head <, tail > ...
# Return: the position of the last merged chunk
def ApplyWinningRule(strtokens, rule, StartPosition):

    if not strtokens:
        logging.error("The strtokens to ApplyWinningRule is blank!")
        raise(RuntimeError("wrong string to apply rule?"))
    if strtokens.size > 2:
        logging.info("Applying Winning Rule:" + rule.RuleName +" to "
                     + strtokens.get(1).text + strtokens.get(2).text + "...")
        #print(str(rule))
        #logging.debug(jsonpickle.dumps(strtokens))
    StoreWinningRule(strtokens, rule, StartPosition)

    if len(rule.Tokens) == 0:
        logging.error("Lenth = 0, error! Need to revisit the parsing process")
        logging.error(str(rule))
        raise(RuntimeError("Rule error"))
    for i in range(len(rule.Tokens)):
        token = strtokens.get(i+StartPosition)
        # try:
        #     logging.debug("Before:\n" + "in position " + str(StartPosition + i )
        #                   + " Rule is:" + jsonpickle.dumps(rule.Tokens[i]))
        # except IndexError as e:
        #     logging.error("Wrong when trying to debug and dump. maybe the string is not long enough?")
        #     logging.error(str(rule))
        #     logging.error(str(e))
        #     return len(rule.Tokens)

        if hasattr(rule.Tokens[i], 'action'):
            token.ApplyActions(rule.Tokens[i].action)

    if rule.Chunks:
        MaxChunkLevelNum = max(chunk.ChunkLevel for chunk in rule.Chunks)
        for ChunkLevel in range(1,MaxChunkLevelNum+1):

            for chunk in rule.Chunks:
                if chunk.ChunkLevel != ChunkLevel:
                    continue

                #print("New Chunk: strtokens.combine(%d, %d, %d)"%(StartPosition+chunk.StartOffset, chunk.Length, chunk.HeadOffset))
                strtokens.combine(StartPosition+chunk.StartOffset, chunk.StringChunkLength, chunk.HeadOffset)

                strtokens.get(StartPosition+chunk.StartOffset).ApplyActions(chunk.Action)

    return 0 #need to modify for those "forward looking rules"


# HeadMatchCache = {}
# RuleSizeLimit = 6
def MatchAndApplyRuleFile(strtokenlist, RuleFileName):
    WinningRules = {}
    i = 0
    logging.debug("Matching using file:" + RuleFileName)

    strtoken = strtokenlist.head
    while strtoken:
        # strsignatures = strtokenlist.signature(i, min([RuleSizeLimit, strtokenlist.size-i]))

        logging.debug("Checking tokens start from:" + strtoken.text)
        WinningRule = None
        rulegroup = Rules.RuleGroupDict[RuleFileName]
        WinningRuleSize = 0
        for rule in rulegroup.RuleList:
            ruleSize = len(rule.Tokens)
            if i+ruleSize > strtokenlist.size:
                continue
            if WinningRuleSize < ruleSize:
                # if ruleSize < len(strsignatures):
                #     pairSignature = str([strsignatures[ruleSize-1], rule.ID])
                # else:
                #     pairSignature = None
                # if pairSignature in HeadMatchCache:
                #     result = HeadMatchCache[pairSignature]
                #     # logging.debug("HeadMatchCache hit! " + str(result))
                #     # logging.debug("\tSize of HeadMatchCache:" + str(len(HeadMatchCache)))
                # else:
                result = HeadMatch(strtokenlist, i, rule.Tokens)
                    # if len(HeadMatchCache) < 1000000:
                    #     passls
                    #     HeadMatchCache[pairSignature] = result
                if result:
                    WinningRule = rule
                    WinningRuleSize = len(WinningRule.Tokens)
                    if WinningRuleSize + i >= strtokenlist.size:
                        logging.debug("Found a winning rule that matchs up to the end of the string.")
                        break
        if WinningRule:
            # rulegroup.RuleList.remove(WinningRule)
            # rulegroup.RuleList.insert(0, WinningRule)
            # logging.info("rulelist of " + rulegroup.FileName + " is modified to have this on top:" + str(WinningRule))
            try:
                if WinningRule.RuleName not in WinningRules:
                    WinningRules[WinningRule.RuleName] = MarkWinningTokens(strtokenlist, WinningRule, i)
                else:
                    WinningRules[WinningRule.RuleName] += " " + MarkWinningTokens(strtokenlist, WinningRule, i)
                skiptokennum = ApplyWinningRule(strtokenlist, WinningRule, StartPosition=i)
                #logging.debug("After applied: " + jsonpickle.dumps(strtokenlist))
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + RuleFileName)
                    rulegroup.RuleList.remove(WinningRule)
                    skiptokennum = 0
            #i += skiptokennum - 1  # go to the next word


        i += 1
        strtoken = strtoken.next
    return WinningRules


def DynamicPipeline(NodeList):
    WinningRules = {}

    for action in PipeLine:
        if action == "segmentation":
            continue
        if action == "apply lexicons":
            continue
        if action.startswith("FSA"):
            Rulefile = action[3:].strip()
            WinningRules.update(MatchAndApplyRuleFile(NodeList, Rulefile))

        if action.startswith("lookup"):
            lookupSourceName = action[6:].strip()
            for x in LexiconLookupSource:
                if x.name == lookupSourceName:
                    Lexicon.LexiconLookup(NodeList, x)
    return  WinningRules


def PrepareJSandJM(nodes):
    nodes.head.ApplyFeature(utils.FeatureID_JS2)
    JSnode = Tokenization.SentenceNode('')
    JSnode.ApplyFeature(utils.FeatureID_JS)
    JSnode.ApplyFeature(utils.FeatureID_JS2)
    nodes.insert(JSnode, 0)

    if utils.FeatureID_punc not in nodes.tail.features:
        JMnode = Tokenization.SentenceNode('')
        JMnode.StartOffset = nodes.tail.EndOffset
        JMnode.EndOffset = nodes.tail.EndOffset
        nodes.append(JMnode)
    nodes.tail.ApplyFeature(utils.FeatureID_JM)
    nodes.tail.ApplyFeature(utils.FeatureID_JM2)
    p = nodes.tail.prev
    while p.prev:
        if utils.FeatureID_punc not in p.features:
            # first one that is not punc. the real JM2:
            p.ApplyFeature(utils.FeatureID_JM2)
            break
        p.ApplyFeature(utils.FeatureID_JM2)
        p = p.prev


def LexicalAnalyze(Sentence):
    try:
        logging.debug("-Start LexicalAnalyze: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)
        NodeList = Tokenization.Tokenize(Sentence)
        if not NodeList or NodeList.size == 0:
            return None, None
        logging.debug("-Start ApplyLexiconToNodes")
        #print("after tokenize" + OutputStringTokens_oneliner(NodeList))
        Lexicon.ApplyLexiconToNodes(NodeList)
        #print("after ApplyLexiconToNodes" + OutputStringTokens_oneliner(NodeList))

        PrepareJSandJM(NodeList)

        WinningRules = DynamicPipeline(NodeList)

        logging.debug("-End LexicalAnalyze")

    except Exception as e:
        logging.error("Overall Error in LexicalAnalyze:")
        logging.error(e)
        logging.error(traceback.format_exc())
        return None, None

    return NodeList, WinningRules


def LoadPipeline(PipelineLocation):
    if PipelineLocation.startswith("."):
        PipelineLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  PipelineLocation)
    with open(PipelineLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            action, _ = SeparateComment(line)
            if not action:
                continue
            PipeLine.append(action.strip())


def LoadCommon():
    #FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    #Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    #Lexicon.LoadLexicon('../../fsa/X/QueryLexicon.txt')

    XLocation = '../../fsa/X/'

    Lexicon.LoadLexicon(XLocation + 'LexX.txt')
    Lexicon.LoadLexicon(XLocation + 'LexXplus.txt')
    Lexicon.LoadLexicon(XLocation + 'brandX.txt')
    Lexicon.LoadLexicon(XLocation + 'idiom4X.txt')
    Lexicon.LoadLexicon(XLocation + 'idiomX.txt')
    Lexicon.LoadLexicon(XLocation + 'locX.txt')
    Lexicon.LoadLexicon(XLocation + 'perX.txt')
    Lexicon.LoadLexicon(XLocation + 'defPlus.txt')
    Lexicon.LoadLexicon(XLocation + 'ChinesePunctuate.txt')
    Lexicon.LoadLexicon(XLocation + 'defLexX.txt', lookupSource=LexiconLookupSource.defLex)

    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_2_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_3_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_4_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_5_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/comment_companyname.txt', lookupSource=LexiconLookupSource.External)

    LoadPipeline(XLocation + 'pipelineX.txt')

    logging.debug("Runtype:" + ParserConfig.get("main", "runtype"))
    logging.debug("utils.Runtype:" + utils.ParserConfig.get("main", "runtype"))

    if ParserConfig.get("main", "runtype") == "Debug":
        RuleFolder = XLocation
    else:
        RuleFolder = ParserConfig.get("main", "compiledfolder")
    for action in PipeLine:
        if action.startswith("FSA"):
            Rulefile = action[3:].strip()
            Rulefile = os.path.join(RuleFolder, Rulefile)
            Rules.LoadRules(Rulefile)

    # Rules.LoadRules("../../fsa/X/0defLexX.txt")
    # Rules.LoadRules("../../fsa/Y/800VGy.txt")
    # Rules.LoadRules("../../fsa/Y/900NPy.xml")
    # Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    # Rules.LoadRules("../../fsa/Y/1test_rules.txt")


    #Rules.LoadRules("../../fsa/X/Q/rule/xac")
    # Rules.LoadRules("../../fsa/X/Q/rule/xab")
    # Rules.LoadRules("../../fsa/X/Q/rule/xac")
    # Rules.LoadRules("../../fsa/X/Q/rule/CleanRule_gram_4_list.txt")
    # Rules.LoadRules("../../fsa/X/Q/rule/CleanRule_gram_5_list.txt")

    #Rules.LoadRules("../../fsa/X/270VPx.txt")

    Rules.ExpandRuleWildCard()
    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()
    Rules.PreProcess_CheckFeatures()
    Rules.SortByLength()

    if ParserConfig.get("main", "runtype") == "Debug":
        logging.debug("Start writing temporary rule files")
        Rules.OutputRuleFiles(ParserConfig.get("main", "compiledfolder"))
        FeatureOntology.OutputFeatureOntologyFile(ParserConfig.get("main", "compiledfolder"))
        logging.debug("Start writing temporary lex file.")
        #Lexicon.OutputLexiconFile(ParserConfig.get("main", "compiledfolder"))

    logging.debug("Done of LoadCommon!")
        #print(Lexicon.OutputLexicon(False))

if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    LoadCommon()

    target = "手毛,短柄"
    m_nodes, winningrules = LexicalAnalyze(target)
    if not m_nodes:
        logging.warning("The result is None!")
        exit(1)


    logging.info("\tDone! counterMatch=%s" % counterMatch)

    print(OutputStringTokens_oneliner(m_nodes, NoFeature=True))
    print(OutputStringTokens_oneliner(m_nodes))


    print("Winning rules:\n" + OutputWinningRules())

    print(FeatureOntology.OutputMissingFeatureSet())

    print(m_nodes.root().CleanOutput().toJSON())
    print(m_nodes.root().CleanOutput_FeatureLeave().toJSON())
    print(m_nodes.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
