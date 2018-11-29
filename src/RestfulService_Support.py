
import urllib, logging, os, re, sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import time, argparse, traceback, jsonpickle, json
from functools import lru_cache


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
        logging.info("[START] ")
        starttime = current_milli_time()
        try:
            if link.path.startswith('/Normalize/'):
                self.Normalize(urllib.parse.unquote(link.path[11:]))
            elif link.path.startswith('/blacklistDetector'):
                self.BlackList(urllib.parse.unquote(link.query[10:]))
            elif link.path.startswith('/removeID'):
                try:
                    _, value = link.query.split("=",1)
                    self.BlacklistID(urllib.parse.unquote(value))
                except:
                    self.send_error(500, "Wrong qaid parameter.")
            elif link.path.startswith('/Reload/'):
                self.Reload()
            elif link.path in ['/gchart_loader.js', '/favicon.ico', '/Readme.txt']:
                self.feed_file(link.path[1:])
            else:
                logging.error("Wrong link.")
                self.send_error(404)

            logging.info("[TIME] {}".format(current_milli_time() - starttime))
        except Exception as e:
            logging.error("Unknown exception in do_GET")
            logging.error(str(e))
            traceback.print_exc()
            self.send_error(500, "Unknown exception")
            #self.ReturnBlank()
            return


    def Normalize(self, Sentence):
        self.send_response(200)
        self.send_header('Content-type', "text/html; charset=utf-8")
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        self.wfile.write(normalization(Sentence).encode("utf-8"))


    def BlacklistID(self, qaid):
        if qaid in idBlack.blacklist:
            Reply = "qaid {} is already in blacklist".format(qaid)
        else:
            timestamp = str(datetime.now())
            idBlack.blacklist.add(qaid)
            with open(args.idblacklist, "a", encoding="utf-8") as blacklist:
                blacklist.write("{}\t{}\n".format(qaid, timestamp))
            Reply = "qaid {} is recorded.".format(qaid)

        self.send_response(200)
        self.send_header('Content-type', "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write( Reply.encode("utf-8"))
        if args.externalcommand:
            logging.warning("Executing {}".format(args.externalcommand))
            runSimpleSubprocess(args.externalcommand)   #remove old ngix cache


    def BlackList(self, questionobjectstr):
        self.send_response(200)
        self.send_header('Content-type', "text/html; charset=utf-8")
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        questionobject = jsonpickle.decode(questionobjectstr)
        if "qaID" not in questionobject:
            questionobject["qaID"] = -1   #not in list.
        if "question" not in questionobject:
            questionobject["question"] = "not in list"

        returnvalue = {'isBlack': isBlack(questionobject["question"]),
                  'containBlack': containBlack(questionobject["question"]),
                       'idBlack': idBlack(questionobject["qaID"])}
        self.wfile.write(json.dumps(returnvalue, ensure_ascii=False).encode("utf-8"))


    def Reload(self):
        self.send_response(200)
        self.send_header('Content-type', "text/html; charset=utf-8")
        self.end_headers()
        loadlist()
        Reply = "Reloaded blacklist at " + str(datetime.now())
        self.wfile.write( Reply.encode("utf-8"))


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


@lru_cache(maxsize=100000)
def  normalization( inputstr):
    temp = re.sub("(https?|ftp)://\S+", " JDHTTP ", inputstr)
    temp = re.sub("\S+@\S+", " JDEMAIL ", temp)
    temp = re.sub("#E-s\d+", " ", temp)
    afterfilter = ""
    for c in temp:
        if c in normalization.dict_fh:
            afterfilter += normalization.dict_fh[c]
            continue
        if c in normalization.signtoremove:
            afterfilter += " "
            continue
        if '😀' <= c <= '🙏' or c == "☹":
            afterfilter += " "
            continue
        afterfilter += c

    return " ".join([x for x in afterfilter.split() if x not in normalization.stopwords])
    # afterreplacestopwords = []
    # for word in afterfilter.split():
    #     if word not in normalization.stopwords:
    #         afterreplacestopwords.append(word)
    #
    # return " ".join(afterreplacestopwords)


def runSimpleSubprocess(aCommand):
    import subprocess

    subprocess.Popen(aCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #don't wait for return.
    # output, error_output = p.communicate()
    # sys.stdout.flush()
    # sys.stderr.flush()
    # if p.returncode != 0:
    #     logging.error('ERROR: command failed with status %d' % p.returncode)
    #     logging.error('    Command: \n' + aCommand)
    #     logging.error('    Output: \n' + str(output))
    #     logging.error('    ErrorOutput: \n' + str(error_output))
    #     return p.returncode, error_output
    # else:
    #     return p.returncode, output


def loadlist():
    isBlack.blacklist = set()
    with open(args.blacklist, encoding="utf-8") as blacklist:
        for word in blacklist:
            if word.strip():
                isBlack.blacklist.add(word.strip())

    containBlack.blacklist = set()
    with open(args.containblacklist, "r", encoding="utf-8") as blacklist:
        for word in blacklist:
            if word.strip():
                containBlack.blacklist.add(word.strip())

    normalization.fulllength = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｇｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９０：-"
    normalization.halflength = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890:-"
    normalization.dict_fh = {}
    for i in range(len(normalization.fulllength)):
        normalization.dict_fh[normalization.fulllength[i]] = normalization.halflength[i]
    normalization.signtoremove = "！？｡＂＃＄％＆＇（）＊＋，／；＜＝＞＠。［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏" \
                                 + "!\"#$%&\'()*+,/;<=>?@[\\]^_`{|}~"

    normalization.stopwords = set()
    with open(args.stowords, encoding="utf-8") as stopwords:
        for stopword in stopwords:
            if stopword.startswith("word,"):
                continue  # opening line
            if "," in stopword:
                word, _ = stopword.split(",")
                normalization.stopwords.add(word.strip())

    idBlack.blacklist = set()
    try:
        with open(args.idblacklist, encoding="utf-8") as blacklist:
            for word in blacklist:
                if word.strip():
                    if "\t" in word:
                        qaid, timestamp = word.strip().split("\t", 1)
                    else:
                        qaid = word.strip()
                    idBlack.blacklist.add(qaid)
    except FileNotFoundError:
        pass


def isBlack(inputstr):
    if inputstr in isBlack.blacklist:
        return True
    else:
        return False


def idBlack(qaid):
    if qaid in idBlack.blacklist:
        return True
    else:
        return False


@lru_cache(maxsize=100000)
def containBlack(inputstr):
    for x in containBlack.blacklist:
        if x in inputstr:
            return True

    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("stowords")
    parser.add_argument("blacklist")
    parser.add_argument("containblacklist")
    parser.add_argument("idblacklist")
    parser.add_argument("--externalcommand")
    args = parser.parse_args()
    if args.port:
        startport = int(args.port)
    else:
        startport = 4001

    print("Running Normalization in port {}".format(startport))
    logging.warning("Running Normalization in port {}".format(startport))
    loadlist()

    httpd = HTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)

    httpd.serve_forever()
    print(" End of RestfulService_BaseHTTP.py")
    # app.test_client().get('/')
