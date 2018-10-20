#!/bin/python2
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
from configparser import NoOptionError
from http.server import BaseHTTPRequestHandler, HTTPServer

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
                    query = urllib.parse.unquote(link.query)

                    q = query.split("&")
                    queries = dict(qc.split("=") for qc in q)

                except ValueError :
                    logging.error("Input query is not correct: " + link.query)
                    self.send_error(500, "Link input error.")
                    return

                if "Key" not in queries or queries["Key"] not in KeyWhiteList:
                    self.send_error(550, "Key Error. Please visit NLP team for an authorization key")
                else:
                    self.LexicalAnalyze(queries)


            elif link.path in ['/gchart_loader.js', '/favicon.ico', '/Readme.txt']:
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
        if queries:
            try:
                output_text = "complete LexicalAnalyze"
                self.send_response(200)
                self.send_header("Content-type:plain/text charset=utf-8")
                self.end_headers()
                self.wfile.write(output_text.encode("utf-8"))

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

    def feed_file(self, filepath):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), filepath)) as f:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'public, max-age=31536000')
            self.end_headers()
            filecontent = f.read()
            if len(filepath)>4 and filepath[-4:] == ".txt":
                reply = "<pre>" + filecontent + "</pre>"
                self.wfile.write(reply.encode("utf-8") )
            else:
                self.wfile.write(filecontent.encode("utf-8"))



def init():

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.port:
        startport = int(args.port)
    else:
        startport = int(utils.ParserConfig.get("website", "port"))

    print("Running python2 RestfulService.py in port {}".format(startport))
    logging.warning("Running in port {}".format(startport))

    httpd = HTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)
    if utils.runtype == "release":
        httpd.request_queue_size = 0
        #allow release_analyze to have normal queue size, as 5.
    httpd.serve_forever()
    print " End of python2 RestfulService.py"
    # app.test_client().get('/')
