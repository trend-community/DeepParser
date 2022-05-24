#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
#usage: to output feature list, run:
#       python Rules.py > features.txt

import  sys, requests, operator
import logging, re, os
import utils
#from utils import *


#_FeatureSet = set()
#_FeatureList = []   #this is populated from FeatureSet. to have featureID.
#_FeatureDict = {}   #this is populated from FeatureSet. for better searching

_AliasDict = {}
_FeatureOntologyDict = {}
_AppendixLists = {}     # Group the NotCopyList, NotShowList, CoreGlobalList, Blocklists together
# NotCopyList = []
# NotShowList = []
# CoreGlobalList = []     # for Lexicon.AddDocumentTempLexicon()
BarTags=[   ['N', 'V', 'A', 'P', 'RB', 'DT', 'MD', 'UH', 'PRP', 'CD', 'RB', 'SC', 'CC', 'DT', 'SYM', 'Punc', 'EX'],
            ['NE', 'DE', 'NG', 'RP'],
            ['AP','VG'],
            ['NP'],
            ['PoP', 'PP'],
            ['VP'],
            #['Pred'],  06/18/2018 suspend 'Pred' for now, may return back later
            ['CL']   ]
BarTagIDs = []
BarTagIDSet = set()
MergeTokenList = ['+++', 'nnn', 'mn', 'N', 'NE', 'DE']
SentimentTags = ['repent', 'sent', 'fear', 'nC', 'cherish', 'apologize', 'mental', 'EMOc', 'EMO', 'emo', 'nEMOc', 'pEMOc', 'nEMO', 'pEMO', 'tuihuan', 'ntV', 'nt', 'bonus', 'pro', 'pt',
                    'pC', 'mianxi', 'mianyou', 'manjian', 'aspir', 'wish', 'solve', 'need', 'pWeather', 'nWeather', 'pt0', 'nt0', 'ntN0', 'ptN0',  'damage', 'conV', 'con', 'adversary',
                 'victim', 'con2', 'beBad', 'beGood', 'negAct', 'posAct', 'ntA', 'ptA', 'ntN', 'ptN', 'ptV', 'proV', 'conA', 'proA', 'conN', 'proN', 'curse', 'nEmo', 'emo', 'illBehave',
                'shameless', 'satisfied', 'sigh', 'weep', 'condole', 'mishap', 'guarantee', 'agree', 'disagree', 'pAttitude', 'emotion', 'laugh', 'joy', 'thank', 'welcome', 'entertain',
                'wellTreat', 'excited', 'nAttitude', 'calm', 'worry', 'unsatisfied', 'uneasy', 'sad', 'embarrassed', 'disappointed', 'ppEmo', 'nnEmo', 'interested', 'hello', 'salute', 'praise',
                'commemorate', 'congr', 'endorse', 'appreciate', 'accept', 'reward', 'illTreat', 'mock', 'protest', 'oppose', 'reject', 'refuse', 'betray', 'pEmo', 'blame', 'angry', 'suffer',
                'full', 'vWell', 'lucky', 'succeed', 'prosper', 'surpass', 'win', 'famous', 'good', 'bad', 'happy', 'annoy', 'hate', 'love', 'frighten', 'mkWorried', 'irritate', 'offend', 'tease',
                'please', 'soothe', 'enLive', 'surprise', 'shy','Pro', 'Con', 'PosEmo', 'NegEmo','PosType', 'NegType','transP','transN']
SentimentTagIDSet = set()
StemFeatureIDSet = set()        # this set is populated in Lexicon.LoadPrefixSuffix(), used in Lookup StemCompound

#_CreateFeatureList = False
_MissingFeatureSet = set()


class AutoincrementValue(dict):
    counter = 0
    def add(self, key):
        if key not in self:
            dict.__setitem__(self, key, self.counter)
            self.counter += 1
            return self.counter-1   #return the value.
        else:
            return self[key]

