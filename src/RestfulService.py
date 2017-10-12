import logging, sys, re, jsonpickle
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
from flask import Flask, request
from flask_cache import Cache

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
app.cache = Cache(app)


import singleton
me = singleton.SingleInstance()


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


@app.route("/GetFeatureList")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def GetFeatureList():
    return jsonpickle.encode(FeatureOntology._FeatureDict)


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
@app.cache.cached(timeout=10)  # cache this view for 10 seconds
def MultiLevelSegmentation(Sentence):
    nodes = ProcessSentence.MultiLevelSegmentation(Sentence)
    return jsonpickle.encode(nodes)


# @app.route("/OutputWinningRules")
# @app.cache.cached(timeout=10)  # cache this view for 10 seconds
# def OutputWinningRules():
#     return ProcessSentence.OutputWinningRules()


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
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
