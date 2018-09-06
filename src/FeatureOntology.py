#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
#usage: to output feature list, run:
#       python Rules.py > features.txt

import  sys, requests, operator
import logging, re, os
import utils
#from utils import *


_FeatureSet = set()
_FeatureList = []   #this is populated from FeatureSet. to have featureID.
_FeatureDict = {}   #this is populated from FeatureSet. for better searching
_AliasDict = {}
_FeatureOntologyDict = {}
NotCopyList = []
NotShowList = []
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
#_CreateFeatureList = False
_MissingFeatureSet = set()


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
            aliasnode = SearchFeatureOntology(GetFeatureID(alias))
            aliasId = GetFeatureID(alias)
            if aliasnode:
                realnode.ancestors.update(aliasnode.ancestors)
                aliasnode.ancestors.clear()
                if alias in _FeatureSet:
                    _FeatureSet.remove(alias)

            # find all feature ontology nodes that have alias as ancestor
            #   replace that using the realfeatureId
            for node in _FeatureOntologyDict.values():
                if aliasId in node.ancestors:
                    node.ancestors.remove(aliasId)
                    node.ancestors.add(realfeatureId)

            _AliasDict[alias] = realfeatureId

        #Only return the features, not the alias.
        if len(features) > 1:
            return  ','.join([blocks[0]] + features[1:])
        else:
            return blocks[0]
        #return features code.replace(lastalias, realfeature )

#Used to extract features from feature.txt, to create full feature list.
def LoadFeatureSet(featureOncologyLocation):
    global _FeatureList, _FeatureDict, _FeatureSet
    _FeatureSet.clear()

    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            code, __ = utils.SeparateComment(line)
            features = [x.strip() for x in re.split("[,;=\s]", code) if x]

            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                _FeatureSet.add(feature)
    _FeatureList = list(sorted(_FeatureSet))
    _FeatureDict = {f: ID for ID, f in enumerate(_FeatureList)}


def OutputFeatureSet():
    output = "// ***Feature Set***" + "\n"
    for feature in sorted(_FeatureSet):
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
    for OpenWord in sorted(_FeatureOntologyDict.keys()):
        if _FeatureOntologyDict[OpenWord].ancestors:
            output += str(_FeatureOntologyDict[OpenWord]) + "\n"
    output += "//***Ontology* * single nodes**" + "\n"
    for OpenWord in sorted(_FeatureOntologyDict.keys()):
        if not _FeatureOntologyDict[OpenWord].ancestors:
            output += str(_FeatureOntologyDict[OpenWord]) + "\n"
    output += "//***Alias***" + "\n"
    for key in sorted(_AliasDict, key=lambda x:GetFeatureName(_AliasDict[x])):
        output += _FeatureList[_AliasDict[key]] + "=" + key  + "\n"
    return output

def OutputFeatureOntologyFile(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FolderLocation)
    FileLocation = os.path.join(FolderLocation, "featureontology.txt")

    with open(FileLocation, "w", encoding="utf-8") as writer:
        writer.write(OutputFeatureOntology())

def OutputFeatureOntologyGraph():
    #output = "//***Ontology***" + "\n"
    if not hasattr(OutputFeatureOntologyGraph, "graph"):
        from collections import defaultdict
        OutputFeatureOntologyGraph.outbound = defaultdict(int)
        OutputFeatureOntologyGraph.inbound = defaultdict(int)
        OutputFeatureOntologyGraph.nodeset = set()

        OutputFeatureOntologyGraph.graph = set()
        PipeLineLocation = utils.ParserConfig.get("main", "Pipelinefile")
        XLocation = os.path.dirname(PipeLineLocation)
        with open(XLocation + '/../Y/feature.txt', encoding="utf-8") as dictionary:
            for line in dictionary:
                code, comment = utils.SeparateComment(line)
                if "," not in code:
                    continue    #no edge. ignore

                OpenWord, ancestors = code.split(",", 1)
                OpenWordID = GetFeatureID(OpenWord.split("=", 1)[0].strip())  #remove the alias.
                if OpenWordID == -1:
                    logging.warning("OutputFeatureOntologyGraph: wrong word ID for line {}.".format(code))
                    continue
                for path in ancestors.split(";"):
                    prev = OpenWordID
                    for node in path.split(","):
                        if node.strip():
                            parentid = GetFeatureID(node.strip())
                            if parentid == -1:
                                logging.warning("OutputFeatureOntologyGraph: wrong parentid for node {}".format(node))
                                continue
                            if (prev, parentid) not in OutputFeatureOntologyGraph.graph:
                                OutputFeatureOntologyGraph.graph.add((prev, parentid))
                                OutputFeatureOntologyGraph.outbound[prev] += 1
                                OutputFeatureOntologyGraph.inbound[parentid] += 1
                                OutputFeatureOntologyGraph.nodeset.add(prev)
                                OutputFeatureOntologyGraph.nodeset.add(parentid)

                            prev = GetFeatureID(node.strip())

    output = "{\n"
    for node in sorted(OutputFeatureOntologyGraph.nodeset):
        output += "{} [label=\"{}\" tooltip=\"Inbound:{} Outbound:{} \" ];\n".format(node, GetFeatureName(node), OutputFeatureOntologyGraph.inbound[node], OutputFeatureOntologyGraph.outbound[node])
    for edge in sorted(OutputFeatureOntologyGraph.graph, key=operator.itemgetter(0, 1)):
        #output += GetFeatureName(edge[0]) + "->" + GetFeatureName(edge[1]) + "\n"
        output += "\t{}->{} ;\n".format(edge[0], edge[1])
    output += "}\n"

    logging.info("In Feature ontology, There are {} edges, for {} nodes.".format(len(OutputFeatureOntologyGraph.graph), len(OutputFeatureOntologyGraph.nodeset)))
    return output

