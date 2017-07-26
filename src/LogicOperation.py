import logging, re, unittest
import FeatureOntology

#not, and, or
def LogicMatch(rule, word):
    if rule == word:
        return True

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatch(AndBlock, word)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatch(rule[1:], word)
        else:
            Result = False
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatch(OrBlock, word)

    return Result


def LogicMatchFeatures(rule, featurelist):
    if not rule:
        return False
    featureID = FeatureOntology.GetFeatureID(rule)
    if featureID and featureID in featurelist:
        return True

    AndBlocks = [x.strip() for x in re.split(" ", rule)]
    if len(AndBlocks) > 1:
        Result = True
        for AndBlock in AndBlocks:
            Result = Result and LogicMatchFeatures(AndBlock, featurelist)
    else:
        if rule[0] == "!":      #Not
            Result = not LogicMatchFeatures(rule[1:], featurelist)
        else:
            Result = False
            OrBlocks = [x.strip() for x in re.split("\|", rule)]
            if len(OrBlocks) > 1:
                for OrBlock in OrBlocks:
                    Result = Result or LogicMatchFeatures(OrBlock, featurelist)

    return Result

class FeatureTest(unittest.TestCase):
    def test_simple(self):
        """exact match"""
        self.assertTrue(LogicMatchFeatures("NN", [FeatureOntology.GetFeatureID("NN")]))
    def test_And(self):
        self.assertFalse(LogicMatchFeatures("NN percent", [FeatureOntology.GetFeatureID("NN")]))
        self.assertTrue(LogicMatchFeatures("NN percent", [FeatureOntology.GetFeatureID("NN"), FeatureOntology.GetFeatureID("percent")]))
    def test_Or(self):
        self.assertTrue(LogicMatchFeatures("NN|percent", [FeatureOntology.GetFeatureID("NN")]))
        self.assertTrue(LogicMatchFeatures("NP|percent", [FeatureOntology.GetFeatureID("NN"), FeatureOntology.GetFeatureID("percent")]))
        self.assertFalse(LogicMatchFeatures("NP", [FeatureOntology.GetFeatureID("NN"), FeatureOntology.GetFeatureID("percent")]))
    def test_NotOr(self):
        self.assertFalse(LogicMatchFeatures("!NN|percent", [FeatureOntology.GetFeatureID("NN")]))
        self.assertFalse(LogicMatchFeatures("!NP|percent", [FeatureOntology.GetFeatureID("NN"), FeatureOntology.GetFeatureID("percent")]))
        self.assertTrue(LogicMatchFeatures("!NP", [FeatureOntology.GetFeatureID("NN"), FeatureOntology.GetFeatureID("percent")]))



class RuleTest(unittest.TestCase):
    def test_LogitExact(self):
        """Exact match"""
        self.assertTrue(LogicMatch("being", "being"))
    def test_LogicOr(self):
        """Logic Or"""
        self.assertTrue(LogicMatch("being|getting", "being"))
    def test_LogicAnd(self):
        """Logic And"""
        self.assertFalse(LogicMatch("a b", "a"))
        self.assertTrue(LogicMatch("a a", "a"))
    def test_LogicAndOr(self):
        """Logic And/Or"""
        self.assertFalse(LogicMatch("a|b a", "b"))
        self.assertTrue(LogicMatch("a|b a", "a"))
    def test_LogicNotOr(self):
        """Logic And/Or"""
        self.assertFalse(LogicMatch("!a|b|c", "b"))
        self.assertTrue(LogicMatch("!a|b|c", "d"))
        self.assertTrue(LogicMatch("!a b|c", "c"))
        self.assertFalse(LogicMatch("!a b|c", "d"))
        self.assertTrue(LogicMatch("a|b !b|c", "a"))
        self.assertFalse(LogicMatch("a|b !b|c", "b"))
        self.assertFalse(LogicMatch("a|b !b|c", "c"))
        self.assertFalse(LogicMatch("a|b !b|c", "d"))


if __name__ == "__main__":
    unittest.main()
