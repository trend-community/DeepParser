import unittest
from ..FeatureOntology import *
#import .. import FeatureOntology

dir_path = os.path.dirname(os.path.realpath(__file__))
LoadFullFeatureList(dir_path + '/../../../fsa/extra/featurelist.txt')
LoadFeatureOntology(dir_path + '/../../../fsa/Y/feature.txt')
LoadLexicon(dir_path + '/../../../fsa/Y/lexY.txt')


class FeatureTest(unittest.TestCase):

    def test_ontology(self):
        print(SearchFeatureOntology(GetFeatureID("com")))
        print(SearchFeatureOntology(GetFeatureID("com")))
    def test_lexicon(self):
        print("i-myself")
        s = SearchLexicon("i_myself")
        if s:
            print(s.features)

        for f in s.features:
            feature = GetFeatureName(f)
            print (feature)
            if feature == "sent":
                self.assertTrue(True)
        self.assertTrue(False)

    def test2(self):
        s = SearchLexicon("ised")
        if s:
            print(s.features)
        print(SearchFeatures("airliner"))
        print(SearchFeatures("airliners"))
        #print("there are so many lexicons:%s" % len(_LexiconDict))
        print(SearchFeatures("pretty"))