def LoadFeatureOntology(featureOncologyLocation):
    if featureOncologyLocation.startswith("."):
        featureOncologyLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  featureOncologyLocation)

    LoadFeatureSet(featureOncologyLocation) #get feature id for each feature first.
    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetAncestors(line)
            if node.openWordID != -1:
                _FeatureOntologyDict[node.openWordID] = node

    LoadAppendixList(featureOncologyLocation)
    utils.InitGlobalFeatureID()


def LoadAppendixList(featureOncologyLocation):
    Folder = os.path.dirname(featureOncologyLocation)
    NoShowFileLocation = os.path.join(Folder, "featureNotShow.txt")
    with open(NoShowFileLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            word, _ = utils.SeparateComment(line)
            if not word:
                continue
            NotShowList.append(GetFeatureID(word))

    NoCopyFileLocation = os.path.join(Folder, "featureNotCopy.Parser.txt")
    with open(NoCopyFileLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            word, _ = utils.SeparateComment(line)
            if not word:
                continue
            NotCopyList.append(GetFeatureID(word))


def SearchFeatureOntology(featureID):
    #print("SearchFeatureOntology ID" + str(featureID))
    if featureID in _FeatureOntologyDict:
        return _FeatureOntologyDict[featureID]
    return None


def GetFeatureID(feature):
    if not _FeatureList:    #for some clients that the _FeatureList is not load locally.
        try:
            GetFeatureIDURL = utils.ParserConfig.get("client", "url_larestfulservice") + "/GetFeatureID/"
            ret = requests.get(GetFeatureIDURL + feature)
        except IOError:
            return -1
        return int(ret.text)

    if feature in _AliasDict:
        return _AliasDict[feature]
    if feature in _FeatureDict:
        return _FeatureDict[feature]

    if utils.ChinesePattern.search(feature):
        return -1   # Chinese is not a feature.

    logging.warning("GetFeatureID: Searching for " + feature + " but it is not in featurefulllist (feature.txt).")
    _MissingFeatureSet.add(feature)
    return -1    # -1? 0?


def GetFeatureName(featureID):
    if len(_FeatureList) == 0:
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

    if 0 <= featureID < len(_FeatureList):
        return _FeatureList[featureID]
    else:
        logging.warning("GetFeatureName: Wrong to get Feature Name: Searching for ID[" + str(featureID) + "] but it is not right. len(_FeatureList)=" + str(len(_FeatureList)))
        # raise(Exception("error"))
        return ""


# For all bar tags in the list, keep only the last one.
def ProcessBarTags(featureset):
    MaxBarTagLevel = -1
    for f in featureset:
        if f not in BarTagIDSet:
            continue
        taglevel, _ = utils.IndexIn2DArray(f, BarTagIDs)
        if taglevel > -1:
            if MaxBarTagLevel < taglevel:
                MaxBarTagLevel = taglevel

    featureset_copy = featureset.copy()
    if MaxBarTagLevel > -1:
        for f in featureset_copy:
            taglevel, _ = utils.IndexIn2DArray(f, BarTagIDs)
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


