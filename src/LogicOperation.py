import logging, re, unittest

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
        Result = False
        OrBlocks = [x.strip() for x in re.split("\|", rule)]
        if len(OrBlocks) > 1:
            for OrBlock in OrBlocks:
                Result = Result or LogicMatch(OrBlock, word)

    return Result

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


if __name__ == "__main__":
    unittest.main()
