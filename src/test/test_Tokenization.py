import unittest
from Tokenization import *

from FeatureOntology import LoadFeatureOntology
XLocation = '../../fsa/X/'
LoadFeatureOntology('../../fsa/Y/feature.txt')
Lexicon.LoadLexicon(XLocation + 'LexX.txt', lookupSource=LexiconLookupSource.Exclude)
Lexicon.LoadSegmentLexicon()


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
        self.assertEqual(NodeList.size, 8)

        NodeList.combine(3, 1)
        self.assertEqual(NodeList.size, 8)
        NodeList.combine(3, 2)
        self.assertEqual(NodeList.size, 7)

    def testSpaceInCombine(self):
        t = "a b  c   d    e"
        NodeList = Tokenize(t)
        self.assertEqual(NodeList.size, 5)
        NodeList.combine(3, 2)
        self.assertEqual(NodeList.size, 4)
        print(NodeList)
        NodeList.combine(2, 2)
        self.assertEqual(NodeList.size, 3)
        print(NodeList)

        t = "蓝色   有jd 3452 j34lm3n2吗"
        NodeList = Tokenize(t)
        print(NodeList)
        self.assertEqual(NodeList.size, 12)
        NodeList.combine(3, 2)
        self.assertEqual(NodeList.size, 11)
        print(NodeList)
        NodeList.combine(2, 2)
        self.assertEqual(NodeList.size, 10)
        print(NodeList)
        print(NodeList.root())

    def testOffset(self):
        t = "1 3  6   10"
        NodeList = Tokenize(t)
        self.assertEqual(NodeList.size, 4)
        self.assertEqual(NodeList.get(1).StartOffset, 2)
        self.assertEqual(NodeList.get(1).EndOffset, 3)
        self.assertEqual(NodeList.get(2).StartOffset, 5)
        self.assertEqual(NodeList.get(2).EndOffset, 6)
        self.assertEqual(NodeList.get(3).StartOffset, 9)
        self.assertEqual(NodeList.get(3).EndOffset, 11)

        t = "1a3bc6def10"
        NodeList = Tokenize(t)
        self.assertEqual(NodeList.size, 7)
        self.assertEqual(NodeList.get(2).StartOffset, 2)
        self.assertEqual(NodeList.get(2).EndOffset, 3)
        self.assertEqual(NodeList.get(4).StartOffset, 5)
        self.assertEqual(NodeList.get(4).EndOffset, 6)
        self.assertEqual(NodeList.get(6).StartOffset, 9)
        self.assertEqual(NodeList.get(6).EndOffset, 11)

        t = "蓝色   有jd 3452 j34lm3n2吗"
        NodeList = Tokenize(t)
        self.assertEqual(NodeList.size, 12)
        self.assertEqual(NodeList.get(1).StartOffset, 2)
        self.assertEqual(NodeList.get(1).EndOffset, 5)
        self.assertEqual(NodeList.get(2).StartOffset, 5)
        self.assertEqual(NodeList.get(2).EndOffset, 6)

    def testListHead(self):
        t = "this is a good desk, for study"
        NodeList = Tokenize(t)
        print(NodeList)
        self.assertEqual(NodeList.size, 8)

        NodeList.combine(7, 1)
        print(NodeList)
        self.assertEqual(NodeList.size, 8)

        NodeList.combine(6, 2)
        print(NodeList)
        self.assertEqual(NodeList.size, 7)

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
        Lexicon.LoadLexicon(XLocation + 'LexX-perX.txt')
        Lexicon.LoadSegmentLexicon()
        t = "中文语义识别研究"

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

        t = "有 "
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 1)

        t = "很少有 科普"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 5)

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
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(7, NodeList.size)
        self.assertEqual(NodeList.get(2).text, "巴西")
        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(0).features)
        self.assertTrue(utils.FeatureID_SpaceQ in NodeList.get(1).features)
        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(1).features)
        self.assertTrue(utils.FeatureID_SpaceQ in NodeList.get(2).features)
        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(2).features)

        t = "a 中文 之间的    空格"  # 2/2
        NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(7, NodeList.size)
        self.assertEqual(NodeList.get(2).text, " ")
        self.assertEqual(NodeList.get(3).text, "之间")

        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(0).features)
        self.assertTrue(utils.FeatureID_SpaceQ in NodeList.get(1).features)

        t = "有什么）  不同吗"  # 2/2
        NodeList = Tokenize(t)
        # import ProcessSentence
        # ProcessSentence.PrepareJSandJM(NodeList)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(6, NodeList.size)

    def test4G(self):
        t = "4G网络"
        NodeList = Tokenize(t)
        self.assertEqual(2, NodeList.size)
        t = "4g网"
        NodeList = Tokenize(t)
        self.assertEqual(2, NodeList.size)

    def testSegmentation_mixed(self):

        t = "ios5越狱,美化成功;哈哈"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(7, NodeList.size) #lexicon is loaded
        self.assertEqual(NodeList.get(0).text, "ios5")
        #self.assertEqual(NodeList.get(3).text, "之间")

        # XLocation = '../../fsa/X/'
        #
        # Lexicon.LoadLexicon(XLocation + 'LexX.txt')
        Lexicon.LoadSegmentLexicon()
        #
        # t = "3d显示"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size)
        # t = "3D显示"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "越狱" is not a word.
        # t = "3d播放"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "越狱" is not a word.
        # t = "3D播放"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "越狱" is not a word.

        t = "1500和1000"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(3, NodeList.size) #lexicon not loaded. "越狱" is not a word.

        # Lexicon.LoadLexicon(XLocation + 'LexXplus.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-brandX.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-idiomXdomain.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-idiomX.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-locX.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-perX.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-EnglishPunctuate.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-ChinesePunctuate.txt')
        # Lexicon.LoadLexicon(XLocation + 'LexX-brandsKG.txt')
        #
        # Lexicon.LoadLexicon(XLocation + 'defPlus.txt', lookupSource=LexiconLookupSource.defLex)
        # Lexicon.LoadLexicon(XLocation + 'defLexX.txt', lookupSource=LexiconLookupSource.defLex)
        # Lexicon.LoadLexicon(XLocation + 'defLexXKG.txt', lookupSource=LexiconLookupSource.defLex)
        #
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_2_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_3_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_4_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_5_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/comment_companyname.txt',    lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadSegmentLexicon()
        # t = "3d显示"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size)
        # t = "3D显示"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "越狱" is not a word.
        # t = "3d播放"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "越狱" is not a word.
        # t = "3D播放"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "越狱" is not a word.

    # def testFinal(self):
    #     import ProcessSentence
    #     ProcessSentence.LoadCommonLexicon(XLocation = '../../fsa/X/')
    #     t = "一共有3G"
    #     NodeList = Tokenize(t)
    #     self.assertEqual(NodeList.size, 4)
    #     self.assertEqual(NodeList.head.text, "一共")