import logging,  jsonpickle, os
import urllib
try:
    from socketserver import ThreadingMixIn, ForkingMixIn
except: #windows? ignore it.
    pass
import ProcessSentence, FeatureOntology
import Graphviz
#from Rules import ResetAllRules, LoadRules
import Rules
import utils
from datetime import datetime
from configparser import NoOptionError
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, HTTPServer
#from urlparse import urlparse, parse_qs
# query_components = parse_qs(urlparse(self.path).query)
# imsi = query_components["imsi"]
#from urlparse import urlparse
import time, argparse, traceback

current_milli_time = lambda: int(round(time.time() * 1000))

class ProcessSentence_Handler(BaseHTTPRequestHandler):
    def address_string(self):
        host, _ = self.client_address[:2]
        # old and slow way: return socket.getfqdn(host)
        return host

    def do_GET(self):
        # if hasattr(self.server, "active_children") and self.server.active_children:
        #     if len(self.server.active_children) > 10:
        #         logging.info("Server Active Children:" + str(len(self.server.active_children)) )
        #         logging.error("Server is too busy to serve!")
        #         self.send_error(504, "Server Busy")
        #         #self.ReturnBlank()
        #         return
        link = urllib.parse.urlparse(self.path)
        try:
            if link.path == '/LexicalAnalyze':
                try:
                    queries = dict(qc.split("=") for qc in link.query.split("&"))
                    self.LexicalAnalyze(queries)
                except ValueError:
                    logging.error("Input query is not correct: " + link.query)
                    self.send_error(500, "Link input error.")
                    return
            elif link.path.startswith('/GetFeatureID/'):
                self.GetFeatureID(link.path[14:])
            elif link.path.startswith('/GetFeatureName/'):
                self.GetFeatureName(int(link.path[16:]))
            elif link.path.startswith('/Reload'):
                self.Reload(link.path[7:])
            elif link.path in ['/gchart_loader.js', '/favicon.ico']:
                self.feed_file(link.path[1:])
            else:
                logging.error("Wrong link.")
                self.send_error(404)
        except Exception as e:
            logging.error("Unknown exception in do_GET")
            logging.error(str(e))
            traceback.print_exc()
            self.send_error(500, "Unknown exception")
            #self.ReturnBlank()
            return

    def LexicalAnalyze(self, queries):
        Sentence = urllib.parse.unquote(queries["Sentence"])[:MAXQUERYSENTENCELENGTH]
        Type = "json"
        if "Type" in queries:
            Type = queries["Type"]
        if "type" in queries:
            Type = queries["type"]
        schema = "full"
        if "Schema" in queries:
            schema = queries["Schema"].lower()
        if "schema" in queries:
            schema = queries["schema"].lower()

        action = ""
        if "Action" in queries:
            action = queries["Action"].lower()
        if "action" in queries:
            action = queries["action"].lower()

        if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
            Sentence = Sentence[1:-1]
        # else:
        #     return "Quote your sentence in double quotes please"
        logging.info("[START] " + Sentence)
        starttime = current_milli_time()

        nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence, schema)
        # return  str(nodes)
        # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
        Debug = "Debug" in queries
        if nodes:
            if  Type  == "simple":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
            elif  Type  == "simpleEx":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokens_oneliner_ex(nodes)
            elif  Type  == "simpleMerge":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokens_oneliner_merge(nodes)
            elif Type == "json2":
                output_type = "text/html;"
                output_text = nodes.root().CleanOutput_FeatureLeave().toJSON()
            elif Type == "parsetree":
                output_type = "text/html;"
                if action == "headdown":
                    output_json = nodes.root().CleanOutput_Propagate().toJSON()
                else:
                    output_json =nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

                orgdata = Graphviz.orgChart(output_json, Debug=Debug)
                chart = charttemplate.replace("[[[DATA]]]", str(orgdata))

                orgdata = Graphviz.digraph(nodes)
                chart = chart.replace("[[[DIGDATA]]]", str(orgdata))

                if Debug:
                    winningrulestring = ""
                    if winningrules:
                        for rule in winningrules:
                            winningrulestring +=  winningrules[rule] + "\n"
                        chart = chart.replace("<!-- EXTRA -->", winningrulestring)
                output_text = chart
            else:
                output_type = "Application/json;"
                if action == "headdown":
                    output_text = nodes.root().CleanOutput_Propagate().toJSON()
                else:
                    output_text =nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

            try:
                self.send_response(200)
                self.send_header('Content-type', output_type + " charset=utf-8")
                self.end_headers()
                self.wfile.write(output_text.encode("utf-8"))
                logging.info("[COMPLETE] " + Sentence)
                logging.info("[TIME] " + str(current_milli_time()-starttime))
            except Exception as e:
                logging.error(e)
                self.send_error(500, "Error in processing")
                #self.ReturnBlank()
        else:
            logging.error("nodes is blank")
            self.ReturnBlank()

    def ReturnBlank(self):
        self.send_response(200)
        self.send_header('Content-type', "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("".encode("utf-8"))

    def Reload(self, ReloadTask):
        XLocation = '../../fsa/X/'
        Reply = "Lexicon/Rule/All:"
        if ReloadTask.lower() in ("/lexicon", "/all"):
            logging.info("Start loading lexicon...")

            ProcessSentence.LoadCommonLexicon(XLocation)
            Reply += "Reloaded lexicon at " + str(datetime.now())
        if ReloadTask.lower() in ("/rule", "/all"):
            logging.info("Start loading rules...")
            Rules.ResetAllRules()
            ProcessSentence.WinningRuleDict.clear()
            # XLocation = '../../fsa/X/'
            # for action in ProcessSentence.PipeLine:
            #     if action.startswith("FSA"):
            #         Rulefile = action[3:].strip()
            #         Rulefile = os.path.join(XLocation, Rulefile)
            #         Rules.LoadRules(Rulefile)
            for action in ProcessSentence.PipeLine:
                if action.startswith("FSA"):
                    Rulefile = action[3:].strip()
                    Rules.LoadRules(XLocation, Rulefile)
            Reply += "Reloaded rules at " + str(datetime.now())

        self.send_response(200)
        self.send_header('Content-type', "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(Reply.encode("utf-8"))


    def GetFeatureID(self, word):
        self.send_response(200)
        self.send_header('Content-type', "Application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(jsonpickle.encode(FeatureOntology.GetFeatureID(word)).encode("utf-8"))


    def GetFeatureName(self, FeatureID):
        self.send_response(200)
        self.send_header('Content-type', "Application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(jsonpickle.encode(FeatureOntology.GetFeatureName(int(FeatureID))).encode("utf-8"))


    def feed_file(self, filepath):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), filepath)) as f:
            self.send_response(200)
            self.send_header('Content-type', "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f.read().encode("utf-8"))


def init():
    global charttemplate
    global MAXQUERYSENTENCELENGTH
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s][%(process)d : %(thread)d] %(message)s')
    
    jsonpickle.set_encoder_options('json', ensure_ascii=False)
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "chart.template.html")) as templatefile:
        charttemplate = templatefile.read()

    ProcessSentence.LoadCommon()
    try:
        MAXQUERYSENTENCELENGTH = int(utils.ParserConfig.get("website", "maxquerysentencelength"))
    except (KeyError, NoOptionError):
        MAXQUERYSENTENCELENGTH = 100
    #FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt') # for debug purpose


class ThreadedHTTPServer(ForkingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    ForkingMixIn.max_children = 4   # default: max_children = 40
    HTTPServer.request_queue_size = 4   #default: request_queue_size = 5


if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.port:
        startport = int(args.port)
    else:
        startport = int(utils.ParserConfig.get("website", "port"))

    print("Running in port " + str(startport))
    httpd = HTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)
    if utils.runtype == "release":
        httpd.request_queue_size = 0
        #allow release_analyze to have normal queue size, as 5.
    httpd.serve_forever()
    print(" End of RestfulService_BaseHTTP.py")
    # app.test_client().get('/')
