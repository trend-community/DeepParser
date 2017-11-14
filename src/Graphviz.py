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
    printTree(nodeList)
    graph = OrgGraph()
    filename = os.path.join(dir_path, '../../parser/graph/' ,  time.strftime("%Y%m%d-%H%M%S")+'.svg')
    # graph.write_svg('g1.svg')
    graph.write_svg(filename)
    return filename

def orgChart(json_input):
    nodeList[:] = []
    decoded = json.loads(json_input)
    CreateTree(decoded)
    textSet = set()
    # printTree(nodeList)
    dataRows = []
    for node in nodeList:
        if len(nodeList) > 1:
            if node.sons:
                hasRelation = False
                for son in node.sons:
                    element = []
                    text = son.text
                    if not textSet.add(text): # add set not successfully due to text duplicate
                        text = {}
                        word = son.text + str(son.startOffset)
                        v = 'v'
                        f = 'f'
                        text.update({v: word})
                        fValue = son.text
                        text.update({f: fValue})
                        if son.upperRelation:
                            relation = son.upperRelation[son.upperRelation.index(".") + 1:]
                            fValue +=  '<div style="color:red; font-style:italic">' + relation + '</div>'
                            text.update({f: fValue})
                            hasRelation = True
                        elif hasRelation:
                            # print("hasRelation is true")
                            relation = 'H'
                            fValue += '<div style="color:red; font-style:italic">' + relation + '</div>'
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
    json_input = '{"EndOffset": 18, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 2, "StartOffset": 0, "features": ["0", "sRB", "butW", "preNumC"], "text": "不过"}, {"EndOffset": 13, "StartOffset": 2, "features": ["beverage", "liquid", "material", "prod", "det0", "inanim", "artifact", "phy", "n", "N", "edible", "solution"], "sons": [{"EndOffset": 3, "StartOffset": 2, "UpperRelationship": "^.M", "features": ["xpC", "det0", "freeM", "indexicalW", "0", "xC", "DT"], "text": "这"}, {"EndOffset": 6, "StartOffset": 3, "UpperRelationship": "^.M", "features": ["linkV", "v", "info", "V", "stateV", "expression", "VG", "inanim", "freeM", "n", "symbol", "beC", "vac"], "sons": [{"EndOffset": 5, "StartOffset": 3, "UpperRelationship": "^.X", "features": ["0", "xC", "MD", "vac"], "text": "应该"}, {"EndOffset": 6, "StartOffset": 5, "features": ["linkV", "v", "info", "V", "stateV", "0", "XP", "expression", "xC", "inanim", "VG", "freeM", "n", "symbol", "beC", "vac"], "text": "是"}], "text": "应该是"}, {"EndOffset": 13, "StartOffset": 6, "features": ["liquid", "beverage", "material", "prod", "NP", "XP", "det0", "inanim", "artifact", "n", "edible", "N", "phy", "solution"], "sons": [{"EndOffset": 10, "StartOffset": 6, "UpperRelationship": "^.M", "features": ["0", "sent", "pt", "A", "an", "source", "N0", "pro"], "text": "原汁原味"}, {"EndOffset": 11, "StartOffset": 10, "UpperRelationship": "^.X", "features": ["UH", "0", "xC", "vac"], "text": "的"}, {"EndOffset": 13, "StartOffset": 11, "features": ["0", "beverage", "liquid", "material", "NP", "prod", "XP", "inanim", "artifact", "phy", "n", "N", "edible", "solution"], "text": "咖啡"}], "text": "原汁原味的咖啡"}], "text": "这应该是原汁原味的咖啡"}, {"EndOffset": 14, "StartOffset": 13, "features": ["0", "punc"], "text": ","}, {"EndOffset": 18, "StartOffset": 14, "features": ["0", "sent", "pt", "A", "an", "source", "N0", "pro"], "text": "原汁原味"}], "text": "不过这应该是原汁原味的咖啡,原汁原味"}'
    # showGraph(json_input)
    dataRows = orgChart(json_input)
    print(str(dataRows))







