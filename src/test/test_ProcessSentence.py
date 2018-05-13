
import unittest
from ProcessSentence import *


class RuleTest(unittest.TestCase):
    def test_ListMatch(self):
        list1 = [["", "A", "B"], ["", "A", "B"]]
        list2 = [None, None, "B"]
        list3 = [None, "B", None]
        self.assertTrue(ListMatch(list1, list2))
        self.assertFalse(ListMatch(list1, list3))

    def test_ConstructNorms(self):
        alist = Tokenization.SentenceLinkedList()
        alist.norms.append(('a', ''))
        alist.norms.append(('b', 'B'))
        alist.norms.append(('c', ''))
        alist.norms.append(('d', 'D'))
        result = ConstructNorms(alist, 0)
        print(str(result))

        result = ConstructNorms(alist, 1)
        print(str(result))