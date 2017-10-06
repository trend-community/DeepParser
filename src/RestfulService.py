import logging, sys, re, jsonpickle
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
from flask import Flask, request
from flask_cache import Cache

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
app.cache = Cache(app)

#
# @app.route("/LoadFullFeatureList/<ListPath>")
# def LoadFullFeatureList(ListPath):
#     FeatureOntology.LoadFullFeatureList(ListPath)
#     return str(True)
#
#
# @app.route("/LoadFeatureOntology/<OntologyPath>")
# def LoadFeatureOntology(OntologyPath):
#     FeatureOntology.LoadFeatureOntology(OntologyPath)
#     return str(True)
#
#
# @app.route("/LoadLexicon/<LexiconPath>")
# def LoadLexicon(LexiconPath):
#     Lexicon.LoadLexicon(LexiconPath)
#     return str(True)
#
#
# @app.route("/LoadRules/<RulePath>")
# def LoadRules(RulePath):
#     Rules.LoadRules(RulePath)
#     return str(True)
#
#
# @app.route("/PostProcessRules")
# def PostProcessRules():
#     Rules.ExpandRuleWildCard()
#     Rules.ExpandParenthesisAndOrBlock()
#     Rules.ExpandRuleWildCard()
#
#     Rules.OutputRuleFiles("../temp/")
#     return str(True)
#
#
# @app.route("/LoadCommon/<LoadCommonRules>")
# def LoadCommon(LoadCommonRules=False):
#     FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
#     FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
#     Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
#     Lexicon.LoadLexicon('../../fsa/X/lexX.txt')
#     Lexicon.LoadLexicon('../../fsa/X/brandX.txt')
#     Lexicon.LoadLexicon('../../fsa/X/idiom4X.txt')
#     Lexicon.LoadLexicon('../../fsa/X/idiomX.txt')
#     Lexicon.LoadLexicon('../../fsa/X/locX.txt')
#     Lexicon.LoadLexicon('../../fsa/X/perX.txt')
#     Lexicon.LoadLexicon('../../fsa/X/defLexX.txt', forLookup=True)
#
#     logging.warning("Parameter is:" + str(LoadCommonRules))
#     if LoadCommonRules:
#         Rules.LoadRules("../../fsa/X/0defLexX.txt")
#         #Rules.LoadRules("../temp/800VGy.txt.compiled")
#         #Rules.LoadRules("../temp/900NPy.xml.compiled")
#         #Rules.LoadRules("../temp/1800VPy.xml.compiled")
#         #Rules.LoadRules("../../fsa/Y/900NPy.xml")
#         #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
#         # Rules.LoadRules("../../fsa/Y/1test_rules.txt")
#         Rules.LoadRules("../../fsa/X/mainX2.txt")
#         Rules.LoadRules("../../fsa/X/ruleLexiconX.txt")
#         #Rules.LoadRules("../../fsa/Y/100y.txt")
#         # Rules.LoadRules("../../fsa/X/180NPx.txt")
#         # Rules.LoadRules("../../fsa/X/270VPx.txt")
#
#         PostProcessRules()
#     return str(True)


@app.route("/SearchLexicon/<word>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def SearchLexicon(word):
    return jsonpickle.encode(Lexicon.SearchLexicon(word))


@app.route("/GetFeatureID/<word>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def GetFeatureID(word):
    return jsonpickle.encode(FeatureOntology.GetFeatureID(word))


@app.route("/GetFeatureName/<FeatureID>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def GetFeatureName(FeatureID):
    return jsonpickle.encode(FeatureOntology.GetFeatureName(int(FeatureID)))


@app.route("/Tokenize/<Sentence>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def Tokenize(Sentence):
    return jsonpickle.encode(Tokenization.Tokenize(Sentence))


@app.route("/ApplyLexicon", methods=['POST'])
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def ApplyLexicon():
    node = jsonpickle.decode(request.data)
    Lexicon.ApplyLexicon(node)
    return jsonpickle.encode(node)


@app.route("/ApplyLexiconToNodes", methods=['POST'])
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def ApplyLexiconToNodes():
    nodes = jsonpickle.decode(request.data)
    Lexicon.ApplyLexiconToNodes(nodes)
    return jsonpickle.encode(nodes)


# Not recommend to use. It is not a good concept.
# @app.route("/TokenizeAndApplyLexicon", methods=['POST'])
# def TokenizeAndApplyLexicon():
#     Sentence = request.data.decode("utf-8")
#     nodes = Tokenization.Tokenize(Sentence)
#     for node in nodes:
#         FeatureOntology.ApplyLexicon(node)
#     return jsonpickle.encode(nodes)


@app.route("/MatchAndApplyAllRules", methods=['POST'])
def MatchAndApplyAllRules():
    nodes = jsonpickle.decode(request.data)
    WinningRules = ProcessSentence.MatchAndApplyAllRules(nodes)
    return jsonpickle.encode([WinningRules, nodes])


@app.route("/MatchAndApplyRuleFile", methods=["POST"])
def MatchAndApplyRuleFile():
    nodes = jsonpickle.decode(request.form["nodes"])
    RuleFileName = jsonpickle.decode(request.form["rulefilename"])
    WinningRules = ProcessSentence.MatchAndApplyRuleFile(nodes, RuleFileName)
    return jsonpickle.encode([WinningRules, nodes])


@app.route("/OutputRules/<Mode>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def OutputRules(Mode="concise"):
    return Rules.OutputRules(Mode)


#Following the instruction in pipelineX.txt
@app.route("/MultiLevelSegmentation/<Sentence>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def MultiLevelSegmentation(Sentence):
    nodes = ProcessSentence.MultiLevelSegmentation(Sentence)
    return jsonpickle.encode(nodes)


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False);

    port = 5001
    if  len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python RestfulService.py [port number (default=5001)]")
            exit(0)

    ProcessSentence.LoadCommon(LoadCommonRules=True)
    print("Running in port " + str(port))
    app.run(port=port, debug=False)
    #app.test_client().get('/')
