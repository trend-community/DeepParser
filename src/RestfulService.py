import logging,  jsonpickle, os
import urllib
try:
    from socketserver import ThreadingMixIn, ForkingMixIn
except: #windows? ignore it.
    pass
import ProcessSentence, FeatureOntology
import Graphviz

import utils

from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, HTTPServer
#from urlparse import urlparse, parse_qs
# query_components = parse_qs(urlparse(self.path).query)
# imsi = query_components["imsi"]
#from urlparse import urlparse

class ProcessSentence_Handler(BaseHTTPRequestHandler):
    def address_string(self):
        host, _ = self.client_address[:2]
        # old and slow way: return socket.getfqdn(host)
        return host

    def do_GET(self):
        link = urllib.parse.urlparse(self.path)
        try:
            if link.path == '/LexicalAnalyze':
                queries = dict(qc.split("=") for qc in link.query.split("&"))
                self.LexicalAnalyze(queries)
            elif link.path.startswith('/GetFeatureID/'):
                self.GetFeatureID(link.path[14:])
            elif link.path.startswith('/GetFeatureName/'):
                self.GetFeatureName(int(link.path[16:]))
            elif link.path in ['/gchart_loader.js', '/favicon.ico']:
                self.feed_file(link.path[1:])
            else:
                logging.error("Wrong link.")
                self.send_response(500)
        except Exception as e:
            logging.error("Unknown exception in do_GET")
            logging.error(str(e))
            self.send_response(500)

    def LexicalAnalyze(self, queries):
        Sentence = urllib.parse.unquote(queries["Sentence"])

        if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
            Sentence = Sentence[1:-1]
        # else:
        #     return "Quote your sentence in double quotes please"
        logging.info(Sentence)

        nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence)
        # return  str(nodes)
        # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
        Debug = "Debug" in queries
        if nodes:
            if   queries["Type"] == "simple":
                output_type = "text/html;"
                output_text = utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
            elif queries["Type"] == "json2":
                output_type = "text/html;"
                output_text = nodes.root().CleanOutput_FeatureLeave().toJSON()
            elif queries["Type"] == "parsetree":
                output_type = "text/html;"
                orgdata = Graphviz.orgChart(nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON())
                chart = charttemplate.replace("[[[DATA]]]", str(orgdata))

                if Debug:
                    winningrulestring = ""
                    for rule in winningrules:
                        winningrulestring +=  winningrules[rule] + "\n"
                    chart = chart.replace("<!-- EXTRA -->", winningrulestring)
                output_text = chart
            else:
                output_type = "Application/json;"
                output_text =nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

            try:
                self.send_response(200)
                self.send_header('Content-type', output_type + " charset=utf-8")
                self.end_headers()
                self.wfile.write(output_text.encode("utf-8"))
                logging.info("Done with" + Sentence)
            except Exception as e:
                logging.error(e)
                self.send_response(500)
        else:
            logging.error("nodes is blank")
            self.send_response(500)


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
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "chart.template.html")) as templatefile:
        charttemplate = templatefile.read()

    ProcessSentence.LoadCommon()
    #FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt') # for debug purpose


#class ThreadedHTTPServer(ForkingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


if __name__ == "__main__":
    init()

    startport = int(utils.ParserConfig.get("website", "port"))
    print("Running in port " + str(startport))
    try:
        httpd = ThreadedHTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)
    except:     #windows?
        httpd = HTTPServer(('0.0.0.0', startport), ProcessSentence_Handler)
        logging.warning("Running without multi-process support.")
    httpd.serve_forever()
    print(" End of RestfulService_BaseHTTP.py")
    # app.test_client().get('/')
