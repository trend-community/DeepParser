import logging, sys, re, jsonpickle
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
from flask import Flask, request

app = Flask(__name__)

@app.route("/LoadFullFeatureList/<ListPath>")
def LoadFullFeatureList(ListPath):
    FeatureOntology.LoadFullFeatureList(ListPath)
    return str(True)


@app.route("/LoadFeatureOntology/<OntologyPath>")
def LoadFeatureOntology(OntologyPath):
    FeatureOntology.LoadFeatureOntology(OntologyPath)
    return str(True)

@app.route("/LoadLexicon/<LexiconPath>")
def LoadLexicon(LexiconPath):
    Lexicon.LoadLexicon(LexiconPath)
    return str(True)


@app.route("/LoadRules/<RulePath>")
def LoadRules(RulePath):
    Rules.LoadRules(RulePath)
    return str(True)


@app.route("/PostProcessRules")
def PostProcessRules():
    Rules.ExpandRuleWildCard()
    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    Rules.OutputRuleFiles("../temp/")
    return str(True)


@app.route("/LoadCommon/<LoadCommonRules>")
def LoadCommon(LoadCommonRules=False):
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    Lexicon.LoadLexicon('../../fsa/X/lexX.txt')
    Lexicon.LoadLexicon('../../fsa/X/brandX.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiom4X.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiomX.txt')
    Lexicon.LoadLexicon('../../fsa/X/locX.txt')
    Lexicon.LoadLexicon('../../fsa/X/perX.txt')

    logging.warning("Parameter is:" + str(LoadCommonRules))
    if LoadCommonRules:
        Rules.LoadRules("../../fsa/X/0defLexX.txt")
        Rules.LoadRules("../temp/800VGy.txt.compiled")
        #Rules.LoadRules("../temp/900NPy.xml.compiled")
        #Rules.LoadRules("../temp/1800VPy.xml.compiled")
        #Rules.LoadRules("../../fsa/Y/900NPy.xml")
        #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
        # Rules.LoadRules("../../fsa/Y/1test_rules.txt")
        Rules.LoadRules("../../fsa/X/mainX2.txt")
        Rules.LoadRules("../../fsa/X/ruleLexiconX.txt")
        Rules.LoadRules("../../fsa/Y/100y.txt")
        # Rules.LoadRules("../../fsa/X/180NPx.txt")
        # Rules.LoadRules("../../fsa/X/270VPx.txt")

        PostProcessRules()
    return str(True)


@app.route("/SearchLexicon/<word>")
def SearchLexicon(word):
    return jsonpickle.encode(Lexicon.SearchLexicon(word))


@app.route("/GetFeatureID/<word>")
def GetFeatureID(word):
    return jsonpickle.encode(FeatureOntology.GetFeatureID(word))

@app.route("/GetFeatureName/<FeatureID>")
def GetFeatureName(FeatureID):
    return jsonpickle.encode(FeatureOntology.GetFeatureName(int(FeatureID)))


@app.route("/Tokenize", methods=['POST'])
def Tokenize_en():
    Sentence = request.data.decode("utf-8")
    return jsonpickle.encode(Tokenization.Tokenize(Sentence))


@app.route("/ApplyLexicon", methods=['POST'])
def ApplyLexicon():
    node = jsonpickle.decode(request.data)
    Lexicon.ApplyLexicon(node)
    return jsonpickle.encode(node)


@app.route("/ApplyLexiconToNodes", methods=['POST'])
def ApplyLexiconToNodes():
    nodes = jsonpickle.decode(request.data)
    for node in nodes:
        Lexicon.ApplyLexicon(node)
    return jsonpickle.encode(nodes)


# Not recommend to use. It is not a good concept.
# @app.route("/TokenizeAndApplyLexicon", methods=['POST'])
# def TokenizeAndApplyLexicon():
#     Sentence = request.data.decode("utf-8")
#     nodes = Tokenization.Tokenize(Sentence)
#     for node in nodes:
#         FeatureOntology.ApplyLexicon(node)
#     return jsonpickle.encode(nodes)


@app.route("/MatchAndApplyRules", methods=['POST'])
def MatchAndApplyRules():
    nodes = jsonpickle.decode(request.data)
    WinningRules, Nodes = ProcessSentence.MatchAndApplyRules(nodes)
    return jsonpickle.encode([WinningRules, Nodes])


@app.route("/OutputRules/<Mode>")
def OutputRules(Mode="concise"):
    return Rules.OutputRules(Mode)


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    LoadCommon(LoadCommonRules=True)
    app.run(port=5001, debug=False)
