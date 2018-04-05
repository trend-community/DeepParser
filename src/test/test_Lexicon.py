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

        LoadLexicon(dir_path + '/../../../fsa/X/LexX-ChinesePunctuate.txt')

        node = Tokenization.SentenceNode('：')
        ApplyLexicon(node)
        self.assertTrue(utils.FeatureID_SYM in node.features)
        self.assertFalse(utils.FeatureID_OOV in node.features)

        node = Tokenization.SentenceNode(':')
        ApplyLexicon(node)
        self.assertTrue(utils.FeatureID_SYM in node.features)
        self.assertFalse(utils.FeatureID_OOV in node.features)


    def test_LexiconLookup(self):
        LoadLexicon(dir_path + '/../../../fsa/X/defLexX.txt', lookupSource=LexiconLookupSource.defLex)
        LoadLexicon(dir_path + '/../../../fsa/X/defPlus.txt', lookupSource=LexiconLookupSource.defLex)

        Sentence="喝不惯"
        NodeList = Tokenization.Tokenize(Sentence)
        import ProcessSentence
        ProcessSentence.PrepareJSandJM(NodeList)
        LexiconLookup(NodeList, LexiconLookupSource.defLex)
        self.assertEqual(NodeList.size, 3)

        Sentence="李四"
        NodeList = Tokenization.Tokenize(Sentence)
        #import ProcessSentence
        ProcessSentence.PrepareJSandJM(NodeList)
        LexiconLookup(NodeList, LexiconLookupSource.defLex)
        self.assertEqual(NodeList.size, 3)
        self.assertFalse(utils.FeatureID_OOV in NodeList.head.features)

    def test_ApplyWordLengthFeature(self):
        Sentence="李四abc456,sab98中文"
        NodeList = Tokenization.Tokenize(Sentence)
        ApplyLexiconToNodes(NodeList)
        self.assertTrue(C1ID in NodeList.head.features)
        self.assertTrue(D1ID in NodeList.get(1).features)

