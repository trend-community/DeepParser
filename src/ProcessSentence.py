import traceback
import Tokenization, FeatureOntology, Lexicon
import Rules
from LogicOperation import LogicMatch, FindPointerNode #, LogicMatchFeatures
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
    StopPosition = StartPosition+rule.StrTokenLength - 1
    while p:
        if counter == StartPosition+1:
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
        output += '[Rule file]' + rule.FileName +  '[' + str(rule.ID) + '] [Rule origin]' + rule.Origin + ' [Hits_num]' + str(len(hits)) + ' [Hits]\t' + str(hits) + "\n"

    return output


#Every token in ruleTokens must match each token in strTokens, from StartPosition.
def HeadMatch(strTokenList, StartPosition, ruleTokens):

    for i in range(len(ruleTokens)):
        try:
            if not LogicMatch(strTokenList, i+StartPosition, ruleTokens[i].word, ruleTokens, i):
                RemoveTempPointer(strTokenList)
                return False  #  this rule does not fit for this string
            if ruleTokens[i].SubtreePointer:
                StartPosition -= 1  # do not skip to next strToken, if this token is for Subtree.
            if ruleTokens[i].pointer:
                strTokenList.get(i + StartPosition).TempPointer = ruleTokens[i].pointer
        except RuntimeError as e:
            logging.error("Error in HeadMatch rule:" + str(ruleTokens))
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text)
            logging.error(e)
            # raise
        except Exception as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text )
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text )
            logging.error(e)
            raise
    #RemoveTempPointer(strTokenList)
    return True


def RemoveTempPointer(StrList):
    x = StrList.head
    while x:
        x.TempPointer = ''
        x = x.next


def MarkTempPointer(strtokens, rule, StrStartPosition):
    VirtualRuleToken = 0
    for i in range(len(rule.Tokens)):
        if rule.Tokens[i].SubtreePointer:
            VirtualRuleToken += 1
        if rule.Tokens[i].pointer:
            strtokens.get(i + StrStartPosition - VirtualRuleToken).TempPointer = rule.Tokens[i].pointer


# Apply the features, and other actions.
def ApplyWinningRule(strtokens, rule, StartPosition):

    if not strtokens:
        logging.error("The strtokens to ApplyWinningRule is blank!")
        raise(RuntimeError("wrong string to apply rule?"))
    StoreWinningRule(strtokens, rule, StartPosition)

    if len(rule.Tokens) == 0:
        logging.error("Lenth = 0, error! Need to revisit the parsing process")
        logging.error(str(rule))
        raise(RuntimeError("Rule error"))

    #MarkTempPointer(strtokens, rule, StartPosition)
    VirtualRuleToken = 0
    for i in range(len(rule.Tokens)):
        if rule.Tokens[i].SubtreePointer:
            VirtualRuleToken += 1

        if rule.Tokens[i].action:
            if rule.Tokens[i].SubtreePointer:
                SubtreePointer = rule.Tokens[i].SubtreePointer
                logging.debug("Start looking for Subtree: " + SubtreePointer)
                token = FindPointerNode(strtokens, i + StartPosition - VirtualRuleToken, rule.Tokens, i, Pointer=SubtreePointer)
            else:
                token = strtokens.get(i + StartPosition - VirtualRuleToken)

            token.ApplyActions(rule.Tokens[i].action)

    if rule.Chunks:
        MaxChunkLevelNum = max(chunk.ChunkLevel for chunk in rule.Chunks)
        for ChunkLevel in range(1,MaxChunkLevelNum+1):
            for chunk in rule.Chunks:   # the chunks are presorted to process right chucks first.
                if chunk.ChunkLevel != ChunkLevel:
                    continue
                strtokens.combine(StartPosition+chunk.StartOffset, chunk.StringChunkLength, chunk.HeadOffset)
                strtokens.get(StartPosition+chunk.StartOffset).ApplyActions(chunk.Action)

    RemoveTempPointer(strtokens)
    return 0


#list1 is combination of norm and Head0Text.
# either of them equals to the item in list2, that means match.
#from functools import lru_cache
#@lru_cache(maxsize=100000)
def ListMatch(list1, list2):
    if len(list1) != len(list2):
        logging.error("Coding error. The size should be the same in ListMatch")
        return False
    for i in range(len(list1)):
        if list2[i] is None or \
            list1[i][0] == list2[i] or \
                len(list1[i]) == 2 and list1[i][1] == list2[i]:
            pass
        else:
            return False

    return True

#Note: the _UsingCache version is slower: 25 seconds instead of 16 seconds, for 100 sentences.
# for 4503026 calls, it took 12 seconds, comparing to 4 seconds.
ListMatchCache = {}
def ListMatch_UsingCache(list1, list2):
    l_hash = str(list1+list2)
    if l_hash in ListMatchCache:
        return ListMatchCache[l_hash]
    if len(list1) != len(list2):
        logging.error("Coding error. The size should be the same in ListMatch")
        return False
    for i in range(len(list1)):
        if list2[i] is None or list1[i] == list2[i]:
            pass
        else:
            ListMatchCache[l_hash] = False
            return False

    ListMatchCache[l_hash] = True
    return True

