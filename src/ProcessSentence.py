import traceback
import concurrent.futures
import Tokenization, FeatureOntology, Lexicon
import Rules, Cache
#from threading import Thread
from LogicOperation import LogicMatch, FindPointerNode #, LogicMatchFeatures
from utils import *
import utils
counterMatch = 0

WinningRuleDict = {}
invalidchar_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
PipeLine = []


def MarkWinningTokens(strtokens, rule, StartPosition):
    result = ""

    p = strtokens.head
    counter = 0
    StopPosition = StartPosition+rule.StrTokenLength - 1
    while p:
        if counter == StartPosition+1:
            result += "<em>"
        result += p.text
        if counter == StopPosition:
            result += "</em>"
        if strtokens.isPureAscii:
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
def HeadMatch(strTokenList, StartPosition, rule):
    HaveTempPointer = False

    for i in range(rule.TokenLength):
        try:
            if not LogicMatch(strTokenList, i+StartPosition, rule.Tokens[i], rule.Tokens, i):
        #    if not LogicMatch_old(strTokenList, i + StartPosition, ruleTokens[i].word, ruleTokens, i):
                if HaveTempPointer:
                    RemoveTempPointer(strTokenList)
#                if (rule.ID, i) in Rules.RuleIdenticalNetwork:
#                    FailedRules.update(Rules.RuleIdenticalNetwork[(rule.ID, i)])
                return False  #  this rule does not fit for this string
            if rule.Tokens[i].SubtreePointer:
                StartPosition -= 1  # do not skip to next strToken, if this token is for Subtree.
            if rule.Tokens[i].pointer:
                HaveTempPointer = True
                strTokenList.get(i + StartPosition).TempPointer = rule.Tokens[i].pointer
        except RuntimeError as e:
            logging.error("Error in HeadMatch rule:" + str(rule.Tokens))
            logging.error("Using " + rule.Tokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text)
            logging.error(e)
            # raise
        except Exception as e:
            logging.error("Using " + rule.Tokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text )
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + rule.Tokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text )
            logging.error(e)
            raise
    #RemoveTempPointer(strTokenList)
    return True


def RemoveTempPointer(StrList):
    x = StrList.head
    while x:
        if x.TempPointer:
            x.TempPointer = ''
        x = x.next


def MarkTempPointer_obsolete(strtokens, rule, StrStartPosition):
    VirtualRuleToken = 0
    for i in range(rule.TokenLength):
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

    if rule.TokenLength == 0:
        logging.error("Lenth = 0, error! Need to revisit the parsing process")
        logging.error(str(rule))
        raise(RuntimeError("Rule error"))

    #MarkTempPointer(strtokens, rule, StartPosition)
    VirtualRuleToken = 0
    for i in range(rule.TokenLength):
        if rule.Tokens[i].SubtreePointer:
            VirtualRuleToken += 1

        if rule.Tokens[i].action:
            if rule.Tokens[i].SubtreePointer:
                SubtreePointer = rule.Tokens[i].SubtreePointer
                #logging.debug("Start looking for Subtree: " + SubtreePointer)
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
    # if len(list1) != 2 or  len(list1[0]) != len(list2):
    #     logging.error("Coding error. The size should be the same in ListMatch")
    #     return False
    # for i in range(num):
    #     if list2[i] == '' or \
    #         list1[i][0] == list2[i] or \
    #             list1[i][1] and list1[i][1] == list2[i]:
    #         pass
    #     else:
    #         return False

    i = -1
    for l2item in list2:
        i += 1
        if l2item == '' or \
            list1[i][0] == l2item or \
            list1[i][1] and list1[i][1] == l2item:
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

