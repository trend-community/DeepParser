import unittest
from utils import *

class UtilsTest(unittest.TestCase):



    def testGet(self):
        self.assertEqual(True, True)

    def testIndexIn2DArray(self):
        a = [[2, 3, 5], [4, 9]]
        x, y = IndexIn2DArray(3, a)
        self.assertEqual(x, 0)
        self.assertEqual(y, 1)

        x, y = IndexIn2DArray(6, a)
        self.assertEqual(x, -1)
        self.assertEqual(y, -1)
