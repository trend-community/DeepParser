## This is for analyzing feature/keywords of sales data.
## input file format: sentence\tsalesnum
## output: 2 files: KeywordSales.txt, FeatureSales.txt


import logging, configparser, os
import requests,  jsonpickle, operator



if __name__ == "__main__":
    Sentence = "物流比官网速度快多了"

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    ParserConfig = configparser.ConfigParser()
    ParserConfig.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

    LexicalAnalyzeURL = "{}/LexicalAnalyze?Type=graphjson&Key={}&Sentence=\"{}\"".format(
        ParserConfig.get("client", "url_larestfulservice") ,
        ParserConfig.get("client", "key"),
        Sentence
    )
    ret = requests.get(LexicalAnalyzeURL )
    g = jsonpickle.decode(ret.text)
    for node in g["nodes"]:
        print(node)
    for edge in g["edges"]:
        print(edge)

    OriginSentence = ""
    Nodes = {}
    for node in g["nodes"]:
        OriginSentence += node["text"]
        Nodes[node["ID"]] = node["text"]

    print("Origin Sentece is {}".format(OriginSentence))
    for edge in g["edges"]:
        print("{} --{}--> {}".format(Nodes[edge["from"]],
                                     edge["relation"],
                                     Nodes[edge["to"]]))
