import unittest
from Tokenization import *

class TokenizationTest(unittest.TestCase):
    def testToken(self):
        t = SentenceNode("good")
        print(t.oneliner())
        #print(t.JsonOutput())

    def testList(self):
        t = "this is a good desk, for study"
        NodeList = Tokenize_space(t)
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


    def testGet(self):
        t = "中文语义识别研究"
        NodeList = Tokenize(t)
        print(NodeList)
        self.assertEqual(NodeList.get(0).text, "中文")
        self.assertEqual(NodeList.get(1).text, "语义")
        self.assertEqual(NodeList.get(2).text, "识别")
        self.assertEqual(NodeList.get(3).text, "研究")
