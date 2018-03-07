import unittest
from Tokenization import *

class TokenizationTest(unittest.TestCase):
    def testToken(self):
        t = SentenceNode("good")
        print(t.oneliner())
        NodeList = Tokenize("better")
        NodeList.insert(t, 0)
        self.assertEqual(NodeList.size, 2)


    def testList(self):
        t = "this is a good desk, for study"
        NodeList = Tokenize(t)
        print(NodeList)
        #NodeList.combine(3, 2)
        print(NodeList)

        NodeList.combine(3, 1)
        print(NodeList)

    def testListHead(self):
        t = "this is a good desk, for study"
        NodeList = Tokenize(t)
        print(NodeList)

        NodeList.combine(7, 1)
        print(NodeList)

    def testListChinese(self):
        t = "中文语义识别研究"
        NodeList = Tokenize(t)
        print(NodeList)

        NodeList.combine(2, 2)
        print(NodeList)

    def testListOperation(self):
        t = "中文语义识别研究"
        NodeList = Tokenize(t)
        print(NodeList)

        NodeList.combine(2, 2)
        print(NodeList)
        NodeList.append(SentenceNode("尾"))
        print(NodeList)

        NodeList.insert(SentenceNode("第三个"), 3)
        print(NodeList)

        NodeList.insert(SentenceNode("头"), 0)
        print(NodeList)

        NodeList.insert(SentenceNode("最后一个"), 6)
        print(NodeList)

    def testJsonOutput(self):
        t = "中历"
        NodeList = Tokenize(t)
        print(NodeList)

        print(NodeList.get(1).CleanOutput().toJSON())
        NodeList.combine(0, 2)
        print(NodeList.get(0).CleanOutput().toJSON())


    def testSegmentation(self):
        t = "中文语义识别研究"

        Lexicon.LoadSegmentLexicon()

        NodeList = Tokenize(t)
        print(NodeList)
        self.assertEqual(NodeList.get(0).text, "中文")
        self.assertEqual(NodeList.get(1).text, "语义")
        self.assertEqual(NodeList.get(2).text, "识别")
        self.assertEqual(NodeList.get(3).text, "研究")
        with self.assertRaises(RuntimeError):
            NodeList.get(4)

        t = "很少有科普"
        NodeList = Tokenize(t)
        self.assertEqual(NodeList.size, 4)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

        t = "很少有 科普"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 4)

        t = "这稍微甜"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "天津市长"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 2)

        t = "坑害过人"  #6ngram.txt
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "李书福"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "前路椎间盘切除术"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        #self.assertEqual(NodeList.size, 2)

        t = "武装部长方大国"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 2)

        t = "产品安全有效"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 4)

        t = "候鸟吃必胜客"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "喝不惯"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "喝"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

    def testSegmentation_22(self):
        Lexicon.LoadSegmentLexicon()

        t = "巴西餐厅"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 2)
        self.assertEqual(NodeList.head.text, "巴西")

        t = "这家巴西餐厅"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 4)
        self.assertEqual(NodeList.get(2).text, "巴西")

        t = "巴西餐厅后"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)
        self.assertEqual(NodeList.get(0).text, "巴西")

    def testSegmentation_space(self):
        Lexicon.LoadSegmentLexicon()

        t = "a    beautiful 巴西 brazil 在   north  america"  # 2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 7)
        self.assertEqual(NodeList.get(2).text, "巴西")