#
# def ConstructNorms(strtokenlist, start):
#     MaxGramSize = 10    #only care for 10 ngram and less.
#
#     StrNorms = []
#     for i in range( MaxGramSize):
#         if start+i >= len(strtokenlist.norms):
#             break
#
#         newset = set()
#         if i == 0:
#             if strtokenlist.norms[start+i][1]:
#                 newset.update(strtokenlist.norms[start+i][1])
#             newset.update(strtokenlist.norms[start+i][0])
#         else:
#             newset2 = set()
#             for strnorms in StrNorms[i - 1]:
#                 if strtokenlist.norms[start+i][1]:
#                     strnorms_copy = copy.copy(strnorms) + strtokenlist.norms[start+i][1]
#                     newset2.add(strnorms_copy)
#                 newset2.add( strnorms + strtokenlist.norms[start+i][0])
#             newset.update(newset2)
#         StrNorms.append(newset)
#     return StrNorms

#FailedRules: gets set according to RuleIdenticalNetwork. gets reset when apply rule.
def MatchAndApplyRuleFile(strtokenlist, RuleFileName):
    WinningRules = {}
    i = 0
    #logging.debug("Matching using file:" + RuleFileName)
    counter = 0

    strtoken = strtokenlist.head

    while strtoken:
        # strsignatures = strtokenlist.signature(i, min([RuleSizeLimit, strtokenlist.size-i]))

        #logging.debug("Checking tokens start from:" + strtoken.text)
        WinningRule = None
        rulegroup = Rules.RuleGroupDict[RuleFileName]
        #WinningRuleSize = 0
        #StrNorms = ConstructNorms(strtokenlist, i)
        # MaxGramSize = 10

        for rule in rulegroup.RuleList:
            if rule.StrTokenLength > strtokenlist.size-i:
                continue
            # if MaxGramSize > rule.StrTokenLength:
            #     for strnorms in StrNorms[rule.StrTokenLength-1]:
            #         if strnorms in rulegroup.NormHash:
            #             WinningRule = rulegroup.NormHash[strnorms]
            #             break
            # if WinningRule:
            #     break

            if rule.norms and not ListMatch(strtokenlist.norms[i:i+rule.StrTokenLength], rule.norms):
                continue
            counter += 1
            #logging.info("    HeadMatch for rule " + str(rule.ID) + " length:" + str(rule.TokenLength) + " |" + rule.Origin )
            result = HeadMatch(strtokenlist, i, rule)
            if result:
                WinningRule = rule
                break   #Because the file is sorted by rule length, so we are satisfied with the first winning rule.
        if WinningRule:
            logging.debug("Found winning rule at counter: " + str(counter))
            try:
                if WinningRule.ID not in WinningRules:
                    WinningRules[WinningRule.ID] = '<li>' + WinningRule.Origin + ' <li class="indent">' + MarkWinningTokens(strtokenlist, WinningRule, i)
                else:
                    WinningRules[WinningRule.ID] += ' <li class="indent">' + MarkWinningTokens(strtokenlist, WinningRule, i)
                ApplyWinningRule(strtokenlist, WinningRule, StartPosition=i)
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error in ApplyWinningRule.":
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


def DynamicPipeline(NodeList, schema):
    WinningRules = {}

    for action in PipeLine:
        if action == "segmentation":
            continue
        if action == "apply lexicons":
            continue

        if action == "SEGMENTATION COMPLETE" and schema == "segonly":
            break
        if action == "SHALLOW COMPLETE" and schema == "shallowcomplete":
            break

        if action.startswith("FSA"):
            Rulefile = action[3:].strip()
            WinningRules.update(MatchAndApplyRuleFile(NodeList, Rulefile))
            # if NodeList:
            #     logging.debug(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

        # if action.startswith("lookup"):
        #     lookupSourceName = action[6:].strip()
        #     for x in LexiconLookupSource:
        #         if x.name == lookupSourceName:
        #             Lexicon.LexiconLookup(NodeList, x)
        #
        # if action == "APPLY COMPOSITE KG":
        #     Lexicon.ApplyCompositeKG(NodeList)

        if action.startswith("Lookup defLex:") or action.startswith("Lookup External:") or action.startswith("Lookup oQcQ"):
            lookupSourceName = action[6:].strip()
            for x in LexiconLookupSource:
                if x.name == lookupSourceName:
                    Lexicon.LexiconLookup(NodeList, x)

        if action == "APPLY COMPOSITE KG":
            Lexicon.ApplyCompositeKG(NodeList)

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


