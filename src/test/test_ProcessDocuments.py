
import unittest
from ProcessDocuments import *


class RuleTest(unittest.TestCase):
    def test_SentenceSegmentation(self):
        ss = SentenceSegmentation("味道还是不错。支持博达，下次还来买。")
        self.assertEqual(len(ss), 2)

    def test_MultiSentenceSegmentation(self):
        ss = SentenceSegmentation("味道还是不错。支持博达；下次还来买。")
        self.assertEqual(len(ss), 3)
        self.assertEqual(ss[0], "味道还是不错。")
