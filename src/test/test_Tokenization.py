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

        t = "čč˛   ćjd 3452 j34lm3n2ĺ"
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

        t = "čč˛   ćjd 3452 j34lm3n2ĺ"
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
        t = "ä¸­ćčŻ­äščŻĺŤç çŠś"
        NodeList = Tokenize(t)
        print(NodeList)

        NodeList.combine(2, 2)
        print(NodeList)

    def testListOperation(self):
        t = "ä¸­ćčŻ­äščŻĺŤç çŠś"
        NodeList = Tokenize(t)
        print(NodeList)

        NodeList.combine(2, 2)
        print(NodeList)
        NodeList.append(SentenceNode("ĺ°ž"))
        print(NodeList)

        NodeList.insert(SentenceNode("çŹŹä¸ä¸Ş"), 3)
        print(NodeList)

        NodeList.insert(SentenceNode("ĺ¤´"), 0)
        print(NodeList)

        NodeList.insert(SentenceNode("ćĺä¸ä¸Ş"), 6)
        print(NodeList)

    def testJsonOutput(self):
        t = "ä¸­ĺ"
        NodeList = Tokenize(t)
        print(NodeList)

        print(NodeList.get(1).CleanOutput().toJSON())
        NodeList.combine(0, 2)
        print(NodeList.get(0).CleanOutput().toJSON())


    def testSegmentation(self):
        Lexicon.LoadLexicon(XLocation + 'LexX-perX.txt')
        Lexicon.LoadSegmentLexicon()
        t = "ä¸­ćčŻ­äščŻĺŤç çŠś"

        NodeList = Tokenize(t)
        print(NodeList)
        self.assertEqual(NodeList.get(0).text, "ä¸­ć")
        self.assertEqual(NodeList.get(1).text, "čŻ­äš")
        self.assertEqual(NodeList.get(2).text, "čŻĺŤ")
        self.assertEqual(NodeList.get(3).text, "ç çŠś")
        with self.assertRaises(RuntimeError):
            NodeList.get(4)

        t = "ĺžĺ°ćç§ćŽ"
        NodeList = Tokenize(t)
        self.assertEqual(NodeList.size, 4)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

        t = "ć "
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 1)

        t = "ĺžĺ°ć ç§ćŽ"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 5)

        t = "čżç¨ĺžŽç"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "ĺ¤Šć´Ľĺ¸éż"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 2)

        t = "ĺĺŽłčżäşş"  #6ngram.txt
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "ćäšŚçŚ"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "ĺčˇŻć¤é´çĺé¤ćŻ"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        #self.assertEqual(NodeList.size, 2)

        t = "ć­ŚčŁé¨éżćšĺ¤§ĺ˝"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 2)

        t = "äş§ĺĺŽĺ¨ćć"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 4)

        t = "ĺé¸ĺĺżčĺŽ˘"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "ĺä¸ćŻ"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)

        t = "ĺ"  #external lexicon
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

    def testSegmentation_22(self):
        Lexicon.LoadSegmentLexicon()

        t = "ĺˇ´čĽżé¤ĺ"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 2)
        self.assertEqual(NodeList.head.text, "ĺˇ´čĽż")

        t = "čżĺŽśĺˇ´čĽżé¤ĺ"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 4)
        self.assertEqual(NodeList.get(2).text, "ĺˇ´čĽż")

        t = "ĺˇ´čĽżé¤ĺĺ"  #2/2
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(NodeList.size, 3)
        self.assertEqual(NodeList.get(0).text, "ĺˇ´čĽż")

    def testSegmentation_space(self):
        Lexicon.LoadSegmentLexicon()

        t = "a    beautiful ĺˇ´čĽż brazil ĺ¨   north  america"  # 2/2
        NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(7, NodeList.size)
        self.assertEqual(NodeList.get(2).text, "ĺˇ´čĽż")
        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(0).features)
        self.assertTrue(utils.FeatureID_SpaceQ in NodeList.get(1).features)
        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(1).features)
        self.assertTrue(utils.FeatureID_SpaceQ in NodeList.get(2).features)
        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(2).features)

        t = "a ä¸­ć äšé´ç    çŠşć ź"  # 2/2
        NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(7, NodeList.size)
        self.assertEqual(NodeList.get(2).text, " ")
        self.assertEqual(NodeList.get(3).text, "äšé´")

        self.assertTrue(utils.FeatureID_SpaceH in NodeList.get(0).features)
        self.assertTrue(utils.FeatureID_SpaceQ in NodeList.get(1).features)

        t = "ćäťäšďź  ä¸ĺĺ"  # 2/2
        NodeList = Tokenize(t)
        # import ProcessSentence
        # ProcessSentence.PrepareJSandJM(NodeList)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(6, NodeList.size)

    def test4G(self):
        t = "4Gç˝çť"
        NodeList = Tokenize(t)
        self.assertEqual(2, NodeList.size)
        t = "4gç˝"
        NodeList = Tokenize(t)
        self.assertEqual(2, NodeList.size)

    def testSegmentation_mixed(self):

        t = "ios5čśçą,çžĺćĺ;ĺĺ"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(7, NodeList.size) #lexicon is loaded
        self.assertEqual(NodeList.get(0).text, "ios5")
        #self.assertEqual(NodeList.get(3).text, "äšé´")

        # XLocation = '../../fsa/X/'
        #
        # Lexicon.LoadLexicon(XLocation + 'LexX.txt')
        Lexicon.LoadSegmentLexicon()
        #
        # t = "3dćžç¤ş"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size)
        # t = "3Dćžç¤ş"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "čśçą" is not a word.
        # t = "3dć­ćž"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "čśçą" is not a word.
        # t = "3Dć­ćž"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "čśçą" is not a word.

        t = "1500ĺ1000"
        NodeList = Tokenize(t)
        print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        self.assertEqual(3, NodeList.size) #lexicon not loaded. "čśçą" is not a word.

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
        # Lexicon.LoadLexicon(XLocation + 'defPlus.txt', lookupSource=LexiconLookupSource.DefLex)
        # Lexicon.LoadLexicon(XLocation + 'defLexX.txt', lookupSource=LexiconLookupSource.DefLex)
        # Lexicon.LoadLexicon(XLocation + 'defLexXKG.txt', lookupSource=LexiconLookupSource.DefLex)
        #
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_2_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_3_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_4_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/CleanLexicon_gram_5_list.txt', lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadLexicon(XLocation + 'Q/lexicon/comment_companyname.txt',    lookupSource=LexiconLookupSource.External)
        # Lexicon.LoadSegmentLexicon()
        # t = "3dćžç¤ş"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size)
        # t = "3Dćžç¤ş"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "čśçą" is not a word.
        # t = "3dć­ćž"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "čśçą" is not a word.
        # t = "3Dć­ćž"
        # NodeList = Tokenize(t)
        # print(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
        # self.assertEqual(2, NodeList.size) #lexicon not loaded. "čśçą" is not a word.

    # def testFinal(self):
    #     import ProcessSentence
    #     ProcessSentence.LoadCommonLexicon(XLocation = '../../fsa/X/')
    #     t = "ä¸ĺąć3G"
    #     NodeList = Tokenize(t)
    #     self.assertEqual(NodeList.size, 4)
    #     self.assertEqual(NodeList.head.text, "ä¸ĺą")