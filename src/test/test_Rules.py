
import unittest
from Rules import *
from Rules import _ExpandParenthesis, _ExpandOrBlock, _ProcessOrBlock
from Rules import  _CheckFeature_returnword, _ExpandRuleWildCard_List, _PreProcess_CheckFeaturesAndCompileChunk, _PreProcess_CompileHash
import FeatureOntology
dir_path = os.path.dirname(os.path.realpath(__file__))
FeatureOntology.LoadFeatureSet(dir_path + '/../../../fsa/Y/feature.txt')

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
        self.assertEqual(r.Tokens[0].word, "[0 a]")
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
        self.assertEqual(r.Tokens[0].word, '[0 a b? c]')
        self.assertEqual(r.Tokens[0].action, 'd e')
    def test_Rule(self):
        r = Rule()
        r.SetRule("""PassiveSimpleING == {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};""")
        self.assertEqual(r.Tokens[2].word, "[RB]")
    def test_twolines(self):
        r = Rule()
        r.SetRule("""rule4words=={[word] [word]
	[word] [word]};""")
        result = r.output("concise")[-46:] == "rule4words == {[word]_[word]_[word]_[word]_};\n" or \
            r.output("concise")[-46:] == "rule4words == {[word] [word] [word] [word] };\n"
        self.assertTrue(result)
    def test_pointer(self):
        r = Rule()
        r.SetRule("rule=={^[word] ^head[word]};")
        self.assertEqual(r.Tokens[0].pointer, "^")
        self.assertEqual(r.Tokens[1].pointer, "^head")
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
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""@andC == ([0 "and|or|&amp;|as_well_as|\/|and\/or"])""", rulegroup)
        s = ProcessMacro("a @andC", rulegroup.MacroDict)
        self.assertEqual(s, "a ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"])")

        s = ProcessMacro("a @andC @andC", rulegroup.MacroDict)
        self.assertEqual(s, "a ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"]) ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"])")

        InsertRuleInList("""#macro_with_parameter(1=$HAVE 2=$NEG, 3=$tm 4=$neg) ==
         <$HAVE $NEG [RB:^.R]? [VBN|Ved:VG perfect $tm $neg ]>""", rulegroup)
        s = ProcessMacro("""#macro_with_parameter(1=a 2=b, 3=c 4=d)""", rulegroup.MacroDict)
        self.assertEqual(s, "<a b [RB:^.R]? [VBN|Ved:VG perfect c d ]>")

        s = ProcessMacro("""#macro_with_parameter(1=a 2=NULL, 3=c 4)""", rulegroup.MacroDict)
        self.assertEqual(s, "<a  [RB:^.R]? [VBN|Ved:VG perfect c  ]>")

        s = ProcessMacro("""#macro_with_parameter(1="a|b" 2=NULL, 3=c 4)""", rulegroup.MacroDict)
        self.assertEqual(s, """<"a|b"  [RB:^.R]? [VBN|Ved:VG perfect c  ]>""")


        InsertRuleInList("""@modalV ==
	( 	MD // MD includes 'will|shall|shalt|would|can|could|should|must|may|might' etc.
		| "\'d|wil|mite|wanna|gotta" // we need escape character "\'d" because we reserve ' for STEM checking
		| ( ("do|does|did") 'have|seem|claim|appear|tend|want|wish|hope|desire|expect' "to" ) // they do appear to own it
	)
""", rulegroup)
        InsertRuleInList("""#simpleMpassive(1=$NEG, 2=$neg) ==
        <@modalV $NEG [RB:^.R]? "be" [RB:^.R]? [VBN|Ved: VG passive simple  modal $neg]> !NNS
            """, rulegroup)
        #InsertRuleInList("""simpleModalPassive == #simpleMpassive(1,2); """)

        #OutputRules()


    def test_Expand(self):

        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        self.assertEqual(len(rulegroup.RuleList), 0)
        InsertRuleInList("aaa==[NR] [PP]?", rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 1)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 2)
        InsertRuleInList("bbb==[JS]? [JM]?", rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 3)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 5)

        #OutputRules()

    def test_adjacentbracket(self):
        r = Rule()
        r.SetRule("rule == [ab][cd]")
        self.assertEqual(len(r.Tokens), 2)
        self.assertEqual(r.Tokens[1].word, "[cd]")

    def test_parenthsis_complicate(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})
        r = Rule()
        r.SetRule("rule_p == [JS2 !DT|PDT|VBN|pro] <([R:^V.R]? ^V[0 Ved:^.M] )? [R:^V2.R]? ^V2[0 Ved:^.M] [AP:^.M]*  [N !date:NP]>")
        self.assertEqual(len(r.Tokens), 6)
        if r.RuleName:
            rulegroup.RuleList.append(r)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 16)
        print("Before expand  parenthesis")
        #OutputRules()
        _ExpandParenthesis(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 16)
        print("Before expand rule, after parenthesis")
        #OutputRules()

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        print(" after expand rule again")
        #OutputRules()
        #self.assertEqual(len(rulegroup.RuleList), 24)

    def test_parenthsis(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})
        r = Rule()
        r.SetRule(
            "rule_p ==  ([R:^V.R]? ^V[0 Ved:^.M] )? ")
        self.assertEqual(len(r.Tokens), 1)
        if r.RuleName:
            rulegroup.RuleList.append(r)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 2)
        _ExpandParenthesis(rulegroup.RuleList)
        print("Start rules after expand parenthesis")
        #OutputRules()
        newr = rulegroup.RuleList[1]
        self.assertEqual(len(newr.Tokens), 2)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        print("Start rules after expand wild card again")
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 3)


    def test_not_parenthsis(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        r = Rule()
        r.SetRule(           "d == [!c4|(c1 !c3)] ")
        self.assertEqual(len(r.Tokens), 1)
        if r.RuleName:
            rulegroup.RuleList.append(r)

        r = Rule()
        r.SetRule(           "e == [!(c1 !c3)|c5] ")
        self.assertEqual(len(r.Tokens), 1)
        if r.RuleName:
            rulegroup.RuleList.append(r)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        print("Start rules after _ExpandRuleWildCard_List")
        print(OutputRules(rulegroup))
        _ExpandParenthesis(rulegroup.RuleList)
        print("Start rules after _ExpandParenthesis")
        print(OutputRules(rulegroup))
        _ExpandOrBlock(rulegroup.RuleList)
        print("Start rules after _ExpandOrBlock")
        print(OutputRules(rulegroup))
        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        print("Start rules after _PreProcess_CheckFeaturesAndCompileChunk")
        print(OutputRules(rulegroup))
        _PreProcess_CompileHash(rulegroup)
        print("Start rules after _PreProcess_CompileHash")
        print(OutputRules(rulegroup))
        self.assertEqual(len(rulegroup.RuleList), 4)

        newr = rulegroup.RuleList[0]
        self.assertEqual(newr.Tokens[0].word, "!c4  !c1")
        newr = rulegroup.RuleList[1]
        self.assertEqual(newr.Tokens[0].word, "!c4  c3")

        newr = rulegroup.RuleList[2]
        self.assertEqual(newr.Tokens[0].word, "!c1  !c5")
        newr = rulegroup.RuleList[3]
        self.assertEqual(newr.Tokens[0].word, "c3  !c5")


    def test_simpleNotAnd(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        r = Rule()
        r.SetRule(           "c == [!(c1 !c3)] ")
        self.assertEqual(len(r.Tokens), 1)
        if r.RuleName:
            rulegroup.RuleList.append(r)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        print("Start rules after _ExpandRuleWildCard_List")
        print(OutputRules(rulegroup))
        _ExpandParenthesis(rulegroup.RuleList)
        print("Start rules after _ExpandParenthesis")
        print(OutputRules(rulegroup))
        _ExpandOrBlock(rulegroup.RuleList)
        print("Start rules after _ExpandOrBlock")
        print(OutputRules(rulegroup))
        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        print("Start rules after _PreProcess_CheckFeaturesAndCompileChunk")
        print(OutputRules(rulegroup))
        _PreProcess_CompileHash(rulegroup)
        print("Start rules after _PreProcess_CompileHash")
        print(OutputRules(rulegroup))
        self.assertEqual(len(rulegroup.RuleList), 2)

        newr = rulegroup.RuleList[0]
        self.assertEqual(newr.Tokens[0].word, "!c1")
        newr = rulegroup.RuleList[1]
        self.assertEqual(newr.Tokens[0].word, "c3")

    def test_UnificationExtension(self):

        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        r = Rule()
        r.SetRule("e == [nN %F(per|animal|org):^.CN] [CC] [nN %F:NG++ H]")
        self.assertEqual(len(r.Tokens), 3)
        if r.RuleName:
            rulegroup.RuleList.append(r)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        print("Start rules after _ExpandRuleWildCard_List")
        print(OutputRules(rulegroup))
        _ExpandParenthesis(rulegroup.RuleList)
        print("Start rules after _ExpandParenthesis")
        print(OutputRules(rulegroup))
        _ExpandOrBlock(rulegroup.RuleList)
        print("Start rules after _ExpandOrBlock")
        print(OutputRules(rulegroup))
        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        print("Start rules after _PreProcess_CheckFeaturesAndCompileChunk")
        print(OutputRules(rulegroup))
        _PreProcess_CompileHash(rulegroup)
        print("Start rules after _PreProcess_CompileHash")
        print(OutputRules(rulegroup))
        self.assertEqual(len(rulegroup.RuleList), 3)

    def test_parenthsis_complicate_little(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})
        
        r = Rule()
        r.SetRule("rule_p == [JS2 !DT|PDT|VBN|pro] <([R:^V.R]? ^V[0 Ved:^.M] )? [R:^V2.R]>")
        self.assertEqual(len(r.Tokens), 3)
        if r.RuleName:
            rulegroup.RuleList.append(r)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 2)
        #print("Before expand  parenthesis")
        #OutputRules()
        _ExpandParenthesis(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 2)
        #print("Before expand rule, after parenthesis")
        #OutputRules()

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        #print(" after expand rule again")
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 3)

    def test_parenthsis_or(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""
@yourC ==
(
	[PRPP:^.M]
	| [one:^.M POS]

)
""", rulegroup)

        InsertRuleInList("DT_NN_VBG_NN2 == (/the/|'any|such|these|those'|@yourC) ", rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 1)
        #print("Before expand  parenthesis")
        #OutputRules()
        ExpandParenthesisAndOrBlock()

        #print("Before expand wild card rule, after parenthesis")
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 4)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        #print(" after expand wild card")
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 4)

    def test_parenthsis_or_pointer(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""
@yourC ==
( ^V[VB : ^.ModS] | ^W[要: ^.ModS] )
""", rulegroup)

        InsertRuleInList("DT_NN_VBG_NN2 == @yourC ", rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 1)
        # print("Before expand  parenthesis")
        # OutputRules()
        ExpandParenthesisAndOrBlock()

        # print("Before expand wild card rule, after parenthesis")
        # OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 2)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        # print(" after expand wild card")
        # OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 2)

    def test_specialrule(self):

        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""single_token_NP5 == <[proNN:NP]>""", rulegroup)
        r = rulegroup.RuleList[0]
        self.assertEqual(r.Tokens[1].word, "[proNN]")
        print(_CheckFeature_returnword(r.Tokens[1].word))

    def test_CheckFeature(self):
        FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""single_token_NP5 == < CD  分 之   [CD:fraction +++]>""", rulegroup)
        r = rulegroup.RuleList[0]
        self.assertEqual(r.Tokens[1].word, "CD")
        self.assertEqual(r.Tokens[2].word, "分")
        print(_CheckFeature_returnword(r.Tokens[2].word))

        InsertRuleInList("""30expert == < ['第-|前-' :AP pred pro succeed] [unit c1 !time:^.X]?>""", rulegroup)
        r = rulegroup.RuleList[1]
        r.Tokens[1].word = "[" + _CheckFeature_returnword(r.Tokens[1].word) + "]"
        self.assertEqual(r.Tokens[1].word, "['第-'|'前-']")

        InsertRuleInList("""30expert1 == < ['第-|前-' ordinal :AP pred pro succeed] [unit c1 !time:^.X]?>""", rulegroup)
        r = rulegroup.RuleList[2]
        print(_CheckFeature_returnword(r.Tokens[1].word))
        print(r.Tokens[1])

        r.Tokens[1].word = "[" + _CheckFeature_returnword(r.Tokens[1].word) + "]"
        print(r.Tokens[1])
        self.assertEqual(r.Tokens[1].word, "['第-'|'前-' ordinal]")


        InsertRuleInList("""30expert3 ==  ['and|or|of|that|which' | PP | CM]""", rulegroup)
        r = rulegroup.RuleList[3]
        #_CheckFeature(r.Tokens[0], 'new')
        print(r)
        print(r.Tokens[0])
        r.Tokens[0].word = _CheckFeature_returnword(r.Tokens[0].word)
        print(r.Tokens[0])

        InsertRuleInList("""2ExpertDomain ==  <[慢性:^.M] [!punc|xC|v:^.m] [sufferFrom: NP an term]> """, rulegroup)
        r = rulegroup.RuleList[4]
        # _CheckFeature(r.Tokens[0], 'new')
        print(r)
        print(r.Tokens[2])
        r.Tokens[2].word = "[" + _CheckFeature_returnword(r.Tokens[2].word) + "]"
        print(r.Tokens[2])
        self.assertEqual(r.Tokens[2].word, "[!punc !xC !v]")

    def test_ExpandOrBlock(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("abc == 'a' 'better|worse' 'gift'", rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 1)
        r = rulegroup.RuleList[0]
        self.assertEqual(len(r.Tokens), 3)

        _ExpandOrBlock(rulegroup.RuleList)
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 1)
        r = rulegroup.RuleList[0]
        self.assertEqual(len(r.Tokens), 3)


    def test_ExpandOrBlock2(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("abc == 'a' ('better|worse') 'gift'", rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 1)
        r = rulegroup.RuleList[0]
        self.assertEqual(len(r.Tokens), 3)

        _ExpandOrBlock(rulegroup.RuleList)
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 1)
        r = rulegroup.RuleList[0]
        self.assertEqual(len(r.Tokens), 3)

    def test_Parenthesis2(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""ADJ_NP6 == < (	('a') | ([PN:^.M]) ) >""", rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 1)

        _ExpandOrBlock(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 2)
        #OutputRules()

        _ExpandParenthesis(rulegroup.RuleList)
        #OutputRules()
        r = rulegroup.RuleList[0]
        self.assertEqual(len(r.Tokens), 2)
        #OutputRules()

    def test_ProcessOrBlock(self):
        whole, left, right = _ProcessOrBlock("['abc|def']", 5)
        self.assertEqual(whole, "abc|def")
        self.assertEqual(left, "abc")
        self.assertEqual(right, "def")

        # if left/right block is enclosed by (), and it is part of one token , then the () can be removed:
        whole, left, right = _ProcessOrBlock("(abc)|'def'|ghi", 5)
        self.assertEqual(whole, "(abc)|'def'")
        self.assertEqual(left, "abc")
        self.assertEqual(right, "'def'")

        whole, left, right = _ProcessOrBlock("(abc)|def|ghi", 5)
        self.assertEqual(whole, "(abc)|def")
        self.assertEqual(left, "abc")
        self.assertEqual(right, "def")

        whole, left, right = _ProcessOrBlock("/abc/|def|ghi", 5)
        self.assertEqual(whole, "/abc/|def")
        self.assertEqual(left, "/abc/")
        self.assertEqual(right, "def")

    def test_Parenthesis(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""simplePres == <[(VB)|VBZ:VG simple  pres]>;""", rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 1)

        _ExpandOrBlock(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 2)
        #OutputRules()

        ResetRules(rulegroup)
        InsertRuleInList("""abc ==
        <DT|PDT|( [PRPP:^.M] | [one:^.M POS])   [NE:NP]>
        """, rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 1)

        #_ExpandOrBlock(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        #OutputRules()
        self.assertEqual(len(rulegroup.RuleList), 4)

    def test_Actions_2(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""ACTION == ([pureDT:^.A] | [POS:^.M])""", rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        #OutputRules("concise")
        self.assertEqual(len(rulegroup.RuleList), 2)

    def test_Actions_3(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""ACTION == (([pureDT:^.A] | [POS:^.M]| [POS:^.M POS]))""", rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        _ExpandRuleWildCard_List(rulegroup.RuleList)

        #OutputRules("concise")
        self.assertEqual(len(rulegroup.RuleList), 4)

    def test_Actions_noDT(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""ACTION == [pureDT:^.A] | [POS:^.M]| [POS:^.M POS]""", rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        _ExpandRuleWildCard_List(rulegroup.RuleList)

        #OutputRules("concise")
        self.assertEqual(len(rulegroup.RuleList), 4)

    def test_Actions_NPP(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList(
            """precontext_IN_no_det_NP(Top) ==

                    ( [0 R b:^M.R] [0 a:^.M] )
                     [AP:^.M]

                 """, rulegroup)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        #OutputRules("concise")
        word = rulegroup.RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = rulegroup.RuleList[1].Tokens[0].word
        self.assertFalse(":" in word)
        #self.assertEqual(len(rulegroup.RuleList), 1)

    def test_Actions_parenthesis(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList(
            """precontext_IN_no_det_NP(Top) ==

                 <[NNP:NE] ['\(':^.X] [OOV:^.EQ] ['\)':^.X]> // Test: 卡雷尼奥.杜兰（Carrenoduran）

                 """, rulegroup)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        # OutputRules("concise")
        word = rulegroup.RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = rulegroup.RuleList[0].Tokens[1].word
        self.assertFalse(":" in word)
        # self.assertEqual(len(rulegroup.RuleList), 1)

    def test_Expanding_VNPAP2(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""
        VNPAP2 == ^[VNPAP !passive VG2] [NP !JS2:^.O ^V2.O2] RB? ^V2[AP OTHO:ingAdj]|[enAdj:^.C] infinitive [!passive:^.purposeR]?
        """  , rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)


        #OutputRules("concise")
        word = rulegroup.RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = rulegroup.RuleList[1].Tokens[0].word
        self.assertFalse(":" in word)

    def test_Expanding_Others(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        InsertRuleInList("""
        the_dollarsign(Top) == <[DT CURR:NP money]>
        """, rulegroup)

        InsertRuleInList("""
        the_blahblah_problem(Top) == <the [nv|NN:^.M] "up|down|in|out|away" ['time|trouble|difficulty|problem|experience|issue|topic|question|view|viewpoint':NP]>
        """, rulegroup)

        InsertRuleInList("""
        @yourC ==
        (
        	[PRPP:^.M]
        	| [one:^.M POS]

        )
        """, rulegroup)

        InsertRuleInList("""    DT_NN_VBG_NN2 ==
            '!with' (/the/|'any|such|these|those'|@yourC)""", rulegroup)

        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        OutputRules(rulegroup, "concise")
        word = rulegroup.RuleList[0].Tokens[0].word
        self.assertFalse(":" in word)
        word = rulegroup.RuleList[1].Tokens[0].word
        self.assertFalse(":" in word)
        word = rulegroup.RuleList[2].Tokens[1].word
        self.assertFalse(":" in word)

    def test_Actions_SimppleModal(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})


        InsertRuleInList(
            """negSimpleModal ==
            <( 	MD 		| "d" 	|  ("do")  	)  >;
                 """, rulegroup)

        InsertRuleInList(
            """Not_That_VTH == [JS|CM|Sconj|Bqut] ^[0 not:V] ^that[0 that:^.X JS2] R* [CL:^that.X fact-]
                 """, rulegroup)

        InsertRuleInList("""
        VWHSS_how3 ==
        ^[ADJSUBCAT:AWHSS AP] [PP F=to human ^PP]? advP? [IN:^Wh.X] ^wh[0 what|which|how|how_many|how_much:^.X Gone] [NP F=!DT:^.O2 wh JS2] [infinitive:^.ObjV]?
        """, rulegroup)

        InsertRuleInList("""NP_CM_VBN ==
        ^[NP2|DE2 !pro !that !date|durR|time|percent:^V.O2] [CM:Done] advP* ^V[enVG VNP|VNPPP Kid Obj:^.X] [PP|RP|DE|R]* ([CM:Done]|[COLN|JM])""", rulegroup)
        _ExpandRuleWildCard_List(rulegroup.RuleList)
        ExpandParenthesisAndOrBlock()
        _ExpandRuleWildCard_List(rulegroup.RuleList)

        #OutputRules("concise")
        self.assertTrue(len(rulegroup.RuleList) >= 3)

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
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})


        InsertRuleInList(
            """features ==
            'a|b|c';
                 """, rulegroup)

        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 3)
        word = rulegroup.RuleList[0].Tokens[0].word
        self.assertEqual(word, "[ 'a' ]")

        InsertRuleInList(
            """features2 ==
            [notfeature:xx];
                 """, rulegroup)
        #OutputRules()
        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        self.assertEqual(len(rulegroup.RuleList), 4)
        word = rulegroup.RuleList[3].Tokens[0].word
        self.assertEqual(word, "['notfeature']")

        InsertRuleInList(
            """features3 ==
            notfeature|'a'|notfeature2;
                 """, rulegroup)

        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        OutputRules(rulegroup)
        self.assertEqual(len(rulegroup.RuleList), 7)
        word = rulegroup.RuleList[6].Tokens[0].word
        self.assertEqual(word, "[ 'notfeature2' ]")

    def test_Random(self):
        rulegroup = RuleGroup("test")
        ResetRules(rulegroup)
        RuleGroupDict.update({rulegroup.FileName: rulegroup})

        FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

        InsertRuleInList("""
        Conj_NP2 == 
{

 	[!NN|plural]|[date|measure|dur]|[RP|PP]
};
   """, rulegroup)
        _PreProcess_CheckFeaturesAndCompileChunk(rulegroup.RuleList)
        OutputRules(rulegroup)

        origin = "this is \(, \), \\', \:, \= as origin"
        print(origin)
        new = origin.replace("\(", IMPOSSIBLESTRINGLP).replace("\)", IMPOSSIBLESTRINGRP).replace("\\'", IMPOSSIBLESTRINGSQ).replace("\:", IMPOSSIBLESTRINGCOLN).replace("\=", IMPOSSIBLESTRINGEQUAL)
        print(new)
        self.assertEqual(new, "this is @#$%@leftparenthesis@, @#$%@rightparenthesis@, @#$%@singlequote@, @#$%@coln@, @#$%@equal@ as origin")

    def test_OrBlocks(self):
        word = "[a b !'c|d|e'|f g]"
        orQuoteMatch = re.search("(')(\S*\|\S*?)\\1", word, re.DOTALL)
        if orQuoteMatch:
            print(orQuoteMatch.group(1))
            print(orQuoteMatch.group(2))
            self.assertEqual(orQuoteMatch.group(1), "'")
            expandedQuotes = ExpandQuotedOrs(orQuoteMatch.group(2), orQuoteMatch.group(1))
            word = word.replace(orQuoteMatch.group(2), expandedQuotes)
        self.assertEqual(word, "[a b !'c'|'d'|'e'|f g]")

        notOrMatch = re.search("!(\S*\|\S*)", word, re.DOTALL)
        if notOrMatch:
            expandAnd = ExpandNotOrTo(notOrMatch.group(1))
            word = word.replace(notOrMatch.group(1), expandAnd)
        self.assertEqual(word, "[a b !'c' !'d' !'e' !f g]")

        word = "[c1 !CD !time !'加'|'减'|'乘'|'除']"
        notOrMatch = re.search("!(\S*\|\S*)", word, re.DOTALL)
        if notOrMatch:
            self.assertEqual(notOrMatch.group(1), "'加'|'减'|'乘'|'除']")
            expandAnd = ExpandNotOrTo(notOrMatch.group(1))
            word = word.replace(notOrMatch.group(1), expandAnd)
        self.assertEqual(word, "[c1 !CD !time !'加' !'减' !'乘' !'除']")

    def test_ExtractParentSonActions(self):
        a, b = Rule.ExtractParentSonActions("a b -c NEW x y ")
        self.assertEqual(b, "-c NEW a b x y")

        a, b = Rule.ExtractParentSonActions("a b -c a++ b++ c++")
        self.assertEqual(b, "-c a b")
        a, b = Rule.ExtractParentSonActions("-a x++ y++ b")
        self.assertEqual(b, "-a b")

        a, b = Rule.ExtractParentSonActions(" x++ y++ ")
        self.assertEqual(b, "")

        a, b = Rule.ExtractParentSonActions(" x++ y++ #xby new ab #")
        self.assertEqual(b, " #xby new ab #")

        a, b = Rule.ExtractParentSonActions("a b -c a++ b++ c++ # this is good #")
        self.assertEqual(b, "-c a b # this is good #")

