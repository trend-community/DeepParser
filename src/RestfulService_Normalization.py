
import urllib, logging, os, re, sys

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
            if link.path.startswith('/Normalize/'):
                self.Normalize(urllib.parse.unquote(link.path[16:]))
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


    def Normalize(self, Sentence):
        self.send_response(200)
        self.send_header('Content-type', "text/html; charset=utf-8")
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        self.wfile.write(normalization(Sentence))



def  normalization( inputstr):
    if not hasattr(normalization, "fulllength"):
        normalization.fulllength = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｇｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９０：-"
        normalization.halflength = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890:-"
        normalization.dict_fh = {}
        for i in range(len(normalization.fulllength)):
            normalization.dict_fh[normalization.fulllength[i]] = normalization.halflength[i]
        normalization.signtoremove = "！？｡＂＃＄％＆＇（）＊＋，／；＜＝＞＠。［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏" \
                                     + "!\"#$%&\'()*+,/;<=>?@[\\]^_`{|}~"

        normalization.stopwordtags = {"赞成": "JDSTOPYES", "拒绝": "JDSTOPNO", "无意义": "JDSTOPHELLO", "敏感词": ""}
        normalization.dict_stopwords = {"敏感词": ["亲", "亲亲", "亲爱的", "宝贝", "宝宝"]}
        with open(sys.argv[2], encoding="utf-8") as stopwords:
            for stopword in stopwords:
                if stopword.startswith("word,"):
                    continue  # opening line
                if "," in stopword:
                    word, tag = stopword.split(",")
                    tag = tag.strip()
                    word = word.strip()
                    if tag in normalization.stopwordtags:
                        if tag not in normalization.dict_stopwords:
                            normalization.dict_stopwords[tag] = [word]
                        else:
                            normalization.dict_stopwords[tag].append(word)

    temp = re.sub("(https?|ftp)://\S+", " JDHTTP ", inputstr)
    temp = re.sub("\S+@\S+", " JDHTTP ", temp)
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

    afterreplacestopwords = []
    for word in afterfilter.split():
        replaced = False
        for stopwordtag in normalization.dict_stopwords:
            if word in normalization.dict_stopwords[stopwordtag]:
                afterreplacestopwords.append(normalization.stopwordtags[stopwordtag])
                replaced = True
                break
        if not replaced:
            afterreplacestopwords.append(word)

    return " ".join(afterreplacestopwords)





if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.port:
        startport = int(args.port)
    else:
        startport = 4001

    print("Running Normalization in port {}".format(startport))
    logging.warning("Running Normalization in port {}".format(startport))

    httpd = HTTPServer( ('0.0.0.0', startport), ProcessSentence_Handler)

    httpd.serve_forever()
    print(" End of RestfulService_BaseHTTP.py")
    # app.test_client().get('/')
