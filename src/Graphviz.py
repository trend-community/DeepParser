import json
import random
import utils, FeatureOntology  # using the BarTags.


class Node(object):
    counter = 1
    def __init__(self,text):
        self.text = text
        self.sons = []
        self.upperRelation = None
        self.id = Node.counter
        Node.counter += 1


def CreateFlatTree(inputnode, nodelist, Debug, parentid=0):
    if 'norm' in inputnode and Debug :
        norm = inputnode['norm']
    else:
        norm = inputnode['text']
    node = Node(norm)
    node.parentid = parentid
    node.endOffset = inputnode['EndOffset']
    node.startOffset = inputnode['StartOffset']
    node.features = inputnode['features']
    # if not hasattr(CreateFlatTree, "nodeid"):
    #     CreateFlatTree.nodeid = 1
    # else:
    #     CreateFlatTree.nodeid += 1
    # node.id = CreateFlatTree.nodeid

    node.upperRelation = ""
    if 'UpperRelationship' in inputnode.keys():
        node.upperRelation = inputnode['UpperRelationship']
    nodelist.append(node)

    if 'sons' in inputnode.keys():
        for son in inputnode['sons']:
            CreateFlatTree(son, nodelist, Debug, node.id)

    return


def orgChart(json_input, Debug):
    nodelist = []
    decoded = json.loads(json_input)
    CreateFlatTree(decoded, nodelist, Debug)
    dataRows = []
    for node in nodelist:
        v = str(node.id)
        if node.parentid:
            manager = str(node.parentid)
        else:
            manager = ''    # root. parentid is zero
        tooltip = ' '.join(node.features) + '\n' + " StartOffset: " + str(node.startOffset) + " EndOffset:" + str(node.endOffset)
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


if __name__ == "__main__":
    m_json_input = '{"EndOffset": 7, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 7, "StartOffset": 0, "features": ["space", "0", "NP", "modJJ", "loc", "locNE", "inanim", "n", "npr", "XP", "Politics", "phy", "country", "countryNE", "place", "N", "natural", "earth"], "text": "中华人民共和国"}], "text": "中华人民共和国"}'
    # showGraph(json_input)
    m_dataRows = orgChart(m_json_input)
    print(str(m_dataRows))







