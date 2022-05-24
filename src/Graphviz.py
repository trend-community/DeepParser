import utils  # using the BarTags.
import Lexicon
from utils import *

class Node(object):
    counter = 1
    def __init__(self,text):
        self.text = text
        self.sons = []
        self.upperRelation = None
        self.ID = Node.counter
        Node.counter += 1


def CreateFlatTree(inputnode, nodelist, Debug, parentid=0):
    if 'text' not in inputnode:
        return

    if 'norm' in inputnode and Debug :
        norm = inputnode['norm']
    else:
        norm = inputnode['text']
    node = Node(norm)
    node.parentid = parentid
    node.endOffset = inputnode['EndOffset']
    node.startOffset = inputnode['StartOffset']
    node.features = inputnode['features']
    #node.text = inputnode['text']
    if 'norm' in inputnode:
        node.norm = inputnode['norm']
    if 'atom' in inputnode:
        node.atom = inputnode['atom']
    if 'pnorm' in inputnode:
        node.pnorm = inputnode['pnorm']

    # if not hasattr(CreateFlatTree, "nodeid"):
    #     CreateFlatTree.nodeid = 1
    # else:
    #     CreateFlatTree.nodeid += 1
    # node.id = CreateFlatTree.nodeid

    node.upperRelation = ""
    if 'UpperRelationship' in inputnode.keys():
        node.upperRelation = inputnode['UpperRelationship']
    nodelist.append(node)

    if 'sons' in inputnode.keys() and  "0" not in node.features:
        #if this node is 0, don't show the sons. April 30, 2018. Ben
        for son in inputnode['sons']:
            CreateFlatTree(son, nodelist, Debug, node.ID)

    return


def GetSourceLexicon(text):
    source = None

    if text in Lexicon._LexiconDict and (text not in Lexicon._LexiconLookupSet[LexiconLookupSource.DEFLEX]) and (text not in Lexicon._LexiconLookupSet[LexiconLookupSource.EXTERNAL]) :
        source = "Exclude"
    if text in Lexicon._LexiconLookupSet[LexiconLookupSource.DEFLEX]:
        source = "DefLex"
    elif text in Lexicon._LexiconLookupSet[LexiconLookupSource.EXTERNAL]:
        source = "External"
    return source

def orgChart(json_input, Debug):
    nodelist = []
    decoded = json.loads(json_input)
    #print (decoded)
    CreateFlatTree(decoded, nodelist, Debug)
    dataRows = []
    for node in nodelist:
        v = str(node.ID)
        if node.parentid:
            manager = str(node.parentid)
        else:
            manager = ''    # root. parentid is zero

        tooltip = ' {}\n StartOffset: {} EndOffset: {}'.format(node.features, node.startOffset, node.endOffset)
        if hasattr(node, "pnorm"):
            tooltip += " pnorm:{}".format(node.pnorm)

        source = GetSourceLexicon(node.text)
        if source:
            tooltip +=  "\nFrom: " + source

        if hasattr(node, "norm"):
            tooltip += " '{}'".format(node.norm)
        if hasattr(node, "atom"):
            tooltip += " /{}/".format(node.atom)

        f = node.text
        f_extra = ""
        BarFeature = utils.LastItemIn2DArray(node.features, FeatureOntology.BarTags)
        if BarFeature:
            f_extra = BarFeature
        if node.upperRelation:
            f_extra += "(" + node.upperRelation + ")"
        if f_extra:
            f += '<div style="color:red; font-style:italic">' + f_extra + '</div>'

        element = [{'v':v, 'f':f}, manager, tooltip]
        dataRows.append(element)

    return dataRows


# def digraph(nodes):
#     import DependencyTree
#     x = DependencyTree.DependencyTree()
#     x.transform(nodes)
#     return x.digraph()


if __name__ == "__main__":
    m_json_input = '{"EndOffset": 7, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 7, "StartOffset": 0, "features": ["space", "0", "NP", "modJJ", "loc", "locNE", "inanim", "n", "npr", "XP", "Politics", "phy", "country", "countryNE", "place", "N", "natural", "earth"], "text": "中华人民共和国"}], "text": "中华人民共和国"}'
    # showGraph(json_input)
    m_dataRows = orgChart(m_json_input, Debug=True)
    print(str(m_dataRows))







