#!/bin/python2
import urllib
import logging, os

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import urlparse

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
        link = urlparse.urlparse(self.path)
        try:
            if link.path == '/LexicalAnalyze':
                try:
                    query = urlparse.unquote(link.query)

                    q = query.split("&")
                    queries = dict(qc.split("=") for qc in q)

                except ValueError as e:
                    logging.error("Input query is not correct: " + link.query)
                    logging.error(e)
                    self.send_error(500, "Link input error.")
                    return

                self.LexicalAnalyze(queries)

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
                output_text = "{'output':'example'}"

                self.send_response(200)
                self.send_header("Content-type", "Application/json; charset=utf-8")
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


def init():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.port:
        startport = int(args.port)
    else:
        startport = 5022

    print "Running python2 RestfulService.py in port {}".format(startport)
    logging.warning("Running in port {}".format(startport))

    httpd = HTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)

    httpd.serve_forever()
    print " End of python2 RestfulService.py"
    # app.test_client().get('/')
