import unittest
from LogicOperation import *
import Tokenization, Rules


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

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "NN percent", [Rules.RuleToken()], 0))

        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NN percent", [Rules.RuleToken()], 0))
    def test_Or(self):
        node = Tokenization.SentenceNode('')
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NN|percent", [Rules.RuleToken()], 0))
        node.features.add(FeatureOntology.GetFeatureID('percent'))

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "NP|percent", [Rules.RuleToken()], 0))
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "NP", [Rules.RuleToken()], 0))

    def test_NotOr(self):
        node = Tokenization.SentenceNode('')
        node.features.add(FeatureOntology.GetFeatureID('NN'))
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!NN|percent", [Rules.RuleToken()], 0))

        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!NN|percent", [Rules.RuleToken()], 0))
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "!NP", [Rules.RuleToken()], 0))


class RuleTest(unittest.TestCase):
    def test_LogitExact(self):
        """Exact match"""
        node = Tokenization.SentenceNode('being')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "being", [Rules.RuleToken()], 0))

    def test_LogicOr(self):
        """Logic Or"""
        node = Tokenization.SentenceNode('being')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "being|getting", [Rules.RuleToken()], 0))

    def test_LogicAnd(self):
        """Logic And"""
        node =  Tokenization.SentenceNode("c")
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        ruletokenlist = [Rules.RuleToken()]

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c d", ruletokenlist, 0))
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "c c", ruletokenlist, 0))

    def test_LogicAndOr(self):
        """Logic And/Or"""
        node =  Tokenization.SentenceNode('d')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        ruletokenlist = [Rules.RuleToken()]
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d c", ruletokenlist, 0))
        node.text = "c"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "c|d c", ruletokenlist, 0))

        #self.assertTrue(LogicMatch())

    def test_LogicNotOr(self):
        """Logic And/Or"""
        node =  Tokenization.SentenceNode('d')
        strtokenlist = Tokenization.SentenceLinkedList()
        strtokenlist.append(node)

        RuleTokenList = [Rules.RuleToken()]

        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!c|d|e", RuleTokenList, 0))
        node.text = "f"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "!c|d|e", RuleTokenList, 0))
        node.text = "e"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "!c d|e", RuleTokenList, 0))
        node.text = "f"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "!c d|e", RuleTokenList, 0))
        node.text = "c"
        self.assertTrue(LogicMatchFeatures(strtokenlist, 0, "c|d !d|e", RuleTokenList, 0))
        node.text = "d"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d !d|e", RuleTokenList, 0))
        node.text = "e"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|e !d|f|g|e", RuleTokenList, 0))
        node.text = "e"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d !d|c", RuleTokenList, 0))
        node.text = "f"
        self.assertFalse(LogicMatchFeatures(strtokenlist, 0, "c|d !d|e", RuleTokenList, 0))


    def test_LogicCombined(self):
        """Logic Combined"""

        blocks = SeparateOrBlocks("a|b|c")
        self.assertEqual(len(blocks), 3)

        blocks = SeparateOrBlocks("a")
        self.assertEqual(len(blocks), 1)

        blocks = SeparateOrBlocks("'a|b'|c")
        self.assertEqual(len(blocks), 2)


        strtokenlist = Tokenization.Tokenize('d')
        RuleTokenList = [Rules.RuleToken()]

        self.assertTrue(LogicMatch(strtokenlist, 0, 'd', RuleTokenList, 0))

        #strtokenlist = Tokenization.Tokenize("notfeature|'d'|notfeature2")
        self.assertTrue(LogicMatch(strtokenlist, 0, "notfeature|'d'|notfeature2", RuleTokenList, 0))

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

    def test_SeparateOrBlocks(self):
        a = SeparateOrBlocks("一款")
        self.assertEqual(len(a), 1)

        b = SeparateOrBlocks("一|款")
        self.assertEqual(len(b), 2)

        c = SeparateOrBlocks("一|款|款")
        self.assertEqual(len(c), 3)



