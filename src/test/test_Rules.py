
import unittest
from ..Rules import *
from ..Rules import _RuleList

class RuleTest(unittest.TestCase):
    def test_Tokenization(self):
        tokenlist = Tokenize("[a] [b]")
        self.assertEqual(tokenlist[0].word, '[a]')
    def test_SetRule_number(self):
        r = Rule()
        r.SetRule("a==[a]4 [b]* [c]*7 [d]?")
        self.assertEqual(r.Tokens[0].repeat[1], 4)
        self.assertEqual(r.Tokens[1].repeat[1], 3)
        self.assertEqual(r.Tokens[2].repeat[1], 7)
        self.assertEqual(r.Tokens[3].repeat[1], 1)
        self.assertEqual(r.Tokens[3].repeat[0], 0)
    def test_tokenspace(self):
        r = Rule()
        r.SetRule("b==[a b? c:d e]")
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
        self.assertEqual(r.oneliner()[-46:], "rule4words == {[word]_[word]_[word]_[word]_};\n")
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
        print(r)

    # def test_Macro(self):
    #     r = Rule()
    #     r.SetRule("rule==@andC")
    #     s = ProcessMacro("a @andC")
    #     self.assertEqual(s, "a ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"])")
    #
    #     s = ProcessMacro("a @andC @andC")
    #     self.assertEqual(s, "a ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"]) ([0 \"and|or|&amp;|as_well_as|\/|and\/or\"])")

    def test_Expand(self):
        r = Rule()
        self.assertEqual(len(_RuleList), 0)
        InsertRuleInList("aaa==[NR] [PP]?")
        self.assertEqual(len(_RuleList), 1)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 2)
        InsertRuleInList("bbb==[NR]? [PP]?")
        self.assertEqual(len(_RuleList), 3)
        ExpandRuleWildCard()
        self.assertEqual(len(_RuleList), 6)

        OutputRules()