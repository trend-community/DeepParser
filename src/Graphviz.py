import os, logging
import pydot
import json
import time
import random

dir_path = os.path.dirname(os.path.realpath(__file__))


nodeList = []
randomSet = set()
featureShown1 = ['VG','AP','PP','RP','NE','DE','NP']
featureShown2 = ['N','V','P','A','X']
class Node(object):
    def __init__(self,text):
        self.text = text
        self.sons = []
        self.upperRelation = None
        # self.id = 0



def CreateTree(inputnode):
    text = inputnode['text']
    node = Node(text)
    end = inputnode['EndOffset']
    node.endOffset = end
    start = inputnode['StartOffset']
    node.startOffset = start
    features = inputnode['features']
    node.features = features
    # id = random.randint(1,1001)
    # while id in randomSet:
    #     id = random.randint(1,1001)
    # randomSet.add(id)
    # node.id = id
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
                    if son.text == node.text and son.startOffset == node.startOffset:
                        continue
                    element = []
                    # text = son.text
                    # if not textSet.add(text): # add set not successfully due to text duplicate
                    # if text in textSet:
                    text = {}
                    word = son.text + str(son.startOffset)
                    # word = str(son.id)
                    v = 'v'
                    f = 'f'
                    text.update({v: word})
                    fValue = son.text
                    # text.update({f: fValue})

                    # upper relationship
                    relation = ""
                    if son.upperRelation:
                        try:
                            relation = son.upperRelation[son.upperRelation.index(".") + 1:]
                        except ValueError as e:
                            relation = son.upperRelation
                            logging.error("The upperRelation is:" + str(son.upperRelation) + " There is no . in it. might need to check rule.")
                        # fValue += '<div style="color:red; font-style:italic">' + relation + '</div>'
                        #text.update({f: fValue})
                        hasRelation = True
                    elif hasRelation or (node.sons.index(son) == 0 and relationExists):
                        # print("hasRelation is true")
                        relation = 'H'
                        #fValue += '<div style="color:red; font-style:italic">' + relation + '</div>'
                        #text.update({f: fValue})
                        hasRelation = False

                    # POS notation, feature 0,1,2,3
                    hasCL = False
                    for feature in son.features:
                        if feature=="3":
                            if  relation!="":
                                fValue += '<div style="color:red; font-style:italic">' + 'CL' + ' (' + relation + ')'  + '</div>'
                            else:
                                fValue += '<div style="color:red; font-style:italic">' + 'CL' + '</div>'
                            hasCL = True
                            break

                    hasVP = False
                    for feature in son.features:
                        if feature=='VP' and hasCL == False:
                            if relation != "":
                                fValue += '<div style="color:red; font-style:italic">' + feature + ' (' + relation + ')' + '</div>'
                            else:
                                fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
                            hasVP = True
                            break

                    hasFeature1 = False
                    for feature in son.features:
                        if feature in featureShown1 and hasCL == False and hasVP == False:
                            if relation != "":
                                fValue += '<div style="color:red; font-style:italic">' + feature + ' (' + relation + ')' + '</div>'
                            else:
                                fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
                            hasFeature1 = True
                            break

                    hasFeature2 = False
                    for feature in son.features:
                        if feature in featureShown2 and hasCL == False and hasVP == False and hasFeature1 == False:
                            if relation != "":
                                fValue += '<div style="color:red; font-style:italic">' + feature + ' (' + relation + ')' + '</div>'
                            else:
                                fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
                            hasFeature2 = True
                            break

                    if hasCL == False and hasVP == False and hasFeature1 == False and hasFeature2 == False and relation!="":
                        fValue += '<div style="color:red; font-style:italic">' + "("+relation +")"+ '</div>'

                    text.update({f: fValue})

                    parent = node.text+str(node.startOffset)
                    if parent == nodeList[-1].text + str(nodeList[-1].startOffset) :
                        if (nodeList[-1].text + str(nodeList[-1].startOffset)) == (nodeList[-2].text + str(nodeList[-2].startOffset)):
                            parentNode = nodeList[-2]
                            parent = {}
                            parent.update({'v':parentNode.text + str(parentNode.startOffset)})
                            fValue = parentNode.text
                            hasCL = False
                            for feature in parentNode.features:
                                if feature == "3":
                                    fValue += '<div style="color:red; font-style:italic">' + 'CL' + '</div>'
                                    hasCL = True
                                    break

                            hasVP = False
                            for feature in parentNode.features:
                                if feature == 'VP' and hasCL == False:
                                    fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
                                    hasVP = True
                                    break

                            hasFeature1 = False
                            for feature in parentNode.features:
                                if feature in featureShown1 and hasCL == False and hasVP == False:
                                    fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
                                    hasFeature1 = True
                                    break

                            hasFeature2 = False
                            for feature in parentNode.features:
                                if feature in featureShown2 and hasCL == False and hasVP == False and hasFeature1 == False:
                                    fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
                                    hasFeature2 = True
                                    break

                            parent.update({'f': fValue})

                        else:
                            parentNode = nodeList[-1]
                            parent = parentNode.text
                        rootElement = []
                        rootElement.append(parent)
                        rootElement.append('')
                        feature = "features: "
                        for f in parentNode.features:
                            feature += f + " "
                        tooltip = feature + "EndOffset :" + str(parentNode.endOffset) +" " + "StartOffset :" + str(parentNode.startOffset)
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
    json_input = '{"EndOffset": 8, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 8, "StartOffset": 0, "features": ["vtThing", "3", "perF", "perVobj", "perfect", "saturated", "chg", "Pred", "v", "ho", "chgPoss", "VG", "take", "buy", "pred", "geiV", "act"], "sons": [{"EndOffset": 1, "StartOffset": 0, "UpperRelationship": "^.S", "features": ["0", "n", "NP", "npr", "XP", "oral", "per", "phy", "xC", "perOrg", "anim", "vac", "PRP"], "text": "我"}, {"EndOffset": 8, "StartOffset": 1, "features": ["vtThing", "3", "chgPoss", "perF", "VG", "take", "buy", "perVobj", "VP", "perfect", "saturated", "pred", "v", "chg", "Pred", "geiV", "ho", "act"], "sons": [{"EndOffset": 3, "StartOffset": 1, "features": ["vtThing", "ho", "V", "chgPoss", "perF", "VG", "take", "buy", "perVobj", "VP", "perfect", "saturated", "pred", "XP", "chg", "Pred", "geiV", "v", "act"], "sons": [{"EndOffset": 2, "StartOffset": 1, "features": ["vtThing", "0", "perF", "perVobj", "perfect", "saturated", "chg", "Pred", "v", "V", "chgPoss", "VG", "take", "buy", "pred", "XP", "geiV", "act", "vt"], "text": "买"}, {"EndOffset": 3, "StartOffset": 2, "UpperRelationship": "^.X", "features": ["0", "vac", "EX", "xC", "V0"], "text": "了"}], "text": "买了"}, {"EndOffset": 8, "StartOffset": 3, "UpperRelationship": "^.O", "features": ["chem", "n", "npr", "NP", "XP", "phy", "tool", "artifact", "solution", "prod", "inanim"], "sons": [{"EndOffset": 6, "StartOffset": 3, "UpperRelationship": "^.M", "features": ["0", "n", "npr", "phy", "org", "perOrg", "com", "group", "N", "brand", "NNP"], "text": "香奈儿"}, {"EndOffset": 8, "StartOffset": 6, "features": ["0", "chem", "n", "npr", "NP", "XP", "phy", "tool", "artifact", "solution", "N", "prod", "inanim"], "text": "眉笔"}], "text": "香奈儿眉笔"}], "text": "买了香奈儿眉笔"}], "text": "我买了香奈儿眉笔"}], "text": "我买了香奈儿眉笔"}'
    # showGraph(json_input)
    dataRows = orgChart(json_input)
    print(str(dataRows))







