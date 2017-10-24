import unittest
import Tokenization
from Lexicon import *

dir_path = os.path.dirname(os.path.realpath(__file__))
LoadFeatureOntology(dir_path + '/../../../fsa/Y/feature.txt')
LoadLexicon(dir_path + '/../../../fsa/Y/lexY.txt')
LoadLexicon(dir_path + '/../../../fsa/Y/compoundY.txt')

class LexiconTest(unittest.TestCase):
    def test_lexicon(self):
        FoundSent = False
        print("i-myself")
        s = SearchLexicon("i_myself")
        if s:
            print(s.features)

        for f in s.features:
            feature = GetFeatureName(f)
            print (feature)
            if feature == "sent":
                print("Found sent!")
                FoundSent = True
        self.assertTrue(FoundSent)

        s = SearchLexicon("BS")
        if s:
            print(s.features)

        print("like")
        s = SearchLexicon("like")
        if s:
            print(s.features)

        for f in s.features:
            feature = GetFeatureName(f)
            print (feature)
            if feature == "Ved":
                print("Found Ved!")
                FoundSent = True
        self.assertTrue(FoundSent)

    def test_ApplyLexicon(self):
        node = Tokenization.SentenceNode('0')
        ApplyLexicon(node)
        CDFeatureID = GetFeatureID('CD')
        self.assertTrue(CDFeatureID in node.features)