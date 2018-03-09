
import unittest
from ProcessSentence import *


class RuleTest(unittest.TestCase):
    def test_ListMatch(self):
        list1 = ["", "A", "B"]
        list2 = [None, None, "B"]
        list3 = [None, "B", None]
        self.assertTrue(ListMatch(list1, list2))
        self.assertFalse(ListMatch(list1, list3))

