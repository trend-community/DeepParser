#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
import logging, re, operator


FeatureSet = set()
FeatureList = []
FeatureDict = {}
AliasDict = {}
FeatureOntology = []


def RemoveComment(line):
    blocks = re.split("//", line)  # remove comment.
    return blocks[0].strip()


class OntologyRule:
    def __init__(self):
        self.openWord = ''
        self.openWordID = 0
        self.ancestors = set()

    def __str__(self):
        output = "[" + self.openWord + "]: "
        for i in self.ancestors:
            output += FeatureList[i] +"; "
        return output

    def SetRule(self, line):
        code = RemoveComment(line)
        code = self.ProcessAlias(code)
        code = code.strip()
        if len(code) == 0:
            return
        features = re.split(",|;| ", code)
        self.openWord = features[0].strip()
        feature = features[0].strip()
        if feature not in FeatureDict:
            logging.error("Feature[" + feature + "] in file is not in FeatureDict!")
            return  # ignore.
        self.openWordID = FeatureDict[feature]
        if len(features) > 1:
            for feature in features[1:]:
                feature = feature.strip()
                if feature not in FeatureDict:
                    logging.error("Feature[" + feature + "] in file is not in FeatureDict!")
                else:
                    self.ancestors.add(FeatureDict[feature])


    @staticmethod
    def ProcessAlias( line):
        blocks = re.split("=", line)
        if len(blocks) <= 1:
            return line     # there is no "=" sign.
        #Now the last block has the real feature name and code
        code = blocks[-1].strip()
        features = re.split(",|;| ", code)    # the first feature is the real one.
        feature = features[0].strip()
        if feature not in FeatureDict:
            logging.error("Feature[" + feature + "] in file is not in FeatureDict (ProcessAlias)!")
            # FeatureList.append([feature])
            # FeatureSet.add({feature, len(FeatureList)})
            return code # ignore.

        featureID = FeatureDict[feature]
        for alias in blocks[:-1]:
            AliasDict[alias.strip()] = featureID

        return code


def LoadFeatureSet(dictionaryLocation):
    with open(dictionaryLocation) as dictionary:
        for line in dictionary:
            blocks = re.split(":", RemoveComment(line))
            if len(blocks) <= 1:
                continue            # there is no ":" sign
            featurestring = blocks[-1].strip()   # the last block has features
            features = featurestring.split(" ")
            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                FeatureSet.add(feature)


def LoadFullFeatureList(featureListLocation):
    global FeatureList, FeatureDict
    FeatureSet.clear()
    with open(featureListLocation) as dictionary:
        for line in dictionary:
            feature = RemoveComment(line)
            if len(feature) == 0:
                continue
            FeatureSet.add(feature)
    FeatureList = list(sorted(FeatureSet))
    FeatureDict = {f:i for i,f in enumerate(sorted(FeatureSet))}


def PrintFeatureSet():
    for feature in sorted(FeatureSet):
        print( feature )

def PrintFeatureOntology():
    for node in sorted(FeatureOntology, key=operator.attrgetter('openWord')):
        print node

def LoadFeatureOntology(featureOncologyLocation):
    global FeatureOntology
    FeatureSet.clear()
    with open(featureOncologyLocation) as dictionary:
        for line in dictionary:
            node = OntologyRule()
            node.SetRule(line)
            if node.openWord <> '':
                FeatureOntology.append(node)


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    # LoadFeatureSet('../../fsa/Y/lexY.txt')
    # LoadFeatureSet('../../fsa/X/lexX.txt')
    LoadFullFeatureList('../doc/lexicon/featurelist.txt')
    PrintFeatureSet()

    LoadFeatureOntology('../doc/featureOntology.txt')
    PrintFeatureOntology()
