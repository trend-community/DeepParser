import unittest, os
from ..LogicOperation import *
import Tokenization


class FeatureTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FeatureTest, self).__init__(*args, **kwargs)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        FeatureOntology.LoadFullFeatureList(dir_path + '/../../../fsa/extra/featurelist.txt')


    def test_simple(self):
        """exact match"""
        node =  Tokenization.EmptyBase()
        node.features = set()
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertTrue(LogicMatchFeatures("NN", node))
    def test_And(self):
        node =  Tokenization.EmptyBase()
        node.lexicon = None
        node.word = "abc"
        node.features = set()
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertFalse(LogicMatchFeatures("NN percent", node))

        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertTrue(LogicMatchFeatures("NN percent", node))
    def test_Or(self):
        node = Tokenization.EmptyBase()
        node.features = set()
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertTrue(LogicMatchFeatures("NN|percent", node))
        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertTrue(LogicMatchFeatures("NP|percent", node))
        self.assertFalse(LogicMatchFeatures("NP", node))
    def test_NotOr(self):
        node = Tokenization.EmptyBase()
        node.features = set()
        node.features.add(FeatureOntology.GetFeatureID('NN'))

        self.assertFalse(LogicMatchFeatures("!NN|percent", node))
        node.features.add(FeatureOntology.GetFeatureID('percent'))
        self.assertFalse(LogicMatchFeatures("!NP|percent", node))
        self.assertTrue(LogicMatchFeatures("!NP", node))


class RuleTest(unittest.TestCase):
    def test_LogitExact(self):
        """Exact match"""
        node = Tokenization.EmptyBase()
        node.lexicon = None
        node.word = "being"
        node.features = set()
        self.assertTrue(LogicMatch("being", node))
    def test_LogicOr(self):
        """Logic Or"""
        node = Tokenization.EmptyBase()
        node.lexicon = None
        node.word = "being"
        node.features = set()

        self.assertTrue(LogicMatch("being|getting", node))
    def test_LogicAnd(self):
        """Logic And"""
        node =  Tokenization.EmptyBase()
        node.lexicon = None
        node.word = "c"
        node.features = set()

        self.assertFalse(LogicMatch("c d", node))
        self.assertTrue(LogicMatch("c c", node))
    def test_LogicAndOr(self):
        """Logic And/Or"""
        node =  Tokenization.EmptyBase()
        node.lexicon = None
        node.word = "d"
        node.features = set()

        self.assertFalse(LogicMatch("c|d c", node))

        node.word = "c"
        self.assertTrue(LogicMatch("c|d c", node))
    def test_LogicNotOr(self):
        """Logic And/Or"""
        node =  Tokenization.EmptyBase()
        node.lexicon = None
        node.word = "d"
        node.features = set()

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
        self.assertFalse(LogicMatch("c|d !d|c", node))
        node.word = "f"
        self.assertFalse(LogicMatch("c|d !d|e", node))

