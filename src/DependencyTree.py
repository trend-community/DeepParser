#Note: DAG is being used in this process, but actually the dependancytree is not pure DAG:
#    some of the graph can be cyclic.
# so it is required to have "root".

import FeatureOntology, Lexicon
import utils    #for the Feature_...
from utils import *

class SubGraph:
    head = -1
    leafs = {}
    startnode = None
    def __init__(self, node):
        self.startnode = node

    def __str__(self):
        output = "{"
        for leaf in self.leafs:
            output += str(leaf)
        output += "}"
        return output

class DependencyTree:
    def __init__(self):
        self.nodes = {}
        self.roots = set()
        #self.graph = {}     #son ->edge->parent
        self.subgraphs = []

    def transform(self, nodelist):    #Transform from SentenceLinkedList to Depen
        root = nodelist.head
        if root.text == '':
            root = root.next
        _subgraphs = []
        while root != nodelist.tail:
            #each "root" has a tree, independent from others.
            node = root
            nodestack = set()
            # Collect all the leaf nodes into self.nodes.
            while node:
                if node.sons:
                    if node.next:
                        nodestack.add(node.next)
                    node = node.sons[0]
                else:
                    self.nodes.update({node.ID : node})      # add leaf node to self.nodes.
                    if nodestack:
                        node = nodestack.pop()
                    else:
                        node = None
                    # node = node.next
                    # if node == None and nodestack:
                    #     node = nodestack.pop()

            _subgraphs.append(SubGraph(root))

            self.roots.add(root.ID)
            root = root.next


        while _subgraphs:
            subgraph = _subgraphs.pop()
            node = subgraph.startnode
            nodestack = set()
            while node:
                if node.sons:
                    if utils.FeatureID_H not in node.features:
                        _subgraphs.append(SubGraph(node))    # non-leaf, non-H. it is a subgraph.
                        if nodestack:
                            node = nodestack.pop()
                        else:
                            node = None
                    else:
                        if node.next:
                            nodestack.add(node.next)
                        node = node.sons[0]
                else:
                    if utils.FeatureID_H in node.features:
                        subgraph.head = node.ID
                    else:
                        subgraph.leafs[node.ID] = node.UpperRelationship
                    if nodestack:
                        node = nodestack.pop()
                    else:
                        node = None
            self.subgraphs.append(subgraph)     # add to the permanent subgraphs

    def __str__(self):
        self.nodes = {}
        self.roots = set()
        #self.graph = {}     #son ->edge->parent
        self.subgraphs = []

        output = "Nodes:\n"
        for node in self.nodes:
            output += "\t" + str(node) + "\n"
        output += "Roots:\n"
        for root in self.roots:
            output += "\t" + str(root) + "\n"
        output += "subgraphs:\n"
        for subgraph in self.subgraphs:
            output += "\t" + str(subgraph) + "\n"

        return output


if __name__ == "__main__":
    # import ProcessSentence
    # ProcessSentence.LoadCommon()

    # Sentence = "被巧妙躲了过去"
    # nodelist, _ = ProcessSentence.LexicalAnalyze(Sentence)
    # print(nodelist.root().CleanOutput().toJSON())
    #
    # nodelist_str = jsonpickle.dumps(nodelist)
    # print(nodelist_str)
    nodelist_str='{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {}, "head": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 6, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 22, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "被", "features": {"py/set": [2193, 162, 386, 1523, 498, 1, 104, 2314, 1099]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 2, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "", "atom": "巧妙", "features": {"py/set": [1, 1732, 5, 1734, 7, 264, 265, 1099, 1681, 533, 1566, 1569, 227, 171, 1901, 880, 1586, 437, 1718, 501, 1081, 381, 1599]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "躲", "ID": 8, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "", "atom": "躲了过去", "features": {"py/set": [225, 930, 1121, 260, 2214, 102, 234, 1099, 2187, 235, 236, 2162, 23, 1846, 503]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 7, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [23, 101, 22, 102, 185, 2314]}, "next": null, "norm": "", "prev": {"py/id": 4}, "sons": [], "text": ""}, "norm": "躲了过去", "prev": {"py/id": 3}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 3, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "躲", "features": {"py/set": [1, 260, 1095, 1099, 2187, 89, 225, 930, 1121, 2214, 234, 235, 236, 2162, 498, 1846, 1593]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 4, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "X", "atom": "了", "features": {"py/set": [1, 386, 259, 226, 258, 2314, 2187, 1099, 106, 2193, 498, 1523, 22, 222]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 5, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "B", "atom": "过去", "features": {"py/set": [1, 386, 259, 2314, 2187, 1099, 2193, 21, 23, 280, 1500, 1438, 31, 1440, 1505, 226, 102, 106, 2092, 1901, 302, 2098, 1523, 501, 191]}, "next": {"py/id": 5}, "norm": "过去", "prev": {"py/id": 9}, "sons": [], "text": "过去"}, "norm": "了", "prev": {"py/id": 8}, "sons": [], "text": "了"}, "norm": "躲", "prev": {"py/id": 3}, "sons": [], "text": "躲"}, {"py/id": 9}, {"py/id": 10}], "text": "躲了过去"}, "norm": "巧妙", "prev": {"py/id": 2}, "sons": [], "text": "巧妙"}, "norm": "被", "prev": {"py/id": 1}, "sons": [], "text": "被"}, "norm": "", "prev": null, "sons": [], "text": ""}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["被", ""]}, {"py/tuple": ["巧妙", ""]}, {"py/tuple": ["躲了过去", "躲"]}, {"py/tuple": ["", ""]}], "size": 5, "tail": {"py/id": 5}}'
    newnodelist = jsonpickle.loads(nodelist_str)
    print(newnodelist.root().CleanOutput().toJSON())

    x = DependencyTree()
    x.transform(newnodelist)
    print(x)