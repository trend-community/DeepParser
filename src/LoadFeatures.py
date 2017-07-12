#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
import logging, re, operator


FeatureSet = set()
FeatureList = []
FeatureDict = {}
AliasDict = {}
FeatureOntology = []


def SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0].strip(), " ".join(blocks[1:])


class OntologyRule:
    def __init__(self):
        self.openWord = ''
        self.Comment = ''
        self.openWordID = 0
        self.ancestors = set()

    def __str__(self):
        output = "[" + self.openWord + "]"
        if self.ancestors:
            output += ": "
            for i in self.ancestors:
                output += FeatureList[i] +"; "
        if self.Comment:
            output += "\t//" + self.Comment
        return output

    def SetRule(self, line):
        code, comment = SeparateComment(line)
        self.Comment = comment
        code = self.ProcessAlias(code)
        if len(code) == 0:
            return

        features = [x.strip() for x in re.split(",|;| ", code) if x]
        self.openWord = features[0]
        feature = features[0]
        if feature not in FeatureDict:
            logging.error("Feature[" + feature + "] in file is not in FeatureDict!")
            return  # ignore.
        self.openWordID = FeatureDict[feature]
        if len(features) > 1:
            for feature in features[1:]:
                if feature not in FeatureDict:
                    logging.error("Feature[" + feature + "] in file is not in FeatureDict!")
                else:
                    self.ancestors.add(FeatureDict[feature])


    @staticmethod
    def ProcessAlias( line):
        blocks = [x.strip() for x in re.split("=", line) if x]
        if len(blocks) <= 1:
            return line     # there is no "=" sign.
        #Now the last block has the real feature name and code
        code = blocks[-1]
        features = re.split(",|;| ", code)    # the first feature is the real one.
        feature = features[0]
        if feature not in FeatureDict:
            logging.error("Feature[" + feature + "] in file is not in FeatureDict (ProcessAlias)!")
            # FeatureList.append([feature])
            # FeatureSet.add({feature, len(FeatureList)})
            return code # ignore.

        featureID = FeatureDict[feature]
        for alias in blocks[:-1]:
            AliasDict[alias] = featureID

        return code


def LoadFeatureSet(dictionaryLocation):
    with open(dictionaryLocation) as dictionary:
        for line in dictionary:
            blocks = [x.strip() for x, __ in re.split(":", SeparateComment(line)) if x]
            if len(blocks) <= 1:
                continue            # there is no ":" sign
            featurestring = blocks[-1]   # the last block has features
            features = featurestring.split()    #separate by space
            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                FeatureSet.add(feature)


def LoadFullFeatureList(featureListLocation):
    global FeatureList, FeatureDict
    FeatureSet.clear()
    with open(featureListLocation) as dictionary:
        for line in dictionary:
            feature, __ = SeparateComment(line)
            if len(feature) == 0:
                continue
            FeatureSet.add(feature)
    FeatureList = list(sorted(FeatureSet))
    FeatureDict = {f:i for i,f in enumerate(sorted(FeatureSet))}


def PrintFeatureSet():
    for feature in sorted(FeatureSet):
        print( feature )

def PrintFeatureOntology():
    print "\n\n***Ontology***"
    for node in sorted(FeatureOntology, key=operator.attrgetter('openWord')):
        print node
    print "\n\n***Alias***"
    for key in sorted(AliasDict):
        print "[" + key + "]:" + FeatureList[AliasDict[key]]

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
    #PrintFeatureSet()
    LoadFullFeatureList('../doc/lexicon/featurelist.txt')

    LoadFeatureOntology('../doc/featureOntology.txt')
    PrintFeatureOntology()
