#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
#usage: to output feature list, run:
#       python Rules.py > features.txt

import logging, re, operator, sys, os, pickle, requests
from utils import *

url = "http://localhost:5001"
url_ch = "http://localhost:8080"

_FeatureSet = set()
_FeatureList = []   #this is populated from FeatureSet. to have featureID.
_FeatureDict = {}   #this is populated from FeatureSet. for better searching
_AliasDict = {}
_FeatureOntology = []


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
            self.ancestors = sorted(self.ancestors)
            for i in self.ancestors:
                output += GetFeatureName(i) +"; "
        if self.Comment:
            output += "\t" + self.Comment
        return output

    def SetRule(self, line):
        code, comment = SeparateComment(line)
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
            _FeatureOntology.append(realnode)

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
            for node in _FeatureOntology:
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
            code, __ = SeparateComment(line)
            features = [x.strip() for x in re.split("[,;=\s]", code) if x]

            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                _FeatureSet.add(feature)
    _FeatureList = list(sorted(_FeatureSet))
    _FeatureDict = {f:ID for ID,f in enumerate(sorted(_FeatureSet))}


def LoadFullFeatureList_Deprecate(featureListLocation):
    global _FeatureList, _FeatureDict
    _FeatureSet.clear()
    with open(featureListLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            feature, __ = SeparateComment(line)
            if len(feature) == 0:
                continue
            _FeatureSet.add(feature)
    _FeatureList = list(sorted(_FeatureSet))
    _FeatureDict = {f:ID for ID,f in enumerate(sorted(_FeatureSet))}


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
    for node in sorted(_FeatureOntology, key=operator.attrgetter('openWord')):
        if node.ancestors:
            output += str(node) + "\n"
    output += "//***Alias***" + "\n"
    for key in sorted(_AliasDict, key=lambda x:GetFeatureName(_AliasDict[x])):
        output += _FeatureList[_AliasDict[key]] + "=" + key  + "\n"
    return output


def LoadFeatureOntology(featureOncologyLocation):
    global _FeatureOntology
    # pickleLocation = "featureontology.pickle"
    # if os.path.isfile(pickleLocation):
    #     with open(pickleLocation, 'rb') as pk:
    #         _FeatureOntology = pickle.load(pk)
    #     return

    LoadFeatureSet(featureOncologyLocation)

    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetRule(line)
            if node.openWordID != -1:
                _FeatureOntology.append(node)

    # with open(pickleLocation, 'wb') as pk:
    #     pickle.dump(_FeatureOntology, pk)


SearchFeatureOntology_Cache = {}
def SearchFeatureOntology(featureID):    #Can be organized to use OpenWordID (featureID), for performance gain.
    #print("SearchFeatureOntology ID" + str(featureID))
    if featureID in SearchFeatureOntology_Cache:
        return SearchFeatureOntology_Cache[featureID]
    for node in _FeatureOntology:
        if node.openWordID == featureID:
            SearchFeatureOntology_Cache[featureID] = node
            return node
    return None


GetFeatureID_Cache = {}
def GetFeatureID(feature):
    # if _CreateFeatureList:
    #     _FeatureSet.add(feature)
    #     return 1

    if feature in GetFeatureID_Cache:
        return GetFeatureID_Cache[feature]

    if len(_FeatureList) == 0:
        try:
            GetFeatureIDURL = url + "/GetFeatureID/"
            ret = requests.get(GetFeatureIDURL + feature)
        except IOError:
            return -1
        GetFeatureID_Cache[feature] = int(ret.text)
        return int(ret.text)

    if re.search(u'[\u4e00-\u9fff]', feature):
        return -1   # Chinese is not a feature.
    if feature in _AliasDict:
        return _AliasDict[feature]
    if feature in _FeatureDict:
        return _FeatureDict[feature]

    #logging.info("Searching for " + feature + " but it is not in featurefulllist (feature.txt).")
    _MissingFeatureSet.add(feature)
    return -1    # -1? 0?


def GetFeatureName(featureID):

    if len(_FeatureList) == 0:
        GetFeatureNameURL = url + "/GetFeatureName/"
        try:
            ret = requests.get(GetFeatureNameURL + str(featureID))
            ret.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            return ""
        return ret.text

    if 0 <= featureID < len(_FeatureList):
        return _FeatureList[featureID]
    else:
        logging.warning("Wrong to get Feature Name: Searching for ID[" + str(featureID) + "] but it is not right. len(_FeatureList)=" + str(len(_FeatureList)))
        # raise(Exception("error"))
        return ""


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
        print(OutputFeatureOntology())
        #PrintFeatureSet()

    else:
        print("Usage: python FeatureOntology.py CreateFeatureList/CreateFeatureOntology > outputfile.txt")
        exit(0)

