#Note: DAG is being used in this process, but actually the dependancytree is not pure DAG:
#    some of the graph can be cyclic.
# so it is required to have "root".

import jsonpickle, copy
import utils    #for the Feature_...
#from utils import *
import Lexicon

class SubGraph: #only used in initial transform.
    def __init__(self, node):
        self.headID = -1
        self.leaves = []
        self.startnode = node


    def __str__(self):
        output = "{"
        for relation in self.leaves:
            output += str(relation[0]) + "-" + relation[1] + "->" + str(self.headID) + "; "
        output += "}" + self.startnode.text
        return output


class DependencyTree:
    def __init__(self):
        self.nodes = {}
        self.roots = []
        #self.graph = {}     #son ->edge->parent
        self.subgraphs = []     #this is only used when constructing from nodelist.
        self.graph = []

    def transform(self, nodelist):    #Transform from SentenceLinkedList to Depen
        root = nodelist.head
        if root.text == '':
            root = root.next
        _subgraphs = []
        # Collect all the leaf nodes into self.nodes.
        while root != nodelist.tail:
            #each "root" has a tree, independent from others.
            node = root
            nodestack = set()
            while node:
                if node.sons:
                    if node.next:
                        nodestack.add(node.next)
                    node = node.sons[0]
                else:
                    if utils.FeatureID_JM not in node.features:
                        self.nodes.update({node.ID : copy.copy(node)})      # add leaf node to self.nodes.

                    if node == root:    #if node is in root level, don't get next.
                        if nodestack:
                            node = nodestack.pop()
                        else:
                            node = None
                        continue

                    node = node.next
                    if node == None and nodestack:
                        node = nodestack.pop()

            _subgraphs.append(SubGraph(root))

            self.roots.append(root.ID)
            root = root.next

        #filling up the subgraphs.
        while _subgraphs:
            subgraph = _subgraphs.pop()
            node = subgraph.startnode

            if node.sons:
                subnode = node.sons[0]
                nodestack = set()
                while subnode:
                    if subnode.sons:
                        if utils.FeatureID_H not in subnode.features:
                            _subgraphs.append(SubGraph(subnode))    # non-leaf, non-H. it is a subgraph.
                            subgraph.leaves.append([subnode.ID, subnode.UpperRelationship])
                            subnode = subnode.next
                            if subnode == None and nodestack:
                                subnode = nodestack.pop()
                        else:
                            if subnode.next:
                                nodestack.add(subnode.next)
                            subnode = subnode.sons[0]
                    else:
                        if utils.FeatureID_H in subnode.features:
                            subgraph.headID = subnode.ID
                            subnode.features.update(subgraph.startnode.features)
                            #Lexicon.ApplyWordLengthFeature(subnode)
                        else:
                            if utils.FeatureID_JM not in subnode.features:
                                subgraph.leaves.append([subnode.ID, subnode.UpperRelationship])
                        subnode = subnode.next
                        if subnode == None and nodestack:
                            subnode = nodestack.pop()
            else:
                subgraph.headID = subgraph.startnode.ID

            self.subgraphs.append(subgraph)     # add to the permanent subgraphs

        # now set the roots, from the top node to the head.
        for i in range(len(self.roots)):
            if self.roots[i] not in self.nodes:
                for _subgraph in self.subgraphs:
                    if _subgraph.startnode.ID == self.roots[i]:
                        self.roots[i] = _subgraph.headID

        # now process the non-leaf, non-H points.
        # copy information to self.graph
        for subgraph in self.subgraphs:
            for relation in subgraph.leaves:
                if relation[0] not in self.nodes:
                    for _subgraph in self.subgraphs:
                        if _subgraph.startnode.ID == relation[0]:
                            relation[0] = _subgraph.headID
                            print("The previous ID" + str(relation[0]) + " is replaced by head ID" + str(_subgraph.headID))
                            break
                self.graph.append([str(relation[0]), relation[1], str(subgraph.headID)])

    def __str__(self):
        output = "Nodes:\n"
        for node in self.nodes:
            output += "\t" + str(node) + ":" + self.nodes[node].text + "\n"
        output += "Roots:\n"
        for root in self.roots:
            output += "\t" + str(root) + ":" + self.nodes[root].text + "\n"
        output += "subgraphs:\n"
        for subgraph in self.subgraphs:
            output += "\t" + str(subgraph) + "\n"

        output += "digraph output:\n"
        output += self.digraph()
        return output

    def digraph(self):
        output = "{"
        for node in self.nodes:
            output +=  "{} [label=\"{}\" tooltip=\"{}\"];\n".format(node, self.nodes[node].text, self.nodes[node].GetFeatures())

        output += "//edges:\n"
        for edge in self.graph:
            output += "\t{}->{} [label=\"{}\"];\n".format(edge[2], edge[0], edge[1])

        output += "}"
        return output


