import unittest
from Tokenization import *

class TokenizationTest(unittest.TestCase):
    def testToken(self):
        t = SentenceNode("good")
        print(t.oneliner())
        print(t.JsonOutput())
