import unittest
from FeatureOntology import *
#import .. import FeatureOntology

dir_path = os.path.dirname(os.path.realpath(__file__))
LoadFullFeatureList(dir_path + '/../../../fsa/extra/featurelist.txt')
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
    def test_lexicon(self):
        FoundSent = False
        #print("i-myself")
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

    def test2(self):
        s = SearchLexicon("ised")
        if s:
            print(s.features)
        print(SearchFeatures("airliner"))
        print(SearchFeatures("airliners"))
        #print("there are so many lexicons:%s" % len(_LexiconDict))
        print(SearchFeatures("pretty"))

    def test_alias(self):
        node = OntologyNode()
        rest = node.ProcessAlias("A=B=C, D, E, F")
        self.assertEqual(rest, "A, D, E, F")

    def test_setrule(self):
        node = OntologyNode()
        node.SetRule("job = titleN,per,anim,phy,n;perF 	// occupation and occupationN ")
        self.assertFalse(node.ancestors)    #this should be in _FeatureOntology already


