import os, logging
import pydot
import json
import time
import random

dir_path = os.path.dirname(os.path.realpath(__file__))


nodeList = []
randomSet = set()
featureShown1 = ['VG','AP','PP','RP','NE','DE']
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
                        if feature=='CL':
                            if  relation!="":
                                fValue += '<div style="color:red; font-style:italic">' + feature + ' (' + relation + ')'  + '</div>'
                            else:
                                fValue += '<div style="color:red; font-style:italic">' + feature + '</div>'
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
                    # parent = str(node.id)
                    # parentNode = None
                    # if parent == nodeList[-2].text + str(nodeList[-2].startOffset):
                    #     parentNode = nodeList[-2]
                    # elif parent == nodeList[-1].text + str(nodeList[-1].startOffset):
                    #     parentNode = nodeList[-1]
                    # if parentNode != None:
                    # if parent == str(nodeList[-1].id) and :
                    if parent == nodeList[-1].text + str(nodeList[-1].startOffset) :
                        if (nodeList[-1].text + str(nodeList[-1].startOffset)) == (nodeList[-2].text + str(nodeList[-2].startOffset)):
                            parentNode = nodeList[-2]
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
    json_input = '{"EndOffset": 22, "StartOffset": 0, "features": [], "sons": [{"EndOffset": 9, "StartOffset": 0, "features": ["phy", "perOrg", "female", "N", "n", "npr"], "sons": [{"EndOffset": 2, "StartOffset": 0, "UpperRelationship": "^.X", "features": ["0", "xpC", "unit", "a", "an", "det0", "property", "DT", "xC", "indexicalW", "content"], "text": "这个"}, {"EndOffset": 4, "StartOffset": 2, "UpperRelationship": "^.M", "features": ["0", "EMO", "vSbVB", "budeliao", "A", "V0", "deBuyu", "con", "vVB", "saturated", "situation", "pred", "attitude", "nt", "nEMOc", "a", "Pred", "can", "sent", "ebla", "property"], "text": "可怜"}, {"EndOffset": 5, "StartOffset": 4, "UpperRelationship": "^.X", "atom": "de", "features": ["0", "UH", "vac", "xC"], "text": "的"}, {"EndOffset": 9, "StartOffset": 5, "features": ["NP", "phy", "perOrg", "XP", "female", "N", "n", "npr"], "sons": [{"EndOffset": 7, "StartOffset": 5, "UpperRelationship": "^.M", "features": ["sent", "0", "A", "pro", "pt"], "text": "年轻"}, {"EndOffset": 9, "StartOffset": 7, "features": ["0", "NP", "phy", "perOrg", "XP", "female", "N", "n", "npr"], "text": "女孩"}], "text": "年轻女孩"}], "text": "这个可怜的年轻女孩"}, {"EndOffset": 10, "StartOffset": 9, "features": ["punc", "0", "CM"], "text": ","}, {"EndOffset": 22, "StartOffset": 10, "features": ["V", "chg", "pro", "succeed", "pt", "sent", "v", "stateV", "plusV"], "sons": [{"EndOffset": 16, "StartOffset": 10, "UpperRelationship": "^.mannerR", "features": ["perF", "V", "Pred", "vVB", "VG", "animF", "v", "vt", "P", "saturated"], "sons": [{"EndOffset": 12, "StartOffset": 10, "features": ["0", "perF", "V", "Pred", "vVB", "VG", "animF", "v", "vt", "P", "VP", "saturated", "xC"], "text": "经过"}, {"EndOffset": 16, "StartOffset": 12, "UpperRelationship": "^.ObjV", "features": ["saturated", "perF", "V", "vi", "Pred", "VG", "animF", "v", "VP", "do", "act"], "sons": [{"EndOffset": 14, "StartOffset": 12, "UpperRelationship": "^.R", "features": ["0", "Pred", "A0", "pro", "RB", "pt", "sent", "N0", "saturated", "pred", "npr"], "text": "努力"}, {"EndOffset": 16, "StartOffset": 14, "features": ["0", "perF", "V", "xx", "vi", "animF", "v", "do", "act"], "text": "拼搏"}], "text": "努力拼搏"}], "text": "经过努力拼搏"}, {"EndOffset": 22, "StartOffset": 16, "features": ["V", "chg", "pro", "succeed", "pt", "sent", "v", "stateV", "plusV"], "sons": [{"EndOffset": 18, "StartOffset": 16, "UpperRelationship": "^.R", "features": ["0", "xC", "vac", "RB"], "text": "终于"}, {"EndOffset": 22, "StartOffset": 18, "features": ["0", "idiom", "V", "chg", "pro", "succeed", "pt", "sent", "v", "stateV", "plusV"], "text": "功成名就"}], "text": "终于功成名就"}], "text": "经过努力拼搏终于功成名就"}], "text": "这个可怜的年轻女孩,经过努力拼搏终于功成名就"}'
    # showGraph(json_input)
    dataRows = orgChart(json_input)
    print(str(dataRows))







