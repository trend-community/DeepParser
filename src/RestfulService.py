import logging, sys, re, jsonpickle, os
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
from flask import Flask, request
from flask_cache import Cache
import viterbi1
import argparse
import utils

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
app.cache = Cache(app)

# for processing leading slash as in:
#  https://stackoverflow.com/questions/24000729/flask-route-using-path-with-leading-slash#24001029
from werkzeug.routing import PathConverter

class EverythingConverter(PathConverter):
    regex = '.*?'

app.url_map.converters['everything'] = EverythingConverter


# import singleton
# me = singleton.SingleInstance()


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

@app.route("/GetFeatureList1")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def GetFeatureList1():
    return jsonpickle.encode({ID:f for f,ID in FeatureOntology._FeatureDict.items()})


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
@app.route("/MultiLevelSegmentation/<everything:Sentence>")
@app.cache.cached(timeout=10)  # cache this view for 10 seconds
def MultiLevelSegmentation(Sentence):
    nodes = ProcessSentence.MultiLevelSegmentation(Sentence)
    return jsonpickle.encode(nodes)


# @app.route("/OutputWinningRules")
# @app.cache.cached(timeout=10)  # cache this view for 10 seconds
# def OutputWinningRules():
#     return ProcessSentence.OutputWinningRules()

@app.route("/QuerySegment/<sentence>")
def QuerySegment(sentence):
    norm = viterbi1.normalize(sentence)
    return ''.join(viterbi1.viterbi1(norm, len(norm)))

def init(querydict = "../data/g1.words.P"):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)


    if querydict.startswith("."):
        querydict = os.path.join(os.path.dirname(os.path.realpath(__file__)),  querydict)
    viterbi1.LoadDictFromPickle(querydict)

    ProcessSentence.LoadCommon(LoadCommonRules=True)


init()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--thisport", default=5001, help="The port for this server")
    parser.add_argument("--querydict", default="../data/g1.words.P", help="The port for this server")
    # parser.add_argument("--segmentserviceport", default=8080, type=int, help="The port of the Jave Segmentation Server")
    # parser.add_argument("--segmentserverlink", default="http://localhost",
    #                     help="The link to the Jave Segmentation Server")
    args = parser.parse_args()

    # utils.url_ch = args.segmentserverlink + ":" + str(args.segmentserviceport)

    print("Running in port " + str(args.thisport))
    app.run(host="0.0.0.0", port=args.thisport, debug=False, threaded=True)
    #app.test_client().get('/')
