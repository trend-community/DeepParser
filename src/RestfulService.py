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

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "chart.template.html")) as templatefile:
    charttemplate = templatefile.read()


@app.route("/GetFeatureID/<word>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def GetFeatureID(word):
    return jsonpickle.encode(FeatureOntology.GetFeatureID(word))


@app.route("/GetFeatureName/<FeatureID>")
@app.cache.cached(timeout=3600)  # cache this view for 1 hour
def GetFeatureName(FeatureID):
    return jsonpickle.encode(FeatureOntology.GetFeatureName(int(FeatureID)))


@app.route("/gchart_loader.js")
def gchart_loader():
    return send_file('gchart_loader.js')


# Following the instruction in pipelineX.txt
@app.route("/LexicalAnalyze")
def LexicalAnalyze():
    Sentence = request.args.get('Sentence')
    Type = request.args.get('Type')
    Debug = request.args.get('Debug')
    if Debug:
        Debug = True
    else:
        Debug = False
    if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
        Sentence = Sentence[1:-1]
    # logging.error(Sentence)
    # else:
    #     return "Quote your sentence in double quotes please"

    nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence)
    # return  str(nodes)
    # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
    if nodes:
        try:
            # logging.info("Type=" + str(Type))
            if Type == "simple":
                return utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
            elif Type == "json2":
                return nodes.root().CleanOutput_FeatureLeave().toJSON()
            elif Type == "parsetree":
                orgdata = Graphviz.orgChart(nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON())
                chart = charttemplate.replace("[[[DATA]]]", str(orgdata))

                if Debug:
                    winningrulestring = ""
                    for rule in winningrules:
                        winningrulestring +=  winningrules[rule] + "\n"
                    chart = chart.replace("<!-- EXTRA -->", winningrulestring)
                return chart
            else:
                return nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()
        except Exception as e:
            logging.error(e)
            return ""
    else:
        logging.error("nodes is blank")
        return ""


# @app.route("/OutputWinningRules")
# @app.cache.cached(timeout=10)  # cache this view for 10 seconds
# def OutputWinningRules():
#     return ProcessSentence.OutputWinningRules()

@app.route("/QuerySegment/<Sentence>")
def QuerySegment(Sentence):
    norm = viterbi1.normalize(Sentence)
    return ''.join(viterbi1.viterbi1(norm, len(norm)))


def init():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)

    ProcessSentence.LoadCommon()


init()

if __name__ == "__main__":
    print("Running in port " + str(utils.ParserConfig.get("website", "port")))
    app.run(host="0.0.0.0", port=int(utils.ParserConfig.get("website", "port")), debug=False, threaded=True)
    # app.test_client().get('/')