def SeparateSentence(Sentence):
    PUNCSet = {"?", "!", ";", "...", ",", "。", "？", "！", "；", "，", "\t"}
    punclist = []
    i_prev = 0
    for i in range(len(Sentence)):
        if Sentence[i] in PUNCSet and (i_prev+5) < i < (len(Sentence) - 5):
            punclist.append(i)
            i_prev = i

    start = 0
    SubSentences = []
    for separator in punclist:
        SubSentences.append( Sentence[start:separator+1])
        start = separator+1
    if start < len(Sentence):
        SubSentences.append(Sentence[start:])

    #logging.info(str(SubSentences))
    return SubSentences


def LexicalAnalyzeTask( SubSentence, schema):

    NodeList = Tokenization.Tokenize(SubSentence)
    if not NodeList or NodeList.size == 0:
        return None, None

    Lexicon.ApplyLexiconToNodes(NodeList)
    # print("after ApplyLexiconToNodes" + OutputStringTokens_oneliner(NodeList))

    PrepareJSandJM(NodeList)
    #Lexicon.LexiconoQoCLookup(NodeList)

    WinningRules = DynamicPipeline(NodeList, schema)
        # t = Thread(target=Cache.WriteSentenceDB, args=(SubSentence, NodeList))
        # t.start()

    return NodeList, WinningRules