_FeatureDict = AutoincrementValue()
_FeatureIDDict = {} # reverse of _FeatureDict

class OntologyFeature:
    counter = 0
    def __init__(self, name):
        self.ID = self.counter
        self.counter += 1
        self.name = name

class OntologyNode:
    def __init__(self):
        self.openWord = ''
        self.Comment = ''
        self.openWordID = -1
        self.ancestors = set()

    def __str__(self):
        output = self.openWord
        if self.ancestors:
            output += ", "
            ancestors = sorted(self.ancestors)
            for i in ancestors:
                output += GetFeatureName(i) +"; "
        if self.Comment:
            output += "\t" + self.Comment
        return output

    def SetAncestors(self, line):
        code, comment = utils.SeparateComment(line)
        self.Comment = comment
        code = self.ProcessAliasInFeatureFile(code)
        if len(code) == 0:
            return

        features = [x.strip() for x in re.split("[,; ]", code) if x]
        openWord = features[0]
        openWordID = GetFeatureID(openWord)

        TryOldNode = SearchFeatureOntology(openWordID)
        if TryOldNode:
            if len(features) > 1:
                for feature in features[1:]:
                    TryOldNode.ancestors.add(GetFeatureID(feature))
        else:
            self.openWord = openWord
            self.openWordID = openWordID

            if len(features) > 1:
                for feature in features[1:]:
                    fid = GetFeatureID(feature)
                    self.ancestors.add(fid)
                    #self.ancestors = set(self.ancestors)

    # if there is alias (using = sign):
    #   1, add the alias (and the real feature id) into _AliasDict
    #   2, return the openword and features without alias.
    @staticmethod
    def ProcessAliasInFeatureFile( line):
        blocks = [x.strip() for x in re.split("=", line) if x]
        if len(blocks) <= 1:
            return line     # there is no "=" sign.
        #Now the last block has the alias name and code
        code = blocks[-1]
        realfeature = blocks[0]
        realfeatureId = GetFeatureID(realfeature)

        #featureID = GetFeatureID(realfeature)
        if realfeatureId == -1: #the feature in file is not in featureFullList
            logging.warning("The feature in file is not in feature list!" + realfeature + " in \n\t" + line)
            return code # ignore

        realnode = SearchFeatureOntology(realfeatureId)
        if not realnode:
            realnode = OntologyNode()
            realnode.openWord = realfeature
            realnode.openWordID = realfeatureId
            _FeatureOntologyDict[realnode.openWordID] = realnode

        features = [x.strip() for x in re.split("[,; ]", code) if x]    # the first feature is the last alias.
        lastalias = features[0]
        for alias in blocks[1:-1] + [lastalias]:
            aliasId = GetFeatureID(alias)
            if aliasId == realfeatureId:    # example: lookFor=lookFor,tryToKnow,ge
                #logging.debug("Feature {} has the same feature Id as the open word".format(alias))
                continue    # ignore, don't add as an alias.
            aliasnode = SearchFeatureOntology(aliasId)

            if aliasnode:
                realnode.ancestors.update(aliasnode.ancestors)
                aliasnode.ancestors.clear()
                if alias in _FeatureDict:
                    _FeatureDict.pop(alias)
                del _FeatureOntologyDict[aliasId]

            # find all feature ontology nodes that have alias as ancestor
            #   replace that using the realfeatureId
            for node in _FeatureOntologyDict.values():
                if aliasId in node.ancestors:
                    node.ancestors.remove(aliasId)
                    node.ancestors.add(realfeatureId)

            # for the existing alias that points to this alias, need to redirect to real id.
            for _aliasname, _aliasid in _AliasDict.items():
                if _aliasid == aliasId:
                    logging.debug("Changeing old alias {} -> {}, now -> {}".format(_aliasname, alias, realfeature))
                    _AliasDict[_aliasname] = realfeatureId

            _AliasDict[alias] = realfeatureId

        #Only return the features, not the alias.
        if len(features) > 1:
            return  ','.join([blocks[0]] + features[1:])
        else:
            return blocks[0]
        #return features code.replace(lastalias, realfeature )

