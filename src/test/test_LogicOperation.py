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

        self.assertTrue(LogicMatchFeatures([node], 0, "NN"))
    def test_And(self):
        node =  Tokenization.SentenceNode("abc")
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertFalse(LogicMatchFeatures([node], 0, "NN percent"))

        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertTrue(LogicMatchFeatures([node], 0, "NN percent"))
    def test_Or(self):
        node = Tokenization.SentenceNode('')
        node.features = set()
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertTrue(LogicMatchFeatures([node], 0, "NN|percent"))
        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertTrue(LogicMatchFeatures([node], 0, "NP|percent"))
        self.assertFalse(LogicMatchFeatures([node], 0, "NP"))
    def test_NotOr(self):
        node = Tokenization.SentenceNode('')
        node.features = set()
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertFalse(LogicMatchFeatures([node], 0, "!NN|percent"))
        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertFalse(LogicMatchFeatures([node], 0, "!NP|percent"))
        self.assertTrue(LogicMatchFeatures([node], 0, "!NP"))


class RuleTest(unittest.TestCase):
    def test_LogitExact(self):
        """Exact match"""
        node = Tokenization.SentenceNode('being')

        self.assertTrue(LogicMatch("being", node))
    def test_LogicOr(self):
        """Logic Or"""
        node = Tokenization.SentenceNode('being')

        self.assertTrue(LogicMatch("being|getting", node))
    def test_LogicAnd(self):
        """Logic And"""
        node =  Tokenization.SentenceNode("c")

        self.assertFalse(LogicMatch("c d", node))
        self.assertTrue(LogicMatch("c c", node))
    def test_LogicAndOr(self):
        """Logic And/Or"""
        node =  Tokenization.SentenceNode('d')

        self.assertFalse(LogicMatch("c|d c", node))

        node.word = "c"
        self.assertTrue(LogicMatch("c|d c", node))

        #self.assertTrue(LogicMatch())

    def test_LogicNotOr(self):
        """Logic And/Or"""
        node =  Tokenization.SentenceNode('d')

        self.assertFalse(LogicMatch("!c|d|e", node))
        node.word = "f"
        self.assertTrue(LogicMatch("!c|d|e", node))
        node.word = "e"
        self.assertTrue(LogicMatch("!c d|e", node))
        node.word = "f"
        self.assertFalse(LogicMatch("!c d|e", node))
        node.word = "c"
        self.assertTrue(LogicMatch("c|d !d|e", node))
        node.word = "d"
        self.assertFalse(LogicMatch("c|d !d|e", node))
        node.word = "e"
        self.assertFalse(LogicMatch("c|e !d|f|g|e", node))
        node.word = "e"
        self.assertFalse(LogicMatch("c|d !d|c", node))
        node.word = "f"
        self.assertFalse(LogicMatch("c|d !d|e", node))

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
        self.assertEqual(matchtype, "word")

        word, matchtype = CheckPrefix("\"abc\"|ab", "unknown")
        self.assertEqual(matchtype, "unknown")

        word, matchtype = CheckPrefix("\"abc\"|ab|\"cde\"", "unknown")
        self.assertEqual(matchtype, "unknown")

        word, matchtype = CheckPrefix("'abc'", "unknown")
        self.assertEqual(matchtype, "stem")

        word, matchtype = CheckPrefix("'abc'|ab", "unknown")
        self.assertEqual(matchtype, "unknown")

        word, matchtype = CheckPrefix("'abc'|ab|'cde'", "unknown")
        self.assertEqual(matchtype, "unknown")