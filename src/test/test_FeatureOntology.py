import unittest
from ..FeatureOntology import *
#import .. import FeatureOntology

class FeatureTest(unittest.TestCase):

    def test1(self):
        print(SearchFeatureOntology(GetFeatureID("com")))
        s = SearchLexicon("is")
        if s:
            print(s.features)
        s = SearchLexicon("ised")
        if s:
            print(s.features)
        print(SearchFeatures("airliner"))
        print(SearchFeatures("airliners"))
        #print("there are so many lexicons:%s" % len(_LexiconDict))
        print(SearchFeatures("pretty"))