#Used to extract features from feature.txt, to create full feature list.
def LoadFeatureSet(featureOncologyLocation):
    global _FeatureIDDict, _FeatureDict
    #_FeatureSet.clear()

    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            code, __ = utils.SeparateComment(line)
            features = [x.strip() for x in re.split("[,;=\s]", code) if x]

            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                _FeatureDict.add(feature)
    _FeatureIDDict =  {v: k for k, v in _FeatureDict.items()}


def OutputFeatureSet():
    output = "// ***Feature Set***" + "\n"
    for feature in sorted(_FeatureDict):
        output += feature
    output += "// ***Alias***" + "\n"
    for key in sorted(_AliasDict):
        output += key  + "\n"
    return output

def OutputMissingFeatureSet():
    output = ""
    if _MissingFeatureSet:
        output ="//  ***Features that are not included in FullFeatureList***" + "\n"
        for feature in sorted(_MissingFeatureSet):
            output += feature + "\n"
    return output

def OutputFeatureOntology():
    output = "//***Ontology***" + "\n"
    for OpenWordID in sorted(_FeatureOntologyDict, key=lambda x:_FeatureOntologyDict[x].openWord):
        if _FeatureOntologyDict[OpenWordID].ancestors:
            output += str(_FeatureOntologyDict[OpenWordID]) + "\n"
    output += "//***Ontology* * single nodes**" + "\n"
    for OpenWordID in sorted(_FeatureOntologyDict, key=lambda x:_FeatureOntologyDict[x].openWord):
        if not _FeatureOntologyDict[OpenWordID].ancestors:
            output += str(_FeatureOntologyDict[OpenWordID]) + "\n"
    output += "//***Alias***" + "\n"
    for key in sorted(_AliasDict, key=lambda x:GetFeatureName(_AliasDict[x])):
        output += _FeatureIDDict[_AliasDict[key]] + "=" + key  + "\n"
    return output

def OutputFeatureOntologyFile(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FolderLocation)
    FileLocation = os.path.join(FolderLocation, "featureontology.txt")

    with open(FileLocation, "w", encoding="utf-8") as writer:
        writer.write(OutputFeatureOntology())


