from Cache import *
import unittest

class FeatureTest(unittest.TestCase):

    def test1(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

        WriteSentenceDB("this is good", {"a":3})

