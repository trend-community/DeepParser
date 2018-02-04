import logging,  jsonpickle
import urllib
import ProcessSentence


import utils

from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, HTTPServer


class ProcessSentence_Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def address_string(self):
        host, _ = self.client_address[:2]
        # old and slow way: return socket.getfqdn(host)
        return host

    def do_GET(self):
        Sentence = urllib.parse.unquote(self.path)
        if Sentence[0] == "/":
            Sentence = Sentence[1:]

        if len(Sentence) >= 2 and Sentence[0] in "\"“”" and Sentence[-1] in "\"“”":
            Sentence = Sentence[1:-1]

        logging.error(Sentence)
        # else:
        #     return "Quote your sentence in double quotes please"

        nodes, winningrules = ProcessSentence.LexicalAnalyze(Sentence)
        # return  str(nodes)
        # return nodes.root().CleanOutput().toJSON() + json.dumps(winningrules)
        if nodes:
            try:
                self.send_response(200)
                self.send_header('Content-type', "Application/json;charset=utf-8')")
                self.end_headers()
                self.wfile.write(nodes.root().CleanOutput(KeepOriginFeature=False).toJSON().encode("utf-8"))
                logging.error("Done with" + Sentence)
            except Exception as e:
                logging.error(e)
                self.send_response(500)
        else:
            logging.error("nodes is blank")
            self.send_response(500)


def init():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)

    ProcessSentence.LoadCommon()



if __name__ == "__main__":
    init()

    print("Running in port " + str(utils.ParserConfig.get("website", "port")))
    httpd = HTTPServer( ('0.0.0.0', int(utils.ParserConfig.get("website", "port"))), ProcessSentence_Handler)

    httpd.serve_forever()
    # app.test_client().get('/')
