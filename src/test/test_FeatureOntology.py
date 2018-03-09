import unittest
from FeatureOntology import *
from Lexicon import *
#import .. import FeatureOntology

dir_path = os.path.dirname(os.path.realpath(__file__))

LoadFeatureOntology(dir_path + '/../../../fsa/Y/feature.txt')
LoadLexicon(dir_path + '/../../../fsa/Y/lexY.txt')


class FeatureTest(unittest.TestCase):

    def test_alias(self):
        dir_path1 = os.path.dirname(os.path.realpath(__file__))
        # LoadFullFeatureList(dir_path1 + '/../../../fsa/extra/featurelist.txt')
        # LoadFeatureOntology(dir_path1 + '/../../../fsa/extra/featureOntology_result.txt')
        #PrintFeatureOntology()

    def test_ontology(self):
        print(SearchFeatureOntology(GetFeatureID("com")))
        print(SearchFeatureOntology(GetFeatureID("com")))
        print(SearchFeatureOntology(GetFeatureID("NNP")))
        lex = SearchFeatureOntology(GetFeatureID("NNP"))
        self.assertTrue(GetFeatureID("nN") in lex.ancestors)


    def test2(self):
        s = SearchLexicon("ised")
        if s:
            print(s.features)
        print(SearchFeatures("airliner"))
        print(SearchFeatures("airliners"))
        #print("there are so many lexicons:%s" % len(_LexiconDict))
        print(SearchFeatures("pretty"))


    def test_alias1(self):
        node = OntologyNode()
        rest = node.ProcessAliasInFeatureFile("A=B=C, D, E, F")
        self.assertEqual(rest, "A,D,E,F")

    def test_setrule(self):
        node = OntologyNode()
        node.SetRule("job = titleN,per,anim,phy,n;perF 	// occupation and occupationN ")
        self.assertFalse(node.ancestors)    #this should be in _FeatureOntology already

    def test_SplitFeatures(self):
        a = SplitFeatures("this is a string")
        self.assertEqual(len(a), 4)

        a = SplitFeatures("this is 'a string'")
        self.assertEqual(len(a), 3)

        a = SplitFeatures("this is a /norm|norm2|norm4/")
        self.assertEqual(len(a), 4)

    def test_ProcessBarTags(self):
        featurelist = [0, 1, 2, 34, GetFeatureID("N"), GetFeatureID('CL'), GetFeatureID('NP')]
        print(str(featurelist))
        ProcessBarTags(featurelist)
        print(str(featurelist))
        self.assertEqual(len(featurelist), 4)
