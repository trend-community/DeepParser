
import unittest
from Rules import *
from Rules import _RuleList,  _ProcessOrBlock, _ExpandOrBlock, _ExpandParenthesis

class RuleTest(unittest.TestCase):
    def test_Tokenization(self):
        tokenlist = Tokenize("[a] [b]")
        self.assertEqual(tokenlist[0].word, '[a]')
        tokenlist = Tokenize("[JS2 !DT|PDT|VBN|pro] <([R:^V.R]? ^V[0 Ved:^.M] @andC)? [R:^V2.R]? ^V2[0 Ved:^.M] [AP:^.M]* @noun_mod [N !date:NP]>")
        self.assertEqual(len(tokenlist), 7)

    def test_Tokenization_or(self):
        tokenlist = Tokenize("[a b c]|[d e f]")
        self.assertEqual(len(tokenlist), 1)

        tokenlist = Tokenize("""[a b c]
            | [d e f]""")
        self.assertEqual(len(tokenlist), 1)

    def test_T_parenthesis(self):
        tokenlist = Tokenize(""" 	MD | "\'d|wil|mite|wanna|gotta" | ( ("do|does|did") 'have|seem|claim|appear|tend|want|wish|hope|desire|expect' "to" )""")
        self.assertEqual(len(tokenlist), 1)

    def test_T_pointer_or(self):
        tokenlist = Tokenize(" [VB : ^.ModS]|[要: ^.ModS] ")
        self.assertEqual(len(tokenlist), 1)
        self.assertEqual(tokenlist[0].word, "[VB : ^.ModS]|[要: ^.ModS]")

        tokenlist = Tokenize(" ^A[VB : ^.ModS]|^B[要: ^.ModS] ")
        self.assertEqual(len(tokenlist), 1)
        self.assertEqual(tokenlist[0].word, "^A[VB : ^.ModS]|^B[要: ^.ModS]")

    def test_SetRule_number(self):
        r = Rule()
        r.SetRule("a==   [0 a]4 [b]* [c]*7 [d]? [e]10 [f]*15 [g]12*16")
        self.assertEqual(r.Tokens[0].repeat[1], 4)
        self.assertEqual(r.Tokens[0].word, "[a]")
        self.assertEqual(r.Tokens[1].repeat[1], 3)
        self.assertEqual(r.Tokens[2].repeat[1], 7)
        self.assertEqual(r.Tokens[3].repeat[1], 1)
        self.assertEqual(r.Tokens[3].repeat[0], 0)

        self.assertEqual(r.Tokens[4].repeat[1], 10)
        self.assertEqual(r.Tokens[5].repeat[1], 15)

        self.assertEqual(r.Tokens[6].repeat[1], 16)
        self.assertEqual(r.Tokens[6].repeat[0], 12)

    def test_tokenspace(self):
        r = Rule()
        r.SetRule("b==[0 a b? c:d e]")
        self.assertEqual(r.Tokens[0].word, '[a b? c]')
        self.assertEqual(r.Tokens[0].action, 'd e')
    def test_Rule(self):
        r = Rule()
        r.SetRule("""PassiveSimpleING == {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};""")
        self.assertEqual(r.Tokens[1].word, "[RB]")
    def test_twolines(self):
        r = Rule()
        r.SetRule("""rule4words=={[word] [word]
	[word] [word]};""")
        result = r.oneliner()[-46:] == "rule4words == {[word]_[word]_[word]_[word]_};\n" or \
            r.oneliner()[-46:] == "rule4words == {[word] [word] [word] [word] };\n"
        self.assertTrue(result)
    def test_pointer(self):
        r = Rule()
        r.SetRule("rule=={^[word] ^head[word]};")
        self.assertEqual(r.Tokens[0].pointer, "")
        self.assertEqual(r.Tokens[1].pointer, "head")
        self.assertEqual(r.Tokens[1].word, "[word]")

    def test_which(self):
        r = Rule()
        r.SetRule("""
        which::
	^VWHSS advP? [F=which NP:^V2.O Wh] advP? ^V2[infinitive Kid=!O:^.ObjV]
    ^VWHSS advP? [F=which NP:^V2.O Wh] [NP "!me|him|us|them":^V2.S] PP? R* ^V2[!passive Pred Kid=!Obj:^.ObjV]
    ^VWHSS advP? [F=which NP:^V2.O Whh] R* ^V2[passive Pred Kid=!Obj:^.ObjV]
	^[NP2 !pro] [R|PP]? ['\,':Done]? (IN+'which':^V.X) ^V[CL:^.ModS]
	^[NP2 !pro] [R|PP]? ['\,':Done]? [NP F=the:^V.S] (of+which:^V.X) [R|PP|DE]* ^V[CL:^.ModS]
//comment
	^VWHSS advP? ['which+one':^V2.O Wh JS2] advP? ^V2[infinitive Kid=!O:^.ObjV]
    ^VWHSS advP? ['which+one':^V2.O Wh JS2] [NP "!me|him|us|them":^V2.S] PP? R* ^V2[Pred !passive Kid=!Obj:^.ObjS]
    ^VWHSS advP? ['which+one':^V2.O Wh JS2] R* ^V2[Pred passive Kid=!Obj:^.ObjS]
//comment2
	^VWHSS advP? ['which':^V2.O JS2] advP? ^V2[infinitive Kid=!O:^.ObjV]
    ^VWHSS advP? ['which':^V2.O JS2] R* ^V2[passive Pred Kid=!Obj:^.ObjV]
	^VWHSS advP? [F=which NP:^V2.O JS2] advP? ^V2[infinitive Kid=!O:^.ObjV]
//comment3
	^VWHSS advP? ['which':^V2.S JS2] R* ^V2[Pred !passive Kid=Obj|Cap:^ObjS CL]
	^VWHSS advP? ['which+one':^V2.S JS2] R* ^V2[Pred !passive Kid=Obj|Cap:^ObjS]
//comment
	^VWHSS advP? [which+one:^V2.S JS2]　R*　^V2[Pred !passive Kid=Obj|Cap:^.ObjS]
	^VWHSS advP? [F=which NP:^V2.S JS2] R* ^V2[Pred !passive Kid=Obj|Cap:^.ObjsS]
//commebt
    ^VWHSS advP? [which:^V2.S JS2] R* ^V2[Pred !passive:^.ObjS]
    ^VWHSS advP? [which+one:^V2.S JS2]) R* ^V2[Pred !passive:^.ObjS]
    ^VWHSS advP? [F=which NP:^V2.S JS2] R* ^V2[Pred !passive:^.ObjS]
//asdfsdfa
    ^VWHSS advP? [which:^V2.O JS2] R* [NP !me|him|us|them:^V2.S JS2] ^V2[Pred !passive !vi Kid=!Obj:^.ObjS]
    ^VWHSS advP? [which+one:^V2.O JS2] R* [NP !me|him|us|them:^V2.S JS2] ^V2[Pred !passive !vi Kid=!Obj:^.ObjS]

        """)
        #print(r)

    def test_Macro(self):
        ResetRules()
        InsertRuleInList("""@andC == ([0 "and|or|&amp;|as_well_as|\/|and\/or"])""")
        s = ProcessMacro("a @andC")
        self.assertEqual(s, "a ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"])")

        s = ProcessMacro("a @andC @andC")
        self.assertEqual(s, "a ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"]) ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"])")

        InsertRuleInList("""#macro_with_parameter(1=$HAVE 2=$NEG, 3=$tm 4=$neg) ==
         <$HAVE $NEG [RB:^.R]? [VBN|Ved:VG perfect $tm $neg ]>""")
        s = ProcessMacro("""#macro_with_parameter(1=a 2=b, 3=c 4=d)""")
        self.assertEqual(s, "<a b [RB:^.R]? [VBN|Ved:VG perfect c d ]>")

        s = ProcessMacro("""#macro_with_parameter(1=a 2=NULL, 3=c 4)""")
        self.assertEqual(s, "<a  [RB:^.R]? [VBN|Ved:VG perfect c  ]>")

        s = ProcessMacro("""#macro_with_parameter(1="a|b" 2=NULL, 3=c 4)""")
        self.assertEqual(s, """<"a|b"  [RB:^.R]? [VBN|Ved:VG perfect c  ]>""")


        InsertRuleInList("""@modalV ==
	( 	MD // MD includes 'will|shall|shalt|would|can|could|should|must|may|might' etc.
		| "\'d|wil|mite|wanna|gotta" // we need escape character "\'d" because we reserve ' for STEM checking
		| ( ("do|does|did") 'have|seem|claim|appear|tend|want|wish|hope|desire|expect' "to" ) // they do appear to own it
	)
""")
        InsertRuleInList("""#simpleMpassive(1=$NEG, 2=$neg) ==
        <@modalV $NEG [RB:^.R]? "be" [RB:^.R]? [VBN|Ved: VG passive simple  modal $neg]> !NNS
            """)
        #InsertRuleInList("""simpleModalPassive == #simpleMpassive(1,2); """)

        #OutputRules()


    def test_Expand(self):
        ResetRules()

        self.assertEqual(len(_RuleList), 0)
        InsertRuleInList("aaa==[NR] [PP]?")
        self.assertEqual(len(_RuleList), 1)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 2)
        InsertRuleInList("bbb==[JS]? [JM]?")
        self.assertEqual(len(_RuleList), 3)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 6)

        #OutputRules()

    def test_adjacentbracket(self):
        r = Rule()
        r.SetRule("rule == [ab][cd]")
        self.assertEqual(len(r.Tokens), 2)
        self.assertEqual(r.Tokens[1].word, "[cd]")

    def test_parenthsis_complicate(self):
        _RuleList.clear()
        r = Rule()
        r.SetRule("rule_p == [JS2 !DT|PDT|VBN|pro] <([R:^V.R]? ^V[0 Ved:^.M] @andC)? [R:^V2.R]? ^V2[0 Ved:^.M] [AP:^.M]* @noun_mod [N !date:NP]>")
        self.assertEqual(len(r.Tokens), 7)
        if r.RuleName:
            _RuleList.append(r)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 16)
        print("Before expand  parenthesis")
        #OutputRules()
        _ExpandParenthesis(_RuleList)
        self.assertEqual(len(_RuleList), 16)
        print("Before expand rule, after parenthesis")
        #OutputRules()

        ExpandRuleWildCard()
        print(" after expand rule again")
        #OutputRules()
        #self.assertEqual(len(_RuleList), 24)

    def test_parenthsis(self):
        _RuleList.clear()
        r = Rule()
        r.SetRule(
            "rule_p ==  <([R:^V.R]? ^V[0 Ved:^.M] @andC)? ")
        self.assertEqual(len(r.Tokens), 1)
        if r.RuleName:
            _RuleList.append(r)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 2)
        _ExpandParenthesis(_RuleList)
        print("Start rules after expand parenthesis")
        #OutputRules()
        newr = _RuleList[1]
        self.assertEqual(len(newr.Tokens), 3)
        ExpandRuleWildCard()
        print("Start rules after expand wild card again")
        #OutputRules()
        self.assertEqual(len(_RuleList), 3)


    def test_parenthsis_complicate_little(self):
        _RuleList.clear()
        r = Rule()
        r.SetRule("rule_p == [JS2 !DT|PDT|VBN|pro] <([R:^V.R]? ^V[0 Ved:^.M] @andC)? [R:^V2.R]>")
        self.assertEqual(len(r.Tokens), 3)
        if r.RuleName:
            _RuleList.append(r)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 2)
        #print("Before expand  parenthesis")
        #OutputRules()
        _ExpandParenthesis(_RuleList)
        self.assertEqual(len(_RuleList), 2)
        #print("Before expand rule, after parenthesis")
        #OutputRules()

        ExpandRuleWildCard()
        #print(" after expand rule again")
        #OutputRules()
        self.assertEqual(len(_RuleList), 3)

    def test_parenthsis_or(self):
        _RuleList.clear()
        InsertRuleInList("""
@yourC ==
(
	[PRPP:^.M]
	| [one:^.M POS]

)
""")

        InsertRuleInList("DT_NN_VBG_NN2 == (/the/|'any|such|these|those'|@yourC) ")

        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 1)
        #print("Before expand  parenthesis")
        #OutputRules()
        ExpandParenthesisAndOrBlock()

        #print("Before expand wild card rule, after parenthesis")
        #OutputRules()
        self.assertEqual(len(_RuleList), 4)

        ExpandRuleWildCard()
        #print(" after expand wild card")
        #OutputRules()
        self.assertEqual(len(_RuleList), 4)

    def test_parenthsis_or_pointer(self):
        ResetRules()
        InsertRuleInList("""
@yourC ==
( ^V[VB : ^.ModS] | ^W[要: ^.ModS] )
""")

        InsertRuleInList("DT_NN_VBG_NN2 == @yourC ")

        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 1)
        # print("Before expand  parenthesis")
        # OutputRules()
        ExpandParenthesisAndOrBlock()

        # print("Before expand wild card rule, after parenthesis")
        # OutputRules()
        self.assertEqual(len(_RuleList), 2)

        ExpandRuleWildCard()
        # print(" after expand wild card")
        # OutputRules()
        self.assertEqual(len(_RuleList), 2)

    def test_specialrule(self):

        ResetRules()
        InsertRuleInList("""single_token_NP5 == <[proNN:NP]>""")
        r = _RuleList[0]
        self.assertEqual(r.Tokens[0].word, "[proNN]")

    def test_ExpandOrBlock(self):
        _RuleList.clear()
        InsertRuleInList("abc == 'a' 'better|worse' 'gift'")
        self.assertEqual(len(_RuleList), 1)
        r = _RuleList[0]
        self.assertEqual(len(r.Tokens), 3)

        _ExpandOrBlock(_RuleList)
        #OutputRules()
        self.assertEqual(len(_RuleList), 1)
        r = _RuleList[0]
        self.assertEqual(len(r.Tokens), 3)


    def test_ExpandOrBlock2(self):
        ResetRules()
        InsertRuleInList("abc == 'a' ('better|worse') 'gift'")
        self.assertEqual(len(_RuleList), 1)
        r = _RuleList[0]
        self.assertEqual(len(r.Tokens), 3)

        _ExpandOrBlock(_RuleList)
        #OutputRules()
        self.assertEqual(len(_RuleList), 1)
        r = _RuleList[0]
        self.assertEqual(len(r.Tokens), 3)

    def test_Parenthesis2(self):
        ResetRules()
        InsertRuleInList("""ADJ_NP6 == < (	('a') | ([PN:^.M]) ) >""")
        self.assertEqual(len(_RuleList), 1)

        _ExpandOrBlock(_RuleList)
        self.assertEqual(len(_RuleList), 2)
        #OutputRules()

        _ExpandParenthesis(_RuleList)
        #OutputRules()
        r = _RuleList[0]
        self.assertEqual(len(r.Tokens), 1)
        #OutputRules()

    def test_ProcessOrBlock(self):
        whole, left, right = _ProcessOrBlock("['abc|def']", 5)
        self.assertEqual(whole, "abc|def")
        self.assertEqual(left, "abc")
        self.assertEqual(right, "def")

        whole, left, right = _ProcessOrBlock("(abc)|'def'|ghi", 5)
        self.assertEqual(whole, "(abc)|'def'")
        self.assertEqual(left, "(abc)")
        self.assertEqual(right, "'def'")

        whole, left, right = _ProcessOrBlock("(abc)|def|ghi", 5)
        self.assertEqual(whole, "(abc)|def")
        self.assertEqual(left, "(abc)")
        self.assertEqual(right, "def")

        whole, left, right = _ProcessOrBlock("/abc/|def|ghi", 5)
        self.assertEqual(whole, "/abc/|def")
        self.assertEqual(left, "/abc/")
        self.assertEqual(right, "def")

    def test_Parenthesis(self):
        ResetRules()
        InsertRuleInList("""simplePres == <[(VB)|VBZ:VG simple  pres]>;""")
        self.assertEqual(len(_RuleList), 1)

        _ExpandOrBlock(_RuleList)
        self.assertEqual(len(_RuleList), 2)
        #OutputRules()

        ResetRules()
        InsertRuleInList("""abc ==
        <[DT|PDT|( [PRPP:^.M] | (one:^.M POS) ):^.M]  [NE:NP]>
        """)
        self.assertEqual(len(_RuleList), 1)

        _ExpandOrBlock(_RuleList)
        #OutputRules()
        self.assertEqual(len(_RuleList), 4)

    def test_Actions_2(self):
        ResetRules()
        InsertRuleInList("""ACTION == ([pureDT:^.A] | [POS:^.M])""")

        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()

        ExpandRuleWildCard()

        #OutputRules("concise")
        self.assertEqual(len(_RuleList), 2)

    def test_Actions_3(self):
        ResetRules()
        InsertRuleInList("""ACTION == (([pureDT:^.A] | [POS:^.M]| [POS:^.M POS]))""")

        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()

        ExpandRuleWildCard()

        #OutputRules("concise")
        self.assertEqual(len(_RuleList), 4)

    def test_Actions_noDT(self):
        ResetRules()
        InsertRuleInList("""ACTION == [pureDT:^.A] | [POS:^.M]| [POS:^.M POS]""")

        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()

        ExpandRuleWildCard()

        #OutputRules("concise")
        self.assertEqual(len(_RuleList), 4)

    def test_Actions_NPP(self):
        ResetRules()

        InsertRuleInList(
            """precontext_IN_no_det_NP(Top) ==

                    ( [0 R b:^M.R] [0 a:^.M] )
                     [AP:^.M]

                 """)
        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()


        #OutputRules("concise")
        word = _RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = _RuleList[1].Tokens[0].word
        self.assertFalse(":" in word)
        #self.assertEqual(len(_RuleList), 1)

    def test_Expanding_VNPAP2(self):
        ResetRules()
        InsertRuleInList("""
        VNPAP2 == ^[VNPAP !passive VG2] [NP !JS2:^.O ^V2.O2] RB? ^V2[AP OTHO:ingAdj]|[enAdj:^.C] infinitive [!passive:^.purposeR]?
        """  )

        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()


        #OutputRules("concise")
        word = _RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = _RuleList[1].Tokens[0].word
        self.assertFalse(":" in word)

    def test_Expanding_Others(self):
        ResetRules()
        InsertRuleInList("""
        the_dollarsign(Top) == <[DT CURR:NP money]>
        """)

        InsertRuleInList("""
        the_blahblah_problem(Top) == <the [nv|NN:^.M] "up|down|in|out|away" ['time|trouble|difficulty|problem|experience|issue|topic|question|view|viewpoint':NP]>
        """)

        InsertRuleInList("""
        @yourC ==
        (
        	[PRPP:^.M]
        	| [one:^.M POS]

        )
        """)

        InsertRuleInList("""    DT_NN_VBG_NN2 ==
            '!with' (/the/|'any|such|these|those'|@yourC)""")

        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()

        #OutputRules("concise")
        word = _RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = _RuleList[1].Tokens[0].word
        self.assertFalse(":" in word)
        word = _RuleList[2].Tokens[1].word
        self.assertFalse(":" in word)

    def test_Actions_SimppleModal(self):
        ResetRules()

        InsertRuleInList(
            """negSimpleModal ==
            <( 	MD 		| "d" 	|  ("do")  	)  >;
                 """)

        InsertRuleInList(
            """Not_That_VTH == [JS|CM|Sconj|Bqut] ^[0 not:V] ^that[0 that:^.X JS2] R* [CL:^that.X fact-]
                 """)

        InsertRuleInList("""
        VWHSS_how3 ==
        ^[ADJSUBCAT:AWHSS AP] [PP F=to human ^PP]? advP? [IN:^Wh.X] ^wh[0 what|which|how|how_many|how_much:^.X Gone] [NP F=!DT:^.O2 wh JS2] [infinitive:^.ObjV]?
        """)

        InsertRuleInList("""NP_CM_VBN ==
        ^[NP2|DE2 !pro !that !date|durR|time|percent:^V.O2] [CM:Done] advP* ^V[enVG VNP|VNPPP Kid Obj:^.X] [PP|RP|DE|R]* ([CM:Done]|[COLN|JM])""")
        ExpandRuleWildCard()
        ExpandParenthesisAndOrBlock()
        ExpandRuleWildCard()

        #OutputRules("concise")
        self.assertTrue(len(_RuleList) >= 3)

    def test_SeparateRules(self):
        a, b = SeparateRules("""good""")
        self.assertEqual(a, "good")
        self.assertFalse(b)

        a, b = SeparateRules("""good
        second line
        third line""")
        self.assertEqual(a, "good")
        self.assertTrue(b)

        a, b = SeparateRules("""{good
        second line
        third line}""")
        self.assertEqual(a, """{good
second line
third line}""")
        self.assertFalse(b)

        a, b = SeparateRules("""{good
        second line
        third line};""")
        self.assertEqual(a, """{good
second line
third line};""")
        self.assertFalse(b)

        a, b = SeparateRules("""
        {good line
        second line
        third line};
        //unittest: test1
        //unittest: test 2
        """)
        self.assertFalse(b)

    def test_PreProcess_CheckFeatures(self):
        ResetRules()

        InsertRuleInList(
            """features ==
            'a|b|c';
                 """)

        PreProcess_CheckFeatures()
        self.assertEqual(len(_RuleList), 1)
        word = _RuleList[0].Tokens[0].word
        self.assertEqual(word, "['a'|'b'|'c']")

        InsertRuleInList(
            """features2 ==
            [notfeature:xx];
                 """)
        #OutputRules()
        PreProcess_CheckFeatures()
        self.assertEqual(len(_RuleList), 2)
        word = _RuleList[1].Tokens[0].word
        self.assertEqual(word, "['notfeature']")

        InsertRuleInList(
            """features3 ==
            notfeature|'a'|notfeature2;
                 """)

        PreProcess_CheckFeatures()
        OutputRules()
        self.assertEqual(len(_RuleList), 3)
        word = _RuleList[2].Tokens[0].word
        self.assertEqual(word, "['notfeature'|'a'|'notfeature2']")

    def test_Random(self):
        ResetRules()
        FeatureOntology.LoadFullFeatureList('../../../fsa/extra/featurelist.txt')

        InsertRuleInList("""
        Conj_NP2 == 
{

 	[!NN|plural]|[date|measure|dur]|[RP|PP]
};
   """)
        PreProcess_CheckFeatures()
        OutputRules()