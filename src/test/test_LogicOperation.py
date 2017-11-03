import unittest, os
from LogicOperation import *
import Tokenization


class FeatureTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FeatureTest, self).__init__(*args, **kwargs)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')


    def test_simple(self):
        """exact match"""
        node =  Tokenization.SentenceNode('')
        node.features.add(FeatureOntology.GetFeatureID('NN'))
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NN", None, 0))
    def test_And(self):
        node =  Tokenization.SentenceNode("abc")
        node.features.add(FeatureOntology.GetFeatureID('NN'))
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "NN percent", None, 0))

        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NN percent", None, 0))
    def test_Or(self):
        node = Tokenization.SentenceNode('')
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NN|percent", None, 0))
        node.features.add(FeatureOntology.GetFeatureID('percent'))

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NP|percent", None, 0))
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "NP", None, 0))

    def test_NotOr(self):
        node = Tokenization.SentenceNode('')
        node.features.add(FeatureOntology.GetFeatureID('NN'))
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!NN|percent", None, 0))

        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!NN|percent", None, 0))
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "!NP", None, 0))


class RuleTest(unittest.TestCase):
    def test_LogitExact(self):
        """Exact match"""
        node = Tokenization.SentenceNode('being')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "being", None, 0))

    def test_LogicOr(self):
        """Logic Or"""
        node = Tokenization.SentenceNode('being')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "being|getting", None, 0))

    def test_LogicAnd(self):
        """Logic And"""
        node =  Tokenization.SentenceNode("c")
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c d", None, 0))
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "c c", None, 0))

    def test_LogicAndOr(self):
        """Logic And/Or"""
        node =  Tokenization.SentenceNode('d')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d c", None, 0))
        node.word = "c"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "c|d c", None, 0))

        #self.assertTrue(LogicMatch())

    def test_LogicNotOr(self):
        """Logic And/Or"""
        node =  Tokenization.SentenceNode('d')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!c|d|e", None, 0))
        node.word = "f"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "!c|d|e", None, 0))
        node.word = "e"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "!c d|e", None, 0))
        node.word = "f"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!c d|e", None, 0))
        node.word = "c"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "c|d !d|e", None, 0))
        node.word = "d"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d !d|e", None, 0))
        node.word = "e"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|e !d|f|g|e", None, 0))
        node.word = "e"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d !d|c", None, 0))
        node.word = "f"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d !d|e", None, 0))


    def test_LogicCombined(self):
        """Logic Combined"""

        blocks = SeparateOrBlocks("a|b|c")
        self.assertEqual(len(blocks), 3)

        blocks = SeparateOrBlocks("a")
        self.assertEqual(len(blocks), 1)

        blocks = SeparateOrBlocks("'a|b'|c")
        self.assertEqual(len(blocks), 2)

        node =  Tokenization.SentenceNode('d')

        self.assertTrue(LogicMatch("'c|d'|e", node))

        self.assertTrue(LogicMatch("notfeature|'d'|notfeature2", node))

    def test_CheckPrefix(self):
        word, matchtype = CheckPrefix("\"abc\"", "unknown")
        self.assertEqual(matchtype, "text")

        word, matchtype = CheckPrefix("\"abc\"|ab", "unknown")
        self.assertEqual(matchtype, "unknown")

        word, matchtype = CheckPrefix("\"abc\"|ab|\"cde\"", "unknown")
        self.assertEqual(matchtype, "unknown")

        word, matchtype = CheckPrefix("'abc'", "unknown")
        self.assertEqual(matchtype, "norm")

        word, matchtype = CheckPrefix("'abc'|ab", "unknown")
        self.assertEqual(matchtype, "unknown")

        word, matchtype = CheckPrefix("'abc'|ab|'cde'", "unknown")
        self.assertEqual(matchtype, "unknown")

