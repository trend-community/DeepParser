import logging, sys, re, jsonpickle, os, json
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
from flask import Flask, request, send_file
from flask_cache import Cache
import viterbi1
import argparse
import utils, Graphviz

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



# Not recommend to use. It is not a good concept.
# @app.route("/TokenizeAndApplyLexicon", methods=['POST'])
# def TokenizeAndApplyLexicon():
#     Sentence = request.data.decode("utf-8")
#     nodes = Tokenization.Tokenize(Sentence)
#     for node in nodes:
#         FeatureOntology.ApplyLexicon(node)
#     return jsonpickle.encode(nodes)




#Following the instruction in pipelineX.txt
@app.route("/MultiLevelSegmentation/<everything:Sentence>")
def MultiLevelSegmentation(Sentence):
    if len(Sentence) > 2 and Sentence.startswith("\"") and Sentence.endswith("\""):
        Sentence = Sentence[1:-1]
    # else:
    #     return "Quote your sentence in double quotes please"
    nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence)
    #return  str(nodes)
    #return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
    return nodes.root().CleanOutput().toJSON()


#Following the instruction in pipelineX.txt
@app.route("/LexicalAnalyze")
def LexicalAnalyze():
    Sentence = request.args.get('Sentence')
    Type = request.args.get('Type')
    if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
        Sentence = Sentence[1:-1]
    # else:
    #     return "Quote your sentence in double quotes please"
    nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence)
    #return  str(nodes)
    #return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
    logging.info("Type=" + str(Type))
    if Type == "simple":
        return utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
    elif Type == "simplefeature":
        return utils.OutputStringTokens_oneliner(nodes, NoFeature=False)
    elif Type == "json2":
        return nodes.root().CleanOutput_FeatureLeave().toJSON()
    elif Type == "parsetree":
        svgfilelocation = Graphviz.showGraph(nodes.root().CleanOutput().toJSON())
        return send_file(svgfilelocation, mimetype='image/gif')
    else:
        return nodes.root().CleanOutput().toJSON()



# @app.route("/OutputWinningRules")
# @app.cache.cached(timeout=10)  # cache this view for 10 seconds
# def OutputWinningRules():
#     return ProcessSentence.OutputWinningRules()

@app.route("/QuerySegment/<Sentence>")
def QuerySegment(Sentence):

    norm = viterbi1.normalize(Sentence)
    return ''.join(viterbi1.viterbi1(norm, len(norm)))

def init(querydict = "../data/g1.words.P"):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)


    if querydict.startswith("."):
        querydict = os.path.join(os.path.dirname(os.path.realpath(__file__)),  querydict)
    viterbi1.LoadDictFromPickle(querydict)

    ProcessSentence.LoadCommon()


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