if __name__ == "__main__":
    import FeatureOntology
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    # import ProcessSentence
    # ProcessSentence.LoadCommon()
    #
    # Sentence = "广州革命政府领导国民革命军进行了北伐战争"
    # nodelist, _ = ProcessSentence.LexicalAnalyze(Sentence)
    #
    # nodelist_str = jsonpickle.dumps(nodelist)
    # print(nodelist_str)

    #Sentence = "被他巧妙躲了过去"
    ###nodelist_str="""{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 7, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 22, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "被", "features": {"py/set": [2193, 162, 386, 1523, 498, 1, 104, 2314, 1099]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "巧妙", "ID": 11, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "", "atom": "他巧妙躲了过去", "features": {"py/set": [260, 261, 1732, 7, 264, 265, 9, 1099, 1734, 204, 1872, 1681, 533, 23, 1566, 1569, 227, 37, 102, 171, 1901, 880, 1586, 381, 437, 1718, 504, 1081, 506, 508, 509, 1599]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 8, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [23, 101, 22, 102, 185, 2314]}, "next": null, "norm": "", "prev": {"py/id": 3}, "sons": [], "text": ""}, "norm": "他巧妙躲了过去", "prev": {"py/id": 2}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "巧妙", "ID": 10, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "他巧妙", "features": {"py/set": [260, 261, 7, 264, 265, 9, 1681, 533, 1566, 1569, 37, 171, 1586, 437, 1718, 1081, 1599, 1732, 1734, 1099, 204, 1872, 89, 227, 1901, 880, 502, 381]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "躲", "ID": 9, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "NX", "atom": "躲了过去", "features": {"py/set": [225, 930, 1121, 260, 2214, 102, 234, 1099, 2187, 235, 236, 2162, 242, 23, 148, 1846, 503]}, "next": null, "norm": "躲了过去", "prev": {"py/id": 7}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 4, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "躲", "features": {"py/set": [1, 260, 1095, 1099, 2187, 89, 225, 930, 1121, 2214, 234, 235, 236, 2162, 498, 1846, 1593]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 5, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "X", "atom": "了", "features": {"py/set": [1, 386, 259, 226, 258, 2314, 2187, 1099, 106, 2193, 498, 1523, 22, 222]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 6, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "B", "atom": "过去", "features": {"py/set": [1, 386, 259, 2314, 2187, 1099, 2193, 21, 23, 280, 1500, 1438, 31, 1440, 1505, 226, 102, 106, 2092, 1901, 302, 2098, 1523, 501, 191]}, "next": null, "norm": "过去", "prev": {"py/id": 11}, "sons": [], "text": "过去"}, "norm": "了", "prev": {"py/id": 10}, "sons": [], "text": "了"}, "norm": "躲", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 3, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "H", "atom": "巧妙", "features": {"py/set": [1, 1732, 5, 1734, 7, 264, 265, 8, 1099, 260, 261, 9, 204, 1872, 1681, 533, 89, 1566, 1569, 227, 171, 1901, 880, 1586, 180, 437, 1718, 501, 1081, 381, 1599]}, "next": null, "norm": "巧妙", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 2, "Head0Text": "", "ID": 2, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "S", "atom": "他", "features": {"py/set": [129, 1601, 386, 260, 261, 259, 1, 199, 2314, 1099, 143, 144, 2193, 18, 340, 213, 1499, 1629, 1438, 1447, 106, 172, 498, 1523, 1594]}, "next": {"py/id": 15}, "norm": "他", "prev": {"py/id": 2}, "sons": [], "text": "他"}, "sons": [], "text": "巧妙"}, "sons": [], "text": "躲"}, {"py/id": 11}, {"py/id": 12}], "text": "躲了过去"}, "norm": "他巧妙", "prev": {"py/id": 2}, "sons": [{"py/id": 16}, {"py/id": 15}], "text": "他巧妙"}, {"py/id": 8}], "text": "他巧妙躲了过去"}, "norm": "被", "prev": {"py/id": 1}, "sons": [], "text": "被"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}, "3": {"py/id": 4}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["被", ""]}, {"py/tuple": ["他巧妙躲了过去", "巧妙"]}, {"py/tuple": ["", ""]}], "size": 4, "tail": {"py/id": 4}}"""
    #Sentence = "广州革命政府领导国民革命军进行了北伐战争"
    nodelist_str = """{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 9, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 22, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 20, "Head0Text": "领导", "ID": 17, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "广州革命政府领导命军进行了北伐战争", "features": {"py/set": [264, 1683, 2326, 23, 1690, 539, 541, 286, 543, 544, 545, 1568, 547, 287, 37, 172, 1972, 1718, 2265, 90, 1505, 2273, 229, 102, 104, 2286, 2290, 372, 2295, 1149, 2430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 20, "Head0Text": "", "ID": 10, "StartOffset": 20, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [2418, 23, 101, 22, 102, 186]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "广州革命政府领导国民革命军进行了北伐战争", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "政府", "ID": 15, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "S", "atom": "广州革命政府", "features": {"py/set": [135, 201, 143, 144, 18, 1619, 215, 1690, 539, 541, 542, 286, 1568, 1505, 287, 104, 1514, 106, 1138, 180, 1718, 1529, 1149]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 20, "Head0Text": "领导", "ID": 16, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "领导命军进行了北伐战争", "features": {"py/set": [264, 265, 1683, 2326, 23, 1690, 539, 541, 286, 543, 544, 545, 1568, 547, 172, 1972, 181, 1718, 2265, 90, 89, 1505, 2273, 229, 102, 2286, 2290, 372, 2295, 1149, 2430]}, "next": null, "norm": "领导国民革命军进行了北伐战争", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "领导", "ID": 11, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "领导命军", "features": {"py/set": [90, 264, 265, 1683, 2326, 2265, 1690, 539, 89, 541, 286, 543, 544, 1568, 1505, 2273, 228, 229, 2286, 2290, 372, 1972, 1718, 2295, 1149, 2430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 20, "Head0Text": "进行", "ID": 14, "StartOffset": 13, "TempPointer": "", "UpperRelationship": "C", "atom": "进行了北伐战争", "features": {"py/set": [264, 265, 2317, 18, 2326, 23, 2265, 539, 541, 1118, 543, 544, 286, 32, 1123, 739, 2084, 1126, 1703, 102, 106, 49, 2290, 2291, 242, 1972, 1149, 2430]}, "next": null, "norm": "进行了北伐战争", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 16, "Head0Text": "进行", "ID": 12, "StartOffset": 13, "TempPointer": "", "UpperRelationship": "H", "atom": "进行了", "features": {"py/set": [264, 2317, 2326, 89, 2265, 537, 2333, 1118, 286, 1123, 739, 2084, 1126, 1703, 2277, 241, 2290, 2291, 242, 1972, 1149, 2430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 20, "Head0Text": "", "ID": 8, "StartOffset": 16, "TempPointer": "", "UpperRelationship": "O", "atom": "北伐战争", "features": {"py/set": [1568, 1, 161, 287, 102, 154, 1514, 106, 143, 144, 18, 23, 538, 123, 1149, 286, 127]}, "next": null, "norm": "北伐战争", "prev": {"py/id": 12}, "sons": [], "text": "北伐战争"}, "norm": "进行了", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "", "ID": 6, "StartOffset": 13, "TempPointer": "", "UpperRelationship": "H", "atom": "进行", "features": {"py/set": [89, 1, 1123, 739, 228, 1126, 903, 2084, 295, 2345, 1703, 2317, 2290, 2291, 536, 2265, 1149, 1118]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 16, "Head0Text": "", "ID": 7, "StartOffset": 15, "TempPointer": "", "UpperRelationship": "X", "atom": "了", "features": {"py/set": [224, 1, 421, 229, 106, 2418, 2290, 533, 22, 1149, 2296, 1593, 284, 285]}, "next": null, "norm": "了", "prev": {"py/id": 16}, "sons": [], "text": "了"}, "norm": "进行", "prev": {"py/id": 9}, "sons": [], "text": "进行"}, {"py/id": 17}], "text": "进行了"}, {"py/id": 13}], "text": "进行了北伐战争"}, "norm": "领导国民革命军", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 4, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "领导", "features": {"py/set": [832, 1, 264, 1683, 2326, 536, 89, 2265, 1690, 2333, 1568, 1505, 2273, 228, 229, 2277, 2286, 2290, 372, 1972, 1718, 2295, 1149]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "", "ID": 5, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "O", "atom": "命军", "features": {"py/set": [1, 130, 131, 1479, 1482, 399, 18, 1619, 1688, 1625, 1690, 539, 540, 154, 286, 1568, 1505, 161, 1514, 106, 1389, 1138, 1718, 1529, 1149, 127]}, "next": null, "norm": "国民革命军", "prev": {"py/id": 21}, "sons": [], "text": "国民革命军"}, "norm": "领导", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 3, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "政府", "features": {"py/set": [1568, 1505, 1, 89, 1514, 1389, 1138, 1619, 180, 1718, 118, 536, 1529, 1690, 1149, 127]}, "next": null, "norm": "政府", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 2, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "M", "atom": "革命", "features": {"py/set": [832, 1, 1992, 8, 1482, 9, 12, 2317, 2326, 536, 2265, 2332, 2333, 286, 1823, 287, 291, 228, 2277, 106, 2290, 115, 1653, 125, 1785, 1149]}, "next": {"py/id": 24}, "norm": "革命", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 2, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "M", "atom": "广州", "features": {"py/set": [1568, 1505, 130, 1, 678, 679, 104, 138, 1514, 1482, 106, 1358, 12, 1361, 115, 125, 536, 1149, 127]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "政府", "ID": 13, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "H", "atom": "革命政府", "features": {"py/set": [1568, 1505, 89, 135, 1514, 1138, 1619, 180, 1718, 1690, 1529, 538, 1149, 286]}, "next": null, "norm": "革命政府", "prev": {"py/id": 26}, "sons": [{"py/id": 25}, {"py/id": 24}], "text": "革命政府"}, "norm": "广州", "prev": {"py/id": 1}, "sons": [], "text": "广州"}, "sons": [], "text": "革命"}, "sons": [], "text": "政府"}, "sons": [], "text": "领导"}, {"py/id": 22}], "text": "领导国民革命军"}, {"py/id": 10}], "text": "领导国民革命军进行了北伐战争"}, "norm": "广州革命政府", "prev": {"py/id": 1}, "sons": [{"py/id": 26}, {"py/id": 27}], "text": "广州革命政府"}, {"py/id": 7}], "text": "广州革命政府领导国民革命军进行了北伐战争"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["广州革命政府领导国民革命军进行了北伐战争", "领导"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}"""
    newnodelist = jsonpickle.loads(nodelist_str)
    print(newnodelist.root().CleanOutput().toJSON())

    x = DependencyTree()
    x.transform(newnodelist)
    print(x)

    # Sentence = "我买了红色的香奈儿眉笔"
    # nodelist, _ = ProcessSentence.LexicalAnalyze(Sentence)
    #
    # nodelist_str = jsonpickle.dumps(nodelist)
    # print(nodelist_str)

    nodelist_str="""{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 20, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 22, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 26, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "我买了红色de香奈儿眉笔", "features": {"py/set": [512, 2051, 260, 261, 2187, 23, 287, 1059, 37, 2214, 2223, 2237, 1599, 2240, 1603, 1608, 1099, 204, 1614, 1872, 594, 1881, 2270, 102, 104, 234, 236, 494, 241, 626, 2162, 504, 506, 508, 510]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 21, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [514, 23, 101, 22, 102, 185, 2314]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "我买了红色的香奈儿眉笔", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 13, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "S", "atom": "我", "features": {"py/set": [129, 1601, 1539, 260, 261, 386, 259, 1, 199, 2314, 1099, 143, 144, 2193, 18, 340, 213, 1499, 1629, 1438, 1447, 104, 106, 172, 498, 1523, 1594]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 25, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "买了红色de香奈儿眉笔", "features": {"py/set": [512, 2051, 260, 2187, 23, 287, 1059, 2214, 2223, 2237, 1599, 2240, 1603, 1608, 1099, 204, 1614, 1872, 594, 1881, 89, 2270, 102, 234, 236, 494, 241, 626, 2162, 242, 504, 506, 508, 510]}, "next": null, "norm": "买了红色的香奈儿眉笔", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "买", "ID": 23, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "买了", "features": {"py/set": [2051, 260, 2187, 287, 1059, 2214, 2223, 2230, 2237, 1599, 2240, 1603, 1608, 1099, 1614, 594, 89, 1881, 2270, 234, 235, 236, 494, 241, 626, 2162, 501, 2174]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "眉笔", "ID": 24, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "O", "atom": "红色de香奈儿眉笔", "features": {"py/set": [129, 260, 261, 1099, 1164, 524, 588, 143, 144, 18, 23, 153, 1499, 1629, 1438, 160, 1958, 1447, 1702, 102, 106, 369, 1462, 504, 505, 506, 508, 2111, 510, 511]}, "next": null, "norm": "红色的香奈儿眉笔", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 16, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "M", "atom": "红色", "features": {"py/set": [129, 1, 1412, 390, 264, 1099, 12, 1487, 661, 1754, 1499, 1438, 1312, 1447, 106, 1324, 115, 501, 1462, 1718, 125, 127]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 17, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "X", "atom": "de", "features": {"py/set": [1, 258, 386, 259, 2314, 1099, 2193, 1510, 106, 498, 1523]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "眉笔", "ID": 22, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "香奈儿眉笔", "features": {"py/set": [129, 260, 135, 1099, 1164, 524, 588, 23, 89, 1499, 1629, 1438, 1958, 1447, 1702, 102, 369, 1462, 504, 505, 2111]}, "next": null, "norm": "香奈儿眉笔", "prev": {"py/id": 13}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "", "ID": 18, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "M", "atom": "香奈儿", "features": {"py/set": [1088, 129, 1601, 1, 1447, 1543, 138, 1099, 1515, 106, 12, 1521, 115, 125, 662, 502, 472, 1499, 1629, 127]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 19, "StartOffset": 9, "TempPointer": "", "UpperRelationship": "H", "atom": "眉笔", "features": {"py/set": [129, 1, 1164, 524, 23, 1438, 1958, 1447, 1702, 1324, 1462, 2111, 1099, 588, 89, 1499, 1629, 102, 369, 501, 118, 127]}, "next": null, "norm": "眉笔", "prev": {"py/id": 16}, "sons": [], "text": "眉笔"}, "norm": "香奈儿", "prev": {"py/id": 13}, "sons": [], "text": "香奈儿"}, {"py/id": 17}], "text": "香奈儿眉笔"}, "norm": "的", "prev": {"py/id": 12}, "sons": [], "text": "的"}, "norm": "红色", "prev": {"py/id": 9}, "sons": [], "text": "红色"}, {"py/id": 13}, {"py/id": 14}], "text": "红色的香奈儿眉笔"}, "norm": "买了", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 2, "Head0Text": "", "ID": 14, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "买", "features": {"py/set": [2240, 1, 2051, 1603, 1608, 2187, 1099, 1614, 594, 89, 2270, 287, 225, 1059, 2214, 234, 494, 626, 2162, 498, 2237, 1599]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 15, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "X", "atom": "了", "features": {"py/set": [1, 386, 259, 226, 258, 2314, 2187, 1099, 106, 2193, 498, 1523, 22, 222]}, "next": null, "norm": "了", "prev": {"py/id": 23}, "sons": [], "text": "了"}, "norm": "买", "prev": {"py/id": 6}, "sons": [], "text": "买"}, {"py/id": 24}], "text": "买了"}, {"py/id": 10}], "text": "买了红色的香奈儿眉笔"}, "norm": "我", "prev": {"py/id": 1}, "sons": [], "text": "我"}, {"py/id": 7}], "text": "我买了红色的香奈儿眉笔"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["我买了红色的香奈儿眉笔", "买"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}
    """
    newnodelist = jsonpickle.loads(nodelist_str)
    print(newnodelist.root().CleanOutput().toJSON())

    x = DependencyTree()
    x.transform(newnodelist)
    print(x)