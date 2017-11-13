import os, logging
import pydot
import json
import time

dir_path = os.path.dirname(os.path.realpath(__file__))


nodeList = []

class Node(object):
    def __init__(self,text):
        self.text = text
        self.sons = []
        self.upperRelation = None


def CreateTree(inputnode):
    text = inputnode['text']
    node = Node(text)
    end = inputnode['EndOffset']
    node.endOffset = end
    start = inputnode['StartOffset']
    node.startOffset = start
    features = inputnode['features']
    node.features = features
    if 'UpperRelationship' in inputnode.keys():
        upperRelation = inputnode['UpperRelationship']
        node.upperRelation = upperRelation
    if 'sons' in inputnode.keys():
        for son in inputnode['sons']:
            node.sons.append(CreateTree(son))
    nodeList.append(node)
    return node

def printTree(list):
    for node in list:
        print ("original text is " + node.text)
        # if node.sons:
        #     print(str(len(node.sons)))
        #     for son in node.sons:
        #         print(son.text)


def OrgGraph():
    graph = pydot.Dot(graph_type='digraph')
    for node in nodeList:
        feature = "features: "
        for f in node.features:
            feature += f + " "
        feature += '&#13;&#10;'
        end = "EndOffset :" + str(node.endOffset) + '&#13;&#10;'
        start = "StartOffset :" +str(node.startOffset)
        txt = feature +  end  + start
        lexNode = pydot.Node(node.text, fontsize=12, tooltip=txt)
        graph.add_node(lexNode)
    for node in nodeList:
        text = node.text
        if node.sons:
            hasRelation = False
            for son in node.sons:
                edge = pydot.Edge(text,son.text)
                if son.upperRelation:
                    upper = son.upperRelation[son.upperRelation.index(".")+1:]
                    edge.set_label(upper)
                    hasRelation = True
                elif hasRelation :
                    edge.set_label("H")
                graph.add_edge(edge)

    return graph


def showGraph(json_input):
    nodeList[:] = []
    decoded = json.loads(json_input)
    CreateTree(decoded)
    print("size of nodelist is " + str(len(nodeList)))
    # printTree(nodeList)
    graph = OrgGraph()
    filename = os.path.join(dir_path, '../../parser/graph/' ,  time.strftime("%Y%m%d-%H%M%S")+'.svg')
    # graph.write_svg('g1.svg')
    graph.write_svg(filename)
    return filename

def orgChart(json_input):
    nodeList[:] = []
    decoded = json.loads(json_input)
    CreateTree(decoded)
    # printTree(nodeList)
    dataRows = []
    for node in nodeList:
        if len(nodeList) > 1:
            if node.sons:
                hasRelation = False
                for son in node.sons:
                    element = []
                    text = son.text

                    if son.upperRelation:
                         relation = son.upperRelation[son.upperRelation.index(".") + 1:]
                         text = {}
                         word = son.text
                         v = 'v'
                         f = 'f'
                         text.update({v:word})
                         fValue = word+'<div style="color:red; font-style:italic">' + relation+'</div>'
                         text.update({f:fValue})
                         hasRelation = True

                    elif hasRelation:
                        # print("hasRelation is true")
                        relation = 'H'
                        text = {}
                        word = son.text
                        v = 'v'
                        f = 'f'
                        text.update({v: word})
                        fValue = word + '<div style="color:red; font-style:italic">' + relation + '</div>'
                        text.update({f: fValue})
                        hasRelation = False

                    print(str(text))
                    parent = node.text
                    feature = "features: "
                    for f in son.features:
                        feature += f + " "
                    end = "EndOffset :" + str(son.endOffset)+"  "
                    start = "StartOffset :" + str(son.startOffset)
                    txt = feature + end + start
                    tooltip = txt
                    element.append(text)
                    element.append(parent)
                    element.append(tooltip)
                    dataRows.append(element)
        else:
            element = []
            text = node.text
            feature = "features: "
            for f in node.features:
                feature += f + " "
            end = "EndOffset :" + str(node.endOffset)+" "
            start = "StartOffset :" + str(node.startOffset)
            txt = feature + end + start
            tooltip = txt
            element.append(text)
            element.append(tooltip)
            dataRows.append(element)
    nodeList[:] = []
    return dataRows






if __name__ == "__main__":
    json_input = '{"EndOffset": 8, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 4, "StartOffset": 0, "features": ["v", "equivN", "chg", "deverbal", "V0", "v2NN", "exercise", "N", "act", "chgLoc", "entice", "attrC"], "sons": [{"EndOffset": 2, "StartOffset": 0, "UpperRelationship": "^.M", "features": ["v", "0", "N", "advV"], "text": "满减"}, {"EndOffset": 4, "StartOffset": 2, "features": ["v", "equivN", "chg", "deverbal", "V0", "v2NN", "0", "NP", "XP", "exercise", "N", "act", "chgLoc", "entice", "attrC"], "text": "活动"}], "text": "满减活动"}, {"EndOffset": 8, "StartOffset": 4, "features": ["sent", "pt", "Pred", "A", "pred", "pro"], "sons": [{"EndOffset": 6, "StartOffset": 4, "UpperRelationship": "^.R", "features": ["0", "pt", "emph", "ptA", "A", "pEmo", "attitude", "sent", "a", "an", "passion", "property", "rank", "intensifier", "good", "daxingC"], "text": "超级"}, {"EndOffset": 8, "StartOffset": 6, "features": ["0", "pt", "A", "AP", "pred", "pro", "sent", "XP", "Pred"], "text": "划算"}], "text": "超级划算"}], "text": "满减活动超级划算"}'
    showGraph(json_input)
    dataRows = orgChart(json_input)
    print(str(dataRows))







