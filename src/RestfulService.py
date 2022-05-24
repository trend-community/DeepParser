
import urllib
try:
    from socketserver import ThreadingMixIn, ForkingMixIn
except: #windows? ignore it.
    pass
import ProcessSentence
import Graphviz
import Rules
import utils
import Lexicon
from utils import *
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import time, argparse, traceback

#current_milli_time = lambda: int(round(time.time() * 1000))
charttemplate = ''
KeyWhiteList = []
MAXQUERYSENTENCELENGTH = 100

class ProcessSentence_Handler(BaseHTTPRequestHandler):
    def address_string(self):
        host, _ = self.client_address[:2]
        # old and slow way: return socket.getfqdn(host)
        return host

    def _sendresponse(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        if content_len:
            post_body = self.rfile.read(content_len)
            post_data = urllib.parse.parse_qs(post_body.decode('utf-8'))

            if "Key" not in post_data or post_data["Key"][0] not in KeyWhiteList:
                self.send_error(550, "Key Error. Please visit NLP team for an authorization key")
            else:
                self.DocumentAnalyze(post_data)


    def do_GET(self):
        # if hasattr(self.server, "active_children") and self.server.active_children:
        #     if len(self.server.active_children) > 10:
        #         logging.info("Server Active Children:" + str(len(self.server.active_children)) )
        #         logging.error("Server is too busy to serve!")
        #         self.send_error(504, "Server Busy")
        #         #self.ReturnBlank()
        #         return
        #   test case 1: http://localhost:5001/LexicalAnalyze?Type=parsetree&Debug=true&Key=Lsdif238fj&Sentence=%22%E4%BA%AC%E4%B8%9C%E5%BE%88%E6%96%B9%E4%BE%BF&hellip;%E8%B4%A8%E9%87%8F%E5%BE%88%E5%A5%BD&hellip%22
        #   test case 2:
        link = urllib.parse.urlparse(self.path)
        try:
            if link.path == '/LexicalAnalyze':
                try:
                    q = link.query.split("&")
                    queries = {}
                    for qc in q:
                        try:
                            key, quotedvalue = qc.split("=",1)
                        except ValueError as e:
                            logging.info("Input query: somehow the & and = sign are not paired. may be part of the sentence.")
                            continue
                        queries[key] = urllib.parse.unquote(quotedvalue)

                    if "Sentence" in queries:   #get the Sentence from original link.query to avoid "&/=" sign
                        query = urllib.parse.unquote(link.query)
                        StartLocation = query.find("Sentence=") + len("Sentence=")
                        if query[StartLocation] in "[\"“”]":
                            #from the first quote to the last quote
                            EndLocation1 = query.rfind("\"", StartLocation + 1)
                            EndLocation2 = query.rfind("“", StartLocation + 1)
                            EndLocation3 = query.rfind("”", StartLocation + 1)
                            EndLocation = max(EndLocation1, EndLocation2, EndLocation3)
                            if EndLocation > 0:
                                queries["Sentence"] = query[StartLocation + 1:EndLocation]

                except ValueError as e:
                    logging.error("Input query is not correct: {}\n{}".format( link.query, e))
                    self.send_error(500, "Link input error.")
                    return

                if "Key" not in queries or queries["Key"] not in KeyWhiteList:
                    self.send_error(550, "Key Error. Please visit NLP team for an authorization key")
                else:
                    self.LexicalAnalyze(queries)

            elif link.path.startswith('/GetFeatureID/'):
                self.GetFeatureID(link.path[14:])
            elif link.path.startswith('/GetFeatureName/'):
                self.GetFeatureName(int(link.path[16:]))
            elif link.path.startswith('/FeatureOntology'):
                self.ShowFeatureOntology()
            elif link.path.startswith('/Reload'):
                #print (link.path[7:])
                self.Reload(link.path[7:])
            elif link.path in ['/gchart_loader.js', '/favicon.ico', '/Readme.txt', '/index.html',
                               '/d3.v4.min.js', '/viz-lite.js', '/d3-graphviz.min.js']:
                self.feed_file("static/" + link.path[1:])
            elif link.path in ['/', '/default.htm', '/default.html', '/index.htm', '/index.html']:
                self.feed_file("static/" + 'index.html')
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


    def DocumentAnalyze(self, queries):
        Type = queries["Type"][0]
        Debug = queries["Debug"][0]
        Schema = queries["Schema"][0]
        Document = queries['Document'][0]
        if 'newline' in queries:
            Newline = queries['newline'][0]
        else:
            Newline = ''
        if 'transferlinebreak' in queries:
            TransferLinebreak = queries['transferlinebreak'][0]
        else:
            TransferLinebreak = 'transfer'

        if "ResetGlobalValue" in queries:
            if queries["ResetGlobalValue"][0] == "true":
                utils.ResetGlobalVariables()
        else:
            utils.ResetGlobalVariables()  # if not present, then also reset (traditional way)

        for x in ["DocumentClass", "ParagraphClass", "SentenceClass"]:
            if x in queries and queries[x]:
                utils.GlobalVariables[x] = queries[x][0]

        output_text = ""
        logging.info("[START] [{}]\t{}...".format(queries["Key"], Document[:10]))
        starttime = current_milli_time()

        dag, winningrules = ProcessSentence.DocumentAnalyze(Document, Schema, Newline, TransferLinebreak)

        winningrulestring = ''
        if winningrules:
            for rule in winningrules:
                winningrulestring += winningrules[rule] + "\n"

        if Type == "pnorm":
            output_type = "Application/json;"
            output_text = dag.pnorm()
        elif Type == "graphjson":
            output_type = "Application/json;"
            output_text = dag.digraph(Type)
        else:   # show the graph part of parsetree
            output_type = "text/html;"
            chart = charttemplate.replace("[[[DIGDATA]]]", str(dag.digraph()))
            chart = chart.replace("<!-- PNORM -->", dag.pnorm_text())
            if Debug == "True":
                globalinfo = ''
                for k in utils.GlobalVariables:
                    globalinfo += k + ": " + utils.GlobalVariables[k] + "\n"
                for k in Lexicon._LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT]:
                    globalinfo += "[" + k.text + "]\n"
                if globalinfo:
                    globalinfo = "<hr/>" + globalinfo
                    chart = chart.replace("<!-- GLOBALINFO -->", globalinfo)

                chart = chart.replace("<!-- EXTRA -->", winningrulestring)
            output_text = chart

        try:
            self.WebsiteReply(output_text, output_type)
            logging.info("[COMPLETE] [{}]\t{}...".format(queries["Key"], Document[:10]))
            logging.info("[TIME] {}".format(current_milli_time() - starttime))
        except Exception as e:
            logging.error(e)
            self.send_error(500, "Error in processing")


    def LexicalAnalyze(self, queries):
        Sentence = queries["Sentence"][:MAXQUERYSENTENCELENGTH]
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

        if "ResetGlobalValue" in queries:
            if queries["ResetGlobalValue"] == "true":
                utils.ResetGlobalVariables()
        else:
            utils.ResetGlobalVariables()    #if not present, then also reset (traditional way)

        for x in ["DocumentClass", "ParagraphClass", "SentenceClass"]:
            if x in queries and queries[x]:
                utils.GlobalVariables[x] = queries[x]

        if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
            Sentence = Sentence[1:-1]
        # else:
        #     return "Quote your sentence in double quotes please"
        logging.info("[START] [{}]\t{}".format(queries["Key"], Sentence) )
        starttime = current_milli_time()

        nodes, dag, winningrules = ProcessSentence.LexicalAnalyze(Sentence, schema)
        # return  str(nodes)
        # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
        Debug = "Debug" in queries
        if nodes:
            if  Type  == "segmentation":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokensSegment_oneliner(nodes)
            elif Type == "keyword":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokensKeyword_oneliner(dag)
            elif  Type  == "simple":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
                # if len(dag.nodes) > 0:
                #     output_text += "\n" + dag.digraph(Type)

            elif  Type  == "simpleEx":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokens_oneliner_ex(nodes)
                # if len(dag.nodes) > 0:
                #     output_text += "\n" + dag.digraph(Type)
            elif  Type  == "simpleMerge":
                output_type = "text/plain;"
                output_text = utils.OutputStringTokens_oneliner_merge(nodes)
            elif Type == "json2":
                output_type = "text/html;"
                output_text = nodes.root().CleanOutput_FeatureLeave().toJSON()
            elif Type == 'graph':
                output_type = "text/plain;"
                output_text = dag.digraph(Type)
            elif Type == "graphjson":
                output_type = "Application/json;"
                output_text = dag.digraph(Type)
            elif Type == 'simplegraph':
                output_type = "text/plain;"
                output_text = dag.digraph(Type)
            elif Type == 'sentiment':
                output_type = 'text/plain;'
                output_text = utils.OutputStringTokens_onelinerSA(dag)
            elif Type == 'sentimenttext':
                output_type = 'text/plain;'
                output_text = utils.OutputStringTokens_onelinerSAtext(dag)
            elif Type =='QA':
                output_type = 'text/plain;'
                output_text = utils.OutputStringTokens_onelinerQA(dag)
            elif Type == "parsetree":
                output_type = "text/html;"
                if action == "headdown":
                    output_json = nodes.root().CleanOutput_Propagate().toJSON()
                else:
                    output_json =nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

                orgdata = Graphviz.orgChart(output_json, Debug=Debug)
                chart = charttemplate.replace("[[[DATA]]]", str(orgdata))

                if dag:
                    orgdata = dag.digraph()
                    chart = chart.replace("[[[DIGDATA]]]", str(orgdata))

                pnorm_text = dag.pnorm_text()
                if pnorm_text:
                    chart = chart.replace("<!-- PNORM -->", pnorm_text)

                if Debug:
                    globalinfo = ''
                    for k in utils.GlobalVariables:
                        globalinfo += k + ": " + utils.GlobalVariables[k] + "\n"
                    for k in Lexicon._LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT]:
                        globalinfo += "[" + k.text + "]\n"
                    if globalinfo:
                        globalinfo = "<hr/>" + globalinfo
                        chart = chart.replace("<!-- GLOBALINFO -->", globalinfo)

                    winningrulestring = ""
                    if winningrules:
                        for rule in winningrules:
                            winningrulestring +=  winningrules[rule] + "\n"
                        chart = chart.replace("<!-- EXTRA -->", winningrulestring)
                output_text = chart
            elif Type == "pnorm":
                output_type = "Application/json;"
                output_text = dag.pnorm()
            else:
                output_type = "Application/json;"
                if action == "headdown":
                    output_text = nodes.root().CleanOutput_Propagate().toJSON()
                else:
                    output_text =nodes.root().CleanOutput(KeepOriginFeature=Debug).toJSON()

            try:
                self.WebsiteReply(output_text, output_type)
                logging.info("[COMPLETE] [{}]\t{}".format(queries["Key"], Sentence) )
                logging.info("[TIME] {}".format(current_milli_time()-starttime))
            except Exception as e:
                logging.error(e)
                self.send_error(500, "Error in processing")
                #self.ReturnBlank()
        else:
            logging.error("nodes is blank")
            self.WebsiteReply("")

    def WebsiteReply(self, Content, ContentType="text/plain;", slowchange=False ):
        self.send_response(200)
        self.send_header('Content-type', ContentType + " charset=utf-8")
        if slowchange:
            self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        self.wfile.write(Content.encode("utf-8"))

    def Reload(self, ReloadTask):
        LoadFrom = ParserConfig.get("main", "loadfrom").lower()
        if LoadFrom == "dump":
            Reply = "The system is loaded from dump as in config.ini. It does not support online reload."
            self.WebsiteReply(Reply)
            return

        utils.InitDB()
        PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
        # XLocation = os.path.dirname(PipeLineLocation)     # need to get relative location, not the absolute location.
        XLocation, _ = os.path.split(PipeLineLocation)
        XLocation += "/"

        Reply = "Lexicon/Rule/Pipeline:"
        systemfileolderthanDB = True # ProcessSentence.SystemFileOlderThanDB(XLocation)
        # when db is disabled, there is no record of system files. then the rule files are forced to reload
        # because we don't know whether the systems are modified or not.
        # Let's disable this functionality for now. Assume the system files are not modified. Not to be reload dynamically.


        if ReloadTask.lower() == "/lexicon":
            logging.info("Start loading lexicon...")
            logging.warning("Need debugging")
            Lexicon.ResetAllLexicons()
            # ProcessSentence.LoadCommonLexicon(XLocation)
            for action in ProcessSentence.PipeLine:
                action_upper = action.upper()
                if action_upper.startswith("LOOKUP SPELLING:"):
                    Spellfile = action[action.index(":") + 1:].strip().split(",")
                    for spell in Spellfile:
                        spell = spell.strip()
                        if spell:
                            Lexicon.LoadExtraReference(XLocation + spell, Lexicon._LexiconSpellingDict)

                elif action_upper.startswith("LOOKUP MAIN:"):
                    Mainfile = action[action.index(":") + 1:].strip().split(",")
                    for main in Mainfile:
                        main = main.strip()
                        if main:
                            Lexicon.LoadMainLexicon(XLocation + main)

                elif action_upper.startswith("LOOKUP SEGMENTSLASH:"):
                    logging.warning(
                        "SEGMENTSLASH files are deprecated. The segments in Main and 5/6 rules are loaded automatically. ")

                elif action_upper.startswith("LOOKUP LEX:"):
                    Lexfile = action[action.index(":") + 1:].strip().split(",")
                    for lex in Lexfile:
                        lex = lex.strip()
                        if lex:
                            Lexicon.LoadLexicon(XLocation + lex)

                elif action_upper.startswith("LOOKUP SENSITIVE:"):
                    Lexfile = action[action.index(":") + 1:].strip().split(",")
                    for lex in Lexfile:
                        lex = lex.strip()
                        if lex:
                            Lexicon.LoadLexicon(XLocation + lex, Sensitive=True)

                elif action_upper.startswith("LOOKUP DEFLEX:"):
                    Compoundfile = action[action.index(":") + 1:].strip().split(",")
                    for compound in Compoundfile:
                        compound = compound.strip()
                        if compound:
                            Lexicon.LoadLexicon(XLocation + compound, lookupSource=LexiconLookupSource.DEFLEX)

                elif action_upper.startswith("LOOKUP EXTERNAL:"):
                    Externalfile = action[action.index(":") + 1:].strip().split(",")
                    for external in Externalfile:
                        external = external.strip()
                        if external:
                            Lexicon.LoadLexicon(XLocation + external,
                                                lookupSource=LexiconLookupSource.EXTERNAL)

            Lexicon.LoadSegmentLexicon()
            Reply += "Reloaded lexicon at " + str(datetime.now())

        if ReloadTask.lower() == "/rule":
            logging.info("Start loading rules...")
            #Rules.ResetAllRules()
            #ProcessSentence.WinningRuleDict.clear()
            #assume system files are not to be reload dynamically.
            #GlobalmacroLocation = os.path.join(XLocation, "../Y/GlobalMacro.txt")
            #Rules.LoadGlobalMacro(GlobalmacroLocation)

            for action in ProcessSentence.PipeLine:
                action_upper = action.upper()
                if action_upper.startswith("FSA "):
                    Rulefile = action[3:].strip()
                    RuleLocation = os.path.join(XLocation, Rulefile)
                    Rules.LoadRules(RuleLocation)

                elif action_upper.startswith("DAGFSA_APP "):  # FUZZY
                    Rulefile = action[10:].strip()
                    RuleLocation = os.path.join(XLocation, Rulefile)
                    Rules.LoadRules(RuleLocation, fuzzy=True)

                elif action_upper.startswith("DAGFSA "):
                    Rulefile = action[6:].strip()
                    RuleLocation = os.path.join(XLocation, Rulefile)
                    Rules.LoadRules(RuleLocation)

            Reply += "Reloaded rules at " + str(datetime.now())

        if ReloadTask.lower() == "/pipeline":
            logging.info("Start loading pipeline...")
            Rules.ResetAllRules()
            ProcessSentence.PipeLine = []
            ProcessSentence.LoadCommon()
            Reply += "Reloaded pipeline at " + str(datetime.now())

        #ProcessSentence.UpdateSystemFileFromDB(XLocation)

        self.WebsiteReply(Reply)
        utils.CloseDB(utils.DBCon)

    def ShowFeatureOntology(self):
        output_text = charttemplate.replace("[[[DIGDATA]]]",
                                FeatureOntology.OutputFeatureOntologyGraph())
        try:
            self.WebsiteReply(output_text, "text/html;")
        except Exception as e:
            logging.error(e)
            self.send_error(500, "Error in processing")


    def GetFeatureID(self, word):
        self.WebsiteReply(jsonpickle.encode(FeatureOntology.GetFeatureID(word)), "Application/json;", slowchange=True)


    def GetFeatureName(self, FeatureID):
        self.WebsiteReply(jsonpickle.encode(FeatureOntology.GetFeatureName(int(FeatureID))), "Application/json;", slowchange=True)


    def feed_file(self, filepath):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), filepath), encoding="utf8") as f:
            filecontent = f.read()
            if len(filepath)>4 and filepath[-4:] == ".txt":
                filecontent = "<pre>" + filecontent + "</pre>"

            self.WebsiteReply(filecontent, 'text/html', slowchange=True)



