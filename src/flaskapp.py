import urllib

from werkzeug.datastructures import MultiDict

import ProcessSentence
import Graphviz
import Rules
import utils
import Lexicon
from utils import *
from datetime import datetime

import logging, jsonpickle, os

from flask import Flask, render_template, request
app = Flask(__name__)

charttemplate = ''
KeyWhiteList = []
MAXQUERYSENTENCELENGTH = 100


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/FeatureOntology')
def ShowFeatureOntology():
    return render_template('chart.template.html', DIGDATA=FeatureOntology.OutputFeatureOntologyGraph())


@app.route('/Reload/<ReloadTask>')
def Reload( ReloadTask):
    LoadFrom = ParserConfig.get("main", "loadfrom").lower()
    if LoadFrom == "dump":
        Reply = "The system is loaded from dump as in config.ini. It does not support online reload."
        return Reply

    utils.InitDB()
    PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
    # XLocation = os.path.dirname(PipeLineLocation)     # need to get relative location, not the absolute location.
    XLocation, _ = os.path.split(PipeLineLocation)
    XLocation += "/"

    Reply = "Lexicon/Rule/Pipeline:"
    systemfileolderthanDB = True  # ProcessSentence.SystemFileOlderThanDB(XLocation)
    # when db is disabled, there is no record of system files. then the rule files are forced to reload
    # because we don't know whether the systems are modified or not.
    # Let's disable this functionality for now. Assume the system files are not modified. Not to be reload dynamically.

    if ReloadTask.lower() == "lexicon":
        logging.info("Start loading lexicon...")
        logging.warning("Need debugging")
        Lexicon.ResetAllLexicons()
        # ProcessSentence.LoadCommonLexicon(XLocation)
        for action in ProcessSentence.PipeLine:
            ProcessSentence.Pipeline_LoadLexicon(XLocation, action)

        Lexicon.LoadSegmentLexicon()
        Lexicon.ApplyStemFeatures()
        Reply += f"Reloaded lexicon at {str(datetime.now())}"

    if ReloadTask.lower() == "rule":
        logging.info("Start loading rules...")
        # Rules.ResetAllRules()
        # ProcessSentence.WinningRuleDict.clear()
        # assume system files are not to be reload dynamically.
        # GlobalmacroLocation = os.path.join(XLocation, "../Y/GlobalMacro.txt")
        # Rules.LoadGlobalMacro(GlobalmacroLocation)

        for action in ProcessSentence.PipeLine:
            ProcessSentence.Pipeline_LoadRule(XLocation, action)

        Reply += f"Reloaded rules at {str(datetime.now())}. Please note that the .xxxxxx. kind of rules is messed up during reload."

    if ReloadTask.lower() == "pipeline":
        logging.info("Start loading pipeline...")
        Rules.ResetAllRules()
        ProcessSentence.PipeLine = []
        ProcessSentence.LoadCommon()
        Reply += f"Reloaded pipeline at {str(datetime.now())}"

    # ProcessSentence.UpdateSystemFileFromDB(XLocation)

    utils.CloseDB(utils.DBCon)
    return Reply


class CaseInsensitiveDict(MultiDict):
    def __init__(self, _copy):
        super().__init__()
        for key in _copy:
            if isinstance(key, str):
                self[key.lower()] = _copy[key]
            else:
                self[key] = _copy[key]


def RequestQueries(uri):    # sample: 'REQUEST_URI': '/LexicalAnalyze?Key=Lsdif238fj&Debug=True&Type=parset...'
    _, kvstring = uri.split("?", 1)
    try:
        q = kvstring.split("&")
        queries = {}
        for qc in q:
            try:
                key, quotedvalue = qc.split("=", 1)
            except ValueError as e:
                logging.info("Input query: somehow the & and = sign are not paired. may be part of the sentence.")
                continue
            queries[key] = urllib.parse.unquote(quotedvalue)

        if "Sentence" in queries:  # get the Sentence from original link.query to avoid "&/=" sign
            query = urllib.parse.unquote(kvstring)
            StartLocation = query.find("Sentence=") + len("Sentence=")
            if query[StartLocation] in "[\"“”]":
                # from the first quote to the last quote
                EndLocation1 = query.rfind("\"", StartLocation + 1)
                EndLocation2 = query.rfind("“", StartLocation + 1)
                EndLocation3 = query.rfind("”", StartLocation + 1)
                EndLocation = max(EndLocation1, EndLocation2, EndLocation3)
                if EndLocation > 0:
                    queries["Sentence"] = query[StartLocation + 1:EndLocation]

    except ValueError as e:
        logging.error("Input query is not correct: {}\n{}".format(uri, e))
        return None

    return queries


