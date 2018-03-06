import unittest

from Graphviz import *

class GraphTest(unittest.TestCase):
    def test_graph(self):
        meilizhongguo = '''
        {"EndOffset": 4, "StartOffset": 0, "features": ["NC", "modJJ", "XP", "loc", "NG", "locNE", "inanim", "NNP", "BR2", "n", "nN", "natural", "space", "hanzi", "country", "countryNE", "npr", "phy", "earth", "JM2", "JS2", "place", "c4"], "sons": [{"EndOffset": 2, "StartOffset": 0, "UpperRelationship": "M", "features": ["0", "A", "AC", "AP", "hanzi", "a", "aA", "Adjunct", "AP2", "XP", "cn", "pt", "xX", "BR2", "M", "looks", "Up", "VA", "pro", "JS2", "Kid", "sent", "beauty", "emph", "c2", "Mod"], "text": "美丽"}, {"EndOffset": 4, "StartOffset": 2, "features": ["space", "0", "N", "NC", "modJJ", "hanzi", "loc", "locNE", "inanim", "NNP", "country", "countryNE", "BR2", "n", "H", "npr", "nN", "phy", "earth", "JM2", "place", "natural", "c2"], "text": "中国"}], "text": "美丽中国"}
        '''
        rows = orgChart(meilizhongguo)
        print(str(rows))
        self.assertEqual(len(rows), 4)


        rows2 = orgChart2(meilizhongguo)
        print(str(rows2))
        self.assertEqual(len(rows2), 3)



    def test_1level(self):
        meili = '''
            {"EndOffset": 2, "StartOffset": 0, "features": ["0", "A", "AC", "hanzi", "a", "aA", "cn", "pt", "xX", "BR2", "looks", "Up", "VA", "JM2", "pro", "JS2", "sent", "beauty", "emph", "c2"], "text": "美丽"}  
                  '''
        rows = orgChart(meili)
        print(str(rows))
        self.assertEqual(len(rows), 0)

        rows2 = orgChart2(meili)
        print(str(rows2))
        self.assertEqual(len(rows2), 1)