"""After testing, the _multithread version is not faster than normal one.
abandened. """
def LexicalAnalyze_multithread(Sentence, schema = "full"):
    try:
        logging.debug("-Start LexicalAnalyze: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)

        ResultNodeList = None
        ResultWinningRules = {}
        SubSentences = SeparateSentence(Sentence)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            Result = {}

            future_to_subsentence = {executor.submit(LexicalAnalyzeTask, SubSentence, schema): SubSentence for SubSentence in SubSentences}
            for future in concurrent.futures.as_completed(future_to_subsentence):
                (NodeList, WinningRules) = future.result()
                Result[future_to_subsentence[future]] = NodeList
                ResultWinningRules.update(WinningRules)
        #logging.warning("submitted into " + str(len(Result)) + " threads to process.")
        for SubSentence in SubSentences:
            NodeList = Result[SubSentence]
            # logging.info("before adding " + SubSentence + ", the nodelist is: " + str(ResultNodeList))
            # logging.info("\t the new nodes are: " + str(NodeList))
            if ResultNodeList:
                if not ResultNodeList.tail.text:
                    ResultNodeList.remove(ResultNodeList.tail)

                NodeList.remove(NodeList.head)
                ResultNodeList.appendnodelist(NodeList)
            else:
                ResultNodeList = NodeList
        logging.debug("-End LexicalAnalyze")

    except Exception as e:
        logging.error("Overall Error in LexicalAnalyze:")
        logging.error(e)
        logging.error(traceback.format_exc())
        return None, None

    return ResultNodeList, ResultWinningRules

def LexicalAnalyze(Sentence, schema = "full"):
    try:
        logging.debug("-Start LexicalAnalyze: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)
        if Sentence in Cache.SentenceCache:
            return Cache.SentenceCache[Sentence], None  # assume ResultWinningRules is none.

        ResultNodeList = None
        ResultWinningRules = {}
        for SubSentence in SeparateSentence(Sentence):

            NodeList, WinningRules = LexicalAnalyzeTask(SubSentence, schema)
            if ResultNodeList:
                if not ResultNodeList.tail.text:
                    ResultNodeList.remove(ResultNodeList.tail)
                if not NodeList.head.text:
                    NodeList.remove(NodeList.head)
                ResultNodeList.appendnodelist(NodeList)
            else:
                ResultNodeList = NodeList
            if WinningRules:
                ResultWinningRules.update(WinningRules)

        if schema == "full" and utils.runtype != "debug":
            if len(Cache.SentenceCache) < utils.maxcachesize:
                Cache.SentenceCache[Sentence] = ResultNodeList
                Cache.WriteSentenceDB(Sentence, ResultNodeList)
        # if ParserConfig.get("main", "runtype").lower() == "debug":
        #     t = Thread(target=Cache.WriteWinningRules_Async, args=(Sentence, ResultWinningRules))
        #     t.start()
            #Cache.WriteWinningRules(Sentence, ResultWinningRules)
        logging.debug("-End LexicalAnalyze")

    except Exception as e:
        logging.error("Overall Error in LexicalAnalyze:")
        logging.error(e)
        logging.error(traceback.format_exc())
        return None, None

    return ResultNodeList, ResultWinningRules


def LoadPipeline(PipelineLocation):
    if PipelineLocation.startswith("."):
        PipelineLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  PipelineLocation)
    with open(PipelineLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            action, _ = SeparateComment(line)
            if not action:
                continue
            PipeLine.append(action.strip())

def LoadCommonLexicon(XLocation):
    Lexicon.LoadCompositeKG(XLocation + 'LexX-CompositeKG.txt')

    Lexicon.LoadLexicon(XLocation + 'LexX.txt')
    Lexicon.LoadLexicon(XLocation + 'LexX-zidian.txt')
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

    Lexicon.LoadLexicon(XLocation + 'LexX-oQcQ.txt',    lookupSource=LexiconLookupSource.oQcQ)

    Lexicon.LoadSegmentLexicon()    #note: the locations are hard-coded
    Lexicon.LoadExtraReference(XLocation + 'CuobieziX.txt', Lexicon._LexiconCuobieziDict)
    Lexicon.LoadExtraReference(XLocation + 'Fanti.txt', Lexicon._LexiconFantiDict)

    Rules.LoadGlobalMacro(XLocation, 'GlobalMacro.txt')

def LoadCommon():

    InitDB()

    import Cache
    Cache.LoadSentenceDB()
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    XLocation = '../../fsa/X/'

    # LoadCommonLexicon(XLocation)

    LoadPipeline(XLocation + 'pipelineX.txt')

    logging.debug("Runtype:" + ParserConfig.get("main", "runtype"))
    logging.debug("utils.Runtype:" + utils.ParserConfig.get("main", "runtype"))
    Rules.LoadGlobalMacro(XLocation, 'GlobalMacro.txt')
    Lexicon.LoadCompositeKG(XLocation + 'LexX-CompositeKG.txt')

    for action in PipeLine:
        if action.startswith("FSA"):
            Rulefile = action[3:].strip()
            Rules.LoadRules(XLocation, Rulefile)

        if action.startswith("Lookup Lex:"):
            Lexfile = action[action.index(":")+1:].strip().split(",")
            for lex in Lexfile:
                lex = lex.strip()
                Lexicon.LoadLexicon(XLocation + lex)


        if action.startswith("Lookup defLex:"):
            Compoundfile = action[action.index(":")+1:].strip().split(",")
            for compound in Compoundfile:
                compound = compound.strip()
                Lexicon.LoadLexicon(XLocation + compound, lookupSource=LexiconLookupSource.defLex)

        if action.startswith("Lookup External:"):
            Externalfile = action[action.index(":")+1:].strip().split(",")
            for external in Externalfile:
                external = external.strip()
                Lexicon.LoadLexicon(XLocation + 'Q/lexicon/' + external,lookupSource=LexiconLookupSource.External)

        if action.startswith("Lookup oQcQ:"):
            oQoCfile = action[action.index(":")+1:].strip().split(",")
            for oQoC in oQoCfile:
                oQoC = oQoC.strip()
                Lexicon.LoadLexicon(XLocation + oQoC,lookupSource=LexiconLookupSource.oQcQ)

    Lexicon.LoadSegmentLexicon()
    Lexicon.LoadExtraReference(XLocation + 'CuobieziX.txt', Lexicon._LexiconCuobieziDict)
    Lexicon.LoadExtraReference(XLocation + 'Fanti.txt', Lexicon._LexiconFantiDict)

    CloseDB(utils.DBCon)
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

    target = "讲真客服是好的，服务也是好的"

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