@app.route('/LexicalAnalyze', methods=['GET', 'POST'])
def LexicalAnalyze():
    queries = CaseInsensitiveDict(request.args)
    if request.method == "GET" and "Sentence" in request.url:  # get the Sentence from original link.query to avoid "&/=" sign
        query = urllib.parse.unquote(request.url)
        StartLocation = query.find("Sentence=") + len("Sentence=")
        if query[StartLocation] in "[\"“”]":
            # from the first quote to the last quote
            EndLocation1 = query.rfind("\"", StartLocation + 1)
            EndLocation2 = query.rfind("“", StartLocation + 1)
            EndLocation3 = query.rfind("”", StartLocation + 1)
            EndLocation = max(EndLocation1, EndLocation2, EndLocation3)
            if EndLocation > 0:
                queries["sentence"] = query[StartLocation + 1:EndLocation]
        for x in ["DocumentClass", "ParagraphClass", "SentenceClass"]:  # These 3 variables are case sensitive
            if x in request.args and request.args[x]:
                utils.GlobalVariables[x] = request.args[x]
    elif request.method == "POST":
        queries = CaseInsensitiveDict(request.form)
        for x in ["DocumentClass", "ParagraphClass", "SentenceClass"]:  # These 3 variables are case sensitive
            if x in request.form and request.form[x]:
                utils.GlobalVariables[x] = request.form[x]

    if not queries:     # when it is rewrite, the information is in REQUEST_URI
        queries = RequestQueries(request.environ['REQUEST_URI'])
        for x in ["DocumentClass", "ParagraphClass", "SentenceClass"]:  # These 3 variables are case sensitive
            if x in queries and queries[x]:
                utils.GlobalVariables[x] = queries[x]
        queries = CaseInsensitiveDict(queries)

    Sentence = queries["sentence"][:MAXQUERYSENTENCELENGTH]
    outputtype = queries.get("type", default="json", type=str).lower()
    schema = queries.get("schema", default="full", type=str).lower()
    action = queries.get("action", default="", type=str).lower()

    if "resetglobalvalue" in queries:
        if queries["resetglobalvalue"] == "true":
            utils.ResetGlobalVariables()
    else:
        utils.ResetGlobalVariables()  # if not present, then also reset (traditional way)

    if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
        Sentence = Sentence[1:-1]
    # else:
    #     return "Quote your sentence in double quotes please"
    logging.info("[START] [{}]\t{}".format(queries["key"], Sentence))
    starttime = current_milli_time()

    nodes, dag, winningrules = ProcessSentence.LexicalAnalyze(Sentence, schema)
    # return  str(nodes)
    # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
    Debug = "debug" in queries
    if nodes:
        if outputtype == "segmentation":
            output_type = "text/plain;"
            output_text = utils.OutputStringTokensSegment_oneliner(nodes)
        elif outputtype == "keyword":
            output_type = "text/plain;"
            output_text = utils.OutputStringTokensKeyword_oneliner(dag)
        elif outputtype == "simple":
            output_type = "text/plain;"
            output_text = utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
            # if len(dag.nodes) > 0:
            #     output_text += "\n" + dag.digraph(Type)

        elif outputtype == "simpleEx":
            output_type = "text/plain;"
            output_text = utils.OutputStringTokens_oneliner_ex(nodes)
            # if len(dag.nodes) > 0:
            #     output_text += "\n" + dag.digraph(Type)
        elif outputtype == "simpleMerge":
            output_type = "text/plain;"
            output_text = utils.OutputStringTokens_oneliner_merge(nodes)
        elif outputtype == "json2":
            output_type = "text/html;"
            output_text = nodes.root().CleanOutput_FeatureLeave().toJSON()
        elif outputtype == 'graph':
            output_type = "text/plain;"
            output_text = dag.digraph(outputtype)
        elif outputtype == "graphjson":
            output_type = "Application/json;"
            output_text = dag.digraph(outputtype)
        elif outputtype == 'simplegraph':
            output_type = "text/plain;"
            output_text = dag.digraph(outputtype)
        elif outputtype == 'sentiment':
            output_type = 'text/plain;'
            output_text = utils.OutputStringTokens_onelinerSA(dag)
        elif outputtype == 'sentimenttext':
            output_type = 'text/plain;'
            output_text = utils.OutputStringTokens_onelinerSAtext(dag)
        elif outputtype == 'QA':
            output_type = 'text/plain;'
            output_text = utils.OutputStringTokens_onelinerQA(dag)
        elif outputtype == "parsetree":
            # output_type = "text/html;"
            if action == "headdown":
                output_json = nodes.root().CleanOutput_Propagate().toJSON()
            else:
                output_json = nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

            winningrulestring = ""
            if Debug:
                if winningrules:
                    for rule in winningrules:
                        winningrulestring += winningrules[rule] + "\n"

            logging.info("[COMPLETE] [{}]\t{}".format(queries["key"], Sentence))
            logging.info("[TIME] {}".format(current_milli_time() - starttime))
            return render_template('chart.template.html', DIGDATA=dag.digraph(),
                                   TREEDATA= Graphviz.orgChart(output_json, Debug=Debug),
                                   EXTRADATA=winningrulestring,
                                   pnorm=OutputExtraInfo(Debug, dag))

        elif outputtype == "pnorm":
            output_type = "Application/json;"
            output_text = dag.pnorm()
        else:
            output_type = "Application/json;"
            if action == "headdown":
                output_text = nodes.root().CleanOutput_Propagate().toJSON()
            else:
                output_text = nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

        try:
            logging.info("[COMPLETE] [{}]\t{}".format(queries["key"], Sentence))
            logging.info("[TIME] {}".format(current_milli_time() - starttime))
            response = app.response_class(response=output_text,
                                          mimetype=output_type)
            return response
        except Exception as e:
            logging.error(e)
            return "Error in processing", 500
            #self.send_error(500, "Error in processing")
            # self.ReturnBlank()
    else:
        logging.error("nodes is blank")
        return ""


