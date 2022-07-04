import logging, sys, re, jsonpickle, os, json

import utils, Graphviz
import urllib, time
from flask import Flask, request, send_file


app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "chart.template.html")) as templatefile:
    charttemplate = templatefile.read()


@app.route("/gchart_loader.js")
def gchart_loader():
    return send_file('gchart_loader.js')


# Following the instruction in pipelineX.txt
@app.route("/LexicalAnalyze")
def LexicalAnalyze():
    Sentence = request.args.get('Sentence')
    Type = request.args.get('Type')

    if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
        Sentence = Sentence[1:-1]
    # logging.error(Sentence)
    # else:
    #     return "Quote your sentence in double quotes please"

    #nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence)

    # noinspection PyUnresolvedReferences
    url = BaseHTTPUrl + urllib.parse.quote_plus(Sentence.encode('utf8'))

    attempts = 0
    response = None
    while attempts < 5:
        try:
            # noinspection PyUnresolvedReferences
            response = urllib.request.urlopen(url, None)
            break
        except OSError:
            attempts += 1
            time.sleep(0.1 * attempts)
            logging.error("Failed ULR Request at try " + str(attempts))

    # return  str(nodes)
    # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
    if response:
        try:
            jsonoutput = response.read().decode("utf-8")
            # logging.info("Type=" + str(Type))
            if Type == "parsetree":
                orgdata = Graphviz.orgChart(jsonoutput)
                chart = charttemplate.replace("[[[DATA]]]", str(orgdata))
                return chart
            else:
                return jsonoutput
        except Exception as e:
            logging.error(e)
            return ""
    else:
        logging.error("nodes is blank")
        return ""


def init():
    global startport, BaseHTTPUrl
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)

    startport = int(utils.ParserConfig.get("website", "port"))
    BaseHTTPUrl = "http://127.0.0.1:" + str(startport+1) + "/"

    #ProcessSentence.LoadCommon()


init()

if __name__ == "__main__":
    print("Running in port " + str(startport))

    app.run(host="0.0.0.0", port=startport, debug=False, threaded=True)
    # app.test_client().get('/')
