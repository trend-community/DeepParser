import os, logging
import pydot
import json
import time
import random

dir_path = os.path.dirname(os.path.realpath(__file__))


nodeList = []
randomSet = set()
class Node(object):
    def __init__(self,text):
        self.text = text
        self.sons = []
        self.upperRelation = None
        self.id = 0



def CreateTree(inputnode):
    text = inputnode['text']
    node = Node(text)
    end = inputnode['EndOffset']
    node.endOffset = end
    start = inputnode['StartOffset']
    node.startOffset = start
    features = inputnode['features']
    node.features = features
    id = random.randint(1,1001)
    while id in randomSet:
        id = random.randint(1,1001)
    randomSet.add(id)
    node.id = id
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
    randomSet.clear()
    decoded = json.loads(json_input)
    CreateTree(decoded)
    textSet = set()
    printTree(nodeList)
    #print("size of nodelist is " + str(len(nodeList)))
    dataRows = []
    for node in nodeList:

        if len(nodeList) > 1:
            if node.sons:
                relationExists = checkRelation(node)
                hasRelation = False
                for son in node.sons:
                    element = []
                    # text = son.text
                    # if not textSet.add(text): # add set not successfully due to text duplicate
                    # if text in textSet:
                    text = {}
                    # word = son.text + str(son.startOffset)
                    word = str(son.id)
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
                    elif hasRelation or (node.sons.index(son)==0 and relationExists) :
                        # print("hasRelation is true")
                        relation = 'H'
                        fValue += '<div style="color:red; font-style:italic">' + relation + '</div>'
                        text.update({f: fValue})
                        hasRelation = False
                    # else:
                    #     textSet.add(son.text)

                    #print(str(text))
                    # parent = node.text+str(node.startOffset)
                    parent = str(node.id)
                    # if parent == nodeList[-1].text + str(nodeList[-1].startOffset):
                    if parent == str(nodeList[-1].id):
                        parent = nodeList[-1].text
                        rootElement = []
                        rootElement.append(parent)
                        rootElement.append('')
                        feature = "features: "
                        for f in nodeList[-1].features:
                            feature += f + " "
                        tooltip = feature + "EndOffset :" + str(nodeList[-1].endOffset) +" " + "StartOffset :" + str(nodeList[-1].startOffset)
                        rootElement.append(tooltip)
                        dataRows.append(rootElement)
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
            element.append('')
            element.append(tooltip)
            dataRows.append(element)

    nodeList[:] = []
    return dataRows

def checkRelation(node):
    for son in node.sons:
        if son.upperRelation:
            return True
    return False





if __name__ == "__main__":
    json_input = '{"EndOffset": 6, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 6, "StartOffset": 0, "features": ["V", "chg", "succeed", "pro", "sent", "pt", "v", "stateV", "plusV"], "sons": [{"EndOffset": 2, "StartOffset": 0, "UpperRelationship": "^.R", "features": ["0", "vac", "xC", "RB"], "text": "终于"}, {"EndOffset": 6, "StartOffset": 2, "features": ["0", "idiom", "V", "chg", "succeed", "pro", "sent", "pt", "v", "stateV", "plusV"], "text": "功成名就"}], "text": "终于功成名就"}], "text": "终于功成名就"}'
    # showGraph(json_input)
    dataRows = orgChart(json_input)
    print(str(dataRows))