def OutputExtraInfo(isDebug, dag):
    globalinfo1 = ""
    for k in utils.GlobalVariables:
        globalinfo1 += k + " = " + utils.GlobalVariables[k] + "\n"
    if globalinfo1:
        globalinfo1 = "\nGlobal Variables:\n" + globalinfo1

    globalinfo2 = ""
    for k in Lexicon._LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT]:
        globalinfo2 += "[" + k.text + "]\n"
    if globalinfo2:
        globalinfo2 = "\nDocument Lexicon:\n" + globalinfo2

    globalinfo3 = dag.OutputSpecialLinks()
    if globalinfo3:
        globalinfo3 = "\nSpecial Links:\n" + globalinfo3

    globalinfo = dag.pnorm_text()
    if isDebug:
        globalinfo += globalinfo1
        globalinfo +=  globalinfo2
        globalinfo += globalinfo3

    return globalinfo


@app.route('/DocumentAnalyze', methods=['POST'])
def DocumentAnalyze():
    queries = CaseInsensitiveDict(request.form)

    outputtype = queries.get("type", default="json", type=str).lower()
    schema = queries.get("schema", default="full", type=str).lower()
    Document = queries["document"]

    if "resetglobalvalue" in queries:
        if queries["resetglobalvalue"] == "true":
            utils.ResetGlobalVariables()
    else:
        utils.ResetGlobalVariables()  # if not present, then also reset (traditional way)

    for x in ["DocumentClass", "ParagraphClass", "SentenceClass"]:  # These 3 variables are case sensitive
        if x in request.form and request.form[x]:
            utils.GlobalVariables[x] = request.form[x]

    Newline = queries.get("newline", default="", type=str)
    TransferLinebreak = queries.get("transferlinebreak", default="transfer", type=str)
    if 'debug' in queries:
        Debug = True
    else:
        Debug = False
    logging.info("[START] [{}]\t{}...".format(queries["key"], Document[:10]))
    starttime = current_milli_time()

    dag, winningrules = ProcessSentence.DocumentAnalyze(Document, schema, Newline, TransferLinebreak)

    winningrulestring = ''
    if winningrules:
        for rule in winningrules:
            winningrulestring += winningrules[rule] + "\n"

    if outputtype == "pnorm":
        output_type = "Application/json;"
        output_text = dag.pnorm()
    elif outputtype == "graphjson":
        output_type = "Application/json;"
        output_text = dag.digraph(outputtype)
    elif outputtype == "graph":
        output_type = "text/plain;"
        output_text = dag.digraph(outputtype)
    else:  # show the graph part of parsetree
        logging.info("[COMPLETE] [{}]\t{}".format(queries["key"], Document[:10]))
        logging.info("[TIME] {}".format(current_milli_time() - starttime))
        return render_template('chart.template.html', DIGDATA=dag.digraph(),
                               EXTRADATA=winningrulestring,
                               pnorm=OutputExtraInfo(Debug, dag))

    try:
        logging.info("[COMPLETE] [{}]\t{}...".format(queries["key"], Document[:20]))
        logging.info("[TIME] {}".format(current_milli_time() - starttime))
        response = app.response_class(response=output_text,
                                      mimetype=output_type)  # or .assets and content_type ?
        return response

    except Exception as e:
        logging.error(e)
        return "Error in processing", 500

# @app.before_first_request
def init():
    if hasattr(init, "initiated"):
        logging.info("Already initiated. ignore flaskapp.init()")
        return
    init.initiated = True       # make this as a singleton

    global charttemplate, KeyWhiteList
    global MAXQUERYSENTENCELENGTH

    if utils.ParserConfig.has_option("website", "maxquerysentencelength"):
        MAXQUERYSENTENCELENGTH = int(utils.ParserConfig.get("website", "maxquerysentencelength"))

    LogLevel = ""
    if utils.ParserConfig.has_option("website", "LogLevel"):
        LogLevel = utils.ParserConfig.get("website", "LogLevel").lower()
    if LogLevel == "debug":
        loglevel = logging.DEBUG
    elif LogLevel == "warning":
        loglevel = logging.WARNING
    else:
        loglevel = logging.INFO

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=loglevel, format='%(asctime)s [%(levelname)s] %(message)s')

    jsonpickle.set_encoder_options('json', ensure_ascii=False)
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "chart.template.html")) as templatefile:
        charttemplate = templatefile.read()

    ProcessSentence.LoadCommon()
    # FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt') # for debug purpose

    KeyWhiteList = [x.split("#", 1)[0].strip() for x in utils.ParserConfig.get("main", "keylist").splitlines() if x]
    logging.warning("Completed init")


init()

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=int(utils.ParserConfig.get("website", "port")))