def init():
    global charttemplate, KeyWhiteList
    global MAXQUERYSENTENCELENGTH

    if utils.ParserConfig.has_option("website", "maxquerysentencelength"):
        MAXQUERYSENTENCELENGTH = int(utils.ParserConfig.get("website", "maxquerysentencelength"))

    LogLevel = ""
    if utils.ParserConfig.has_option("website", "LogLevel") :
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
    #FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt') # for debug purpose

    KeyWhiteList = [x.split("#", 1)[0].strip() for x in utils.ParserConfig.get("main", "keylist").splitlines() if x]



# class ThreadedHTTPServer(ForkingMixIn, HTTPServer):
#     """Handle requests in a separate thread."""
#     ForkingMixIn.max_children = 4   # default: max_children = 40
#     HTTPServer.request_queue_size = 4   #default: request_queue_size = 5


if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.port:
        startport = int(args.port)
    else:
        startport = int(utils.ParserConfig.get("website", "port"))

    if os.name != 'nt':
        #kill the process that is using the same port
        returncode, psid = utils.runSimpleSubprocess("lsof -i tcp:{} | grep LISTEN | awk {{'print $2'}}".format(startport))
        #logging.warning("returncode = {}, psid={}".format(returncode, psid))
        if psid:
            processid = psid.decode('ascii').strip()
            logging.warning("Killing process {} because it is using the same port of {}".format(processid, startport))
            utils.runSimpleSubprocess("kill -9 {}".format(processid))
            time.sleep(0.5) #wait 500ms for the former process to exit cleanly.

    print("Running in port {}".format(startport))
    logging.warning("Running in port {}".format(startport))

    httpd = HTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)
    if utils.runtype == "release":
        httpd.request_queue_size = 0
        #allow release_analyze to have normal queue size, as 5.

    # # to run as ssl, just provide a cert file, and uncomment the following 2 lines:
    # import ssl
    # httpd.socket = ssl.wrap_socket(httpd.socket, certfile='cert-and-key.pem', server_side=True)

    httpd.serve_forever()
    print(" End of RestfulService_BaseHTTP.py")
    # app.test_client().get('/')