def  LoadOntologyFile(filelocation, outbound, inbound, nodeset, graph):
    with open(filelocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            code, comment = utils.SeparateComment(line)
            if "," not in code:
                continue  # no edge. ignore

            OpenWord, ancestors = code.split(",", 1)
            OpenWordID = GetFeatureID(OpenWord.split("=", 1)[0].strip())  # remove the alias.
            if OpenWordID == -1:
                logging.warning("OutputFeatureOntologyGraph: wrong word ID for line {}.".format(line))
                logging.warning("   The OpenWord is {} and the word that is trying to get featureID is {}".format(OpenWord,
                                 OpenWord.split( "=", 1)[0].strip()))
                continue
            firstpath = True    #first is the "real path"
            for path in ancestors.split(";"):
                prev = OpenWordID
                for node in path.split(","):
                    if node.strip():
                        parentid = GetFeatureID(node.strip())
                        if parentid == -1:
                            logging.warning("OutputFeatureOntologyGraph: wrong parentid for node {}".format(node))
                            continue
                        if (prev, parentid) not in graph:
                            graph[(prev, parentid)] = firstpath
                            outbound[prev] += 1
                            inbound[parentid] += 1
                            nodeset.add(prev)
                            nodeset.add(parentid)
                        else:
                            graph[(prev, parentid)] = graph[(prev, parentid)] or firstpath

                        prev = GetFeatureID(node.strip())
                firstpath = False

# reload the file, because previous the ontology was loaded without disctinction of ";" and ",".
def OutputFeatureOntologyGraph():
    #output = "//***Ontology***" + "\n"
    if not hasattr(OutputFeatureOntologyGraph, "graph"):
        from collections import defaultdict
        OutputFeatureOntologyGraph.outbound = defaultdict(int)
        OutputFeatureOntologyGraph.inbound = defaultdict(int)
        OutputFeatureOntologyGraph.nodeset = set()

        OutputFeatureOntologyGraph.graph = {}
        PipeLineLocation = utils.ParserConfig.get("main", "Pipelinefile")
        XLocation, _ = os.path.split(PipeLineLocation)

        LoadOntologyFile(os.path.join(XLocation, '../ontology/feature.txt'), OutputFeatureOntologyGraph.outbound, OutputFeatureOntologyGraph.inbound,
                         OutputFeatureOntologyGraph.nodeset, OutputFeatureOntologyGraph.graph)
        logging.info("After loading from common ontology, there are {} edges, for {} nodes.".format(len(OutputFeatureOntologyGraph.graph), len(OutputFeatureOntologyGraph.nodeset)))

        LoadOntologyFile(os.path.join(XLocation, 'feature.txt'), OutputFeatureOntologyGraph.outbound, OutputFeatureOntologyGraph.inbound,
                         OutputFeatureOntologyGraph.nodeset, OutputFeatureOntologyGraph.graph)
        logging.info("After loading from local ontology, there are {} edges, for {} nodes.".format(len(OutputFeatureOntologyGraph.graph),
                                                                            len(OutputFeatureOntologyGraph.nodeset)))

    RemoveAbundantEdge(OutputFeatureOntologyGraph.graph)
    logging.info("After RemoveAbundantEdge, there are {} edges, for {} nodes.".format(
        len(OutputFeatureOntologyGraph.graph),
        len(OutputFeatureOntologyGraph.nodeset)))

    output = "digraph {\n"
    for node in sorted(OutputFeatureOntologyGraph.nodeset):
        output += "d{} [label=\"{}\" tooltip=\"Inbound:{} Outbound:{} \" ];\n".format(node, GetFeatureName(node), OutputFeatureOntologyGraph.inbound[node], OutputFeatureOntologyGraph.outbound[node])
    for edge in sorted(OutputFeatureOntologyGraph.graph, key=operator.itemgetter(0, 1)):
        #output += GetFeatureName(edge[0]) + "->" + GetFeatureName(edge[1]) + "\n"
        output += "\td{}->d{} {};\n".format(edge[0], edge[1], "[color=blue]" if OutputFeatureOntologyGraph.graph[edge] else "")
    output += "}\n"

    logging.debug("OutputFeatureOntologyGraph() done!")
    return output


def RemoveAbundantEdge(graph):
    """
    If a parent is already in grandparent/great-grandparent list, then remove this son-parent link.
    :param graph:
    :return:
    """
    for (sonid, parentid) in sorted(graph, key=operator.itemgetter(0, 1)):
        if sonid in _FeatureOntologyDict:
            for ancestor in _FeatureOntologyDict[sonid].ancestors:
                if ancestor in _FeatureOntologyDict and parentid in _FeatureOntologyDict[ancestor].ancestors:
                    del graph[(sonid, parentid)]
                    break   # only break the loop of ancestor.


def LoadFeatureOntology(localfeatureOncologyLocation):
    global _FeatureIDDict, _FeatureDict
    if localfeatureOncologyLocation.startswith("."):
        localfeatureOncologyLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  localfeatureOncologyLocation)

    Folder = os.path.dirname(localfeatureOncologyLocation)
    commonfeatureOncologyLocation = os.path.join(Folder, "../ontology/feature.txt")

    LoadFeatureSet(commonfeatureOncologyLocation) #get feature id for each feature first.
    with open(commonfeatureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetAncestors(line)
            if node.openWordID != -1:
                _FeatureOntologyDict[node.openWordID] = node
    for f in _AliasDict:
        if f in _FeatureDict:
            if _FeatureDict[f] in _FeatureOntologyDict:
                logging.warning("   Alias {}  _FeatureDict[f] in _FeatureOntologyDict ".format(f))
            _FeatureDict.pop(f)

    LoadFeatureSet(localfeatureOncologyLocation) #get feature id for each feature first.
    with open(localfeatureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetAncestors(line)
            if node.openWordID != -1:
                _FeatureOntologyDict[node.openWordID] = node
    for f in _AliasDict:
        if f in _FeatureDict:
            if _FeatureDict[f] in _FeatureOntologyDict:
                logging.warning("   Alias {}  _FeatureDict[f] in _FeatureOntologyDict ".format(f))
            _FeatureDict.pop(f)

    LoadAppendixList(localfeatureOncologyLocation)
    utils.InitGlobalFeatureID()
    utils.initiated = True  # the featureID, featureName are set.


def CreateTempFeature(middlename):
    FeatureName = "Temp{}_{}".format(middlename, _FeatureDict.counter)
    _FeatureDict.add(FeatureName)

    FeatureID = _FeatureDict[FeatureName]
    _FeatureIDDict[FeatureID] = FeatureName

    return FeatureName, FeatureID


def LoadAppendixList(featureOncologyLocation):
    Folder = os.path.dirname(featureOncologyLocation)
    NoShowFileLocation = os.path.join(Folder, "../ontology/featureNotShow.txt")
    with open(NoShowFileLocation, encoding="utf-8") as dictionary:
        _AppendixLists['NotShowList'] = set()
        for line in dictionary:
            word, _ = utils.SeparateComment(line)
            if not word:
                continue
            _AppendixLists['NotShowList'].add(GetFeatureID(word))

    NoCopyFileLocation = os.path.join(Folder, "../ontology/featureNotCopy.Parser.txt")
    with open(NoCopyFileLocation, encoding="utf-8") as dictionary:
        _AppendixLists['NotCopyList'] = set()
        for line in dictionary:
            word, _ = utils.SeparateComment(line)
            if not word:
                continue
            _AppendixLists['NotCopyList'].add(GetFeatureID(word))


    CoreGlobalFileLocation = os.path.join(Folder, "featureCoreGlobal.txt")
    with open(CoreGlobalFileLocation, encoding="utf-8") as dictionary:
        _AppendixLists['CoreGlobalList'] = set()
        for line in dictionary:
            word, _ = utils.SeparateComment(line)
            if not word:
                continue
            _AppendixLists['CoreGlobalList'].add(GetFeatureID(word))

    for f in ['a', 'n', 'v']:
        BlockFileLocation = os.path.join(Folder, "../ontology/" + f + "Blocklist.txt")
        with open(BlockFileLocation, encoding="utf-8") as dictionary:
            _AppendixLists[f+'Blocklist'] = set()
            for line in dictionary:
                word, _ = utils.SeparateComment(line)
                if not word:
                    continue
                _AppendixLists[f+'Blocklist'].add(GetFeatureID(word))


def SearchFeatureOntology(featureID):
    #print("SearchFeatureOntology ID" + str(featureID))
    if featureID in _FeatureOntologyDict:
        return _FeatureOntologyDict[featureID]
    return None


def ApplyFeature(oneset, featureID):
    if featureID == utils.FeatureID_NEW:
        oneset.clear()  # removed all existing feature if there is "NEW"
        return
    
    oneset.add(featureID)
    ontologynode = SearchFeatureOntology(featureID)
    if ontologynode:
        if ontologynode.ancestors:
            oneset.update(ontologynode.ancestors)


GetFeatureID_Cache = {}
def GetFeatureID(feature):
    if feature in GetFeatureID_Cache:
        return GetFeatureID_Cache[feature]

    if not _FeatureIDDict:    #for some clients that the _FeatureList is not load locally.
        try:
            GetFeatureIDURL = utils.ParserConfig.get("client", "url_larestfulservice") + "/GetFeatureID/"
            ret = requests.get(GetFeatureIDURL + feature)
        except IOError:
            return -1
        return int(ret.text)

    if feature in _AliasDict:
        if utils.initiated:
            GetFeatureID_Cache[feature] = _AliasDict[feature]
        return _AliasDict[feature]

    if feature in _FeatureDict:
        if utils.initiated:
            GetFeatureID_Cache[feature] = _FeatureDict[feature]
        return _FeatureDict[feature]

    if utils.ChinesePattern.fullmatch(feature):
        if utils.initiated:
            GetFeatureID_Cache[feature] = -1
        return -1   # Chinese is not a feature.

    logging.warning("GetFeatureID: Searching for " + feature + " but it is not in featurefulllist (feature.txt).")
    _MissingFeatureSet.add(feature)
    if utils.initiated:
        GetFeatureID_Cache[feature] = -1
    return -1    # -1? 0?


GetFeatureName_Cache = {}
def GetFeatureName(featureID):
    if featureID in GetFeatureName_Cache:
        return GetFeatureName_Cache[featureID]

    if len(_FeatureIDDict) == 0:
        logging.warning("GettingFeatureName using URL")
        GetFeatureNameURL = utils.ParserConfig.get("client", "url_larestfulservice") + "/GetFeatureName/"
        try:
            ret = requests.get(GetFeatureNameURL + str(featureID))
            ret.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            logging.error("Link = " + GetFeatureNameURL)
            return ""
        return ret.text

    if featureID in _FeatureIDDict:
        if utils.initiated:
            GetFeatureName_Cache[featureID] = _FeatureIDDict[featureID]
        return _FeatureIDDict[featureID]
    else:
        if utils.initiated:
            GetFeatureName_Cache[featureID] = ""
        logging.warning("GetFeatureName: Wrong to get Feature Name: Searching for ID[" + str(featureID) + "] but it is not right. len(_FeatureIDDict)=" + str(len(_FeatureIDDict)))
        # raise(Exception("error"))
        return ""


# For all bar tags in the list, keep only the last one.
def ProcessBarTags(featureset):
    MaxBarTagLevel = -1
    for f in featureset:
        if f not in BarTagIDSet:
            continue
        taglevel = utils.IndexXIn2DArray(f, BarTagIDs)
        if taglevel > -1:
            if MaxBarTagLevel < taglevel:
                MaxBarTagLevel = taglevel

    featureset_copy = featureset.copy()
    if MaxBarTagLevel > -1:
        for f in featureset_copy:
            taglevel = utils.IndexXIn2DArray(f, BarTagIDs)
            if taglevel > -1:
                if taglevel != MaxBarTagLevel:
                    featureset.remove(f)


def ProcessSentimentTags(featureset):
    featureset_copy = featureset.copy()
    for f in featureset_copy:
        if f not in SentimentTagIDSet:
            continue
        else:
            featureset.remove(f)


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    if len(sys.argv) != 2:
        print("Usage: python FeatureOntology.py CreateFeatureList/CreateFeatureOntology > outputfile.txt")
        exit(0)
    command = sys.argv[1]

    if command == "CreateFeatureList":
        #_CreateFeatureList = True
        LoadFeatureSet(dir_path + '/../../fsa/Y/feature.txt')
        print(OutputFeatureSet())

    elif command == "CreateFeatureOntology":
        #LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        #_CreateFeatureList = True
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        #print(OutputFeatureOntology())
        OutputFeatureOntologyFile('../temp')
        print(OutputFeatureOntologyGraph())

    else:
        print("Usage: python FeatureOntology.py CreateFeatureList/CreateFeatureOntology > outputfile.txt")
        exit(0)


