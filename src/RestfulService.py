import logging, sys, re, jsonpickle
import Tokenization, FeatureOntology
import ProcessSentence, Rules
from flask import Flask, request

app = Flask(__name__)

@app.route("/LoadFullFeatureList/<ListPath>")
def LoadFullFeatureList(ListPath):
    FeatureOntology.LoadFullFeatureList(ListPath)
    return str(True)


@app.route("/LoadFeatureOntology/<OntologyPath>")
def LoadFeatureOntology(OntologyPath):
    FeatureOntology.LoadFeatureOntology(OntologyPath)
    return str(True)

@app.route("/LoadLexicon/<LexiconPath>")
def LoadLexicon(LexiconPath):
    FeatureOntology.LoadLexicon(LexiconPath)
    return str(True)


@app.route("/LoadRules/<RulePath>")
def LoadRules(RulePath):
    Rules.LoadRules(RulePath)
    return str(True)


@app.route("/LoadCommon/<LoadCommonRules>")
def LoadCommon(LoadCommonRules=False):
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    FeatureOntology.LoadLexicon('../../fsa/Y/lexY.txt')
    logging.warning("Parameter is:" + str(LoadCommonRules))
    if LoadCommonRules:
        Rules.LoadRules("../temp/800VGy.txt.compiled")
        #Rules.LoadRules("../../fsa/Y/900NPy.xml")
        #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
        # Rules.LoadRules("../../fsa/Y/1test_rules.txt")
        PostProcessRules()
    return str(True)


@app.route("/PostProcessRules")
def PostProcessRules():
    Rules.ExpandRuleWildCard()
    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    Rules.OutputRuleFiles("../temp/")
    return str(True)


@app.route("/Tokenize", methods=['POST'])
def Tokenize_en():
    Sentence = request.form['Sentence']
    return jsonpickle.encode(Tokenization.Tokenize(Sentence))


@app.route("/SearchLexicon/<word>")
def SearchLexicon(word):
    return jsonpickle.encode(FeatureOntology.SearchLexicon(word))


@app.route("/SearchMatchingRule", methods=['POST'])
def SearchMatchingRule():
    nodes = request.form['nodes']
    return jsonpickle.encode(ProcessSentence.SearchMatchingRule(nodes))

@app.route("/OutputRules/<Mode>")
def OutputRules(Mode="concise"):

    return Rules.OutputRules(Mode)

if __name__ == "__main__":
    LoadCommon(LoadCommonRules=True)
    app.run(port=5001, debug=True)