# HeadMatchCache = {}
# RuleSizeLimit = 6
def MatchAndApplyRuleFile(strtokenlist, RuleFileName):
    WinningRules = {}
    i = 0
    logging.debug("Matching using file:" + RuleFileName)

    strtoken = strtokenlist.head
    strnorms = strtokenlist.norms()
    while strtoken:
        # strsignatures = strtokenlist.signature(i, min([RuleSizeLimit, strtokenlist.size-i]))

        logging.debug("Checking tokens start from:" + strtoken.text)
        WinningRule = None
        rulegroup = Rules.RuleGroupDict[RuleFileName]
        WinningRuleSize = 0
        for rule in rulegroup.RuleList:
            if rule.StrTokenLength > strtokenlist.size-i:
                continue

            if not ListMatch(strnorms[i:i+rule.StrTokenLength], rule.norms):
                continue

            if WinningRuleSize < len(rule.Tokens):
                result = HeadMatch(strtokenlist, i, rule.Tokens)
                if result:
                    WinningRule = rule
                    WinningRuleSize = len(WinningRule.Tokens)
                    break   #Because the file is sorted by rule length, so we are satisfied with the first winning rule.
                    # if WinningRuleSize + i >= strtokenlist.size:
                    #     logging.debug("Found a winning rule that matchs up to the end of the string.")
                    #     break
        if WinningRule:
            try:
                if WinningRule.RuleName not in WinningRules:
                    WinningRules[WinningRule.RuleName] = '<li>' + WinningRule.Origin + ' <li class="indent">' + MarkWinningTokens(strtokenlist, WinningRule, i)
                else:
                    WinningRules[WinningRule.RuleName] += ' <li class="indent">' + MarkWinningTokens(strtokenlist, WinningRule, i)
                ApplyWinningRule(strtokenlist, WinningRule, StartPosition=i)
                strnorms = strtokenlist.norms()     #the list is updated.
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + RuleFileName)
                    rulegroup.RuleList.remove(WinningRule)
                else:
                    logging.error("Unknown Rule Applying Error:" + str(e))

            except IndexError as e:
                logging.error("Failed to apply this rule:")
                logging.error(str(WinningRule))
                logging.error(str(e))
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
            # if NodeList:
            #     logging.debug(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

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
    p = nodes.head.next
    while p.next:
        if utils.FeatureID_SYM not in p.features:
            p.ApplyFeature(utils.FeatureID_JS2)
            break
        p.ApplyFeature(utils.FeatureID_JS2)
        p = p.next

    PUNCSet = {".", "?", "!", ";", "...", ":", "。"}
    if utils.FeatureID_SYM not in nodes.tail.features and \
            nodes.tail.text not in PUNCSet  :
        JMnode = Tokenization.SentenceNode('')
        JMnode.StartOffset = nodes.tail.EndOffset
        JMnode.EndOffset = nodes.tail.EndOffset
        JMnode.ApplyFeature(utils.FeatureID_punc)
        nodes.append(JMnode)
    nodes.tail.ApplyFeature(utils.FeatureID_JM)
    nodes.tail.ApplyFeature(utils.FeatureID_JM2)
    p = nodes.tail.prev
    while p.prev:
        if utils.FeatureID_SYM not in p.features:
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
    Lexicon.LoadLexicon(XLocation + 'LexX-brandX.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-idiomXdomain.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-idiomX.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-locX.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-perX.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-EnglishPunctuate.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-ChinesePunctuate.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-brandsKG.txt')

    Lexicon.LoadLexicon(XLocation + 'defPlus.txt', lookupSource=LexiconLookupSource.defLex)
    Lexicon.LoadLexicon(XLocation + 'defLexX.txt', lookupSource=LexiconLookupSource.defLex)
    Lexicon.LoadLexicon(XLocation + 'defLexXKG.txt', lookupSource=LexiconLookupSource.defLex)

    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_2_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_3_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_4_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_5_list.txt', lookupSource=LexiconLookupSource.External)
    Lexicon.LoadLexicon(XLocation + 'Q/lexicon/comment_companyname.txt',    lookupSource=LexiconLookupSource.External)

    Lexicon.LoadSegmentLexicon()    #note: the locations are hard-coded
    Lexicon.LoadExtraReference(XLocation + 'CuobieziX.txt', Lexicon._LexiconCuobieziDict)
    Lexicon.LoadExtraReference(XLocation + 'Fanti.txt', Lexicon._LexiconFantiDict)

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

    # Rules.ExpandRuleWildCard()
    # Rules.ExpandParenthesisAndOrBlock()
    # Rules.ExpandRuleWildCard()
    # Rules.PreProcess_CheckFeatures()
    # Rules.PreProcess_CompileHash()
    # Rules.SortByLength()

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    LoadCommon()

    target = "能油比高是优点还是缺点？"

    # import cProfile, pstats
    # cProfile.run("LexicalAnalyze(target)", 'restatslex')
    # pstat = pstats.Stats('restatslex')
    # pstat.sort_stats('time').print_stats(10)



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
