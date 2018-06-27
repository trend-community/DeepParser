#Note: DAG is being used in this process, but actually the dependancytree is not pure DAG:
#    some of the graph can be cyclic.
# so it is required to have "root".

import jsonpickle, copy, logging
import operator
import utils    #for the Feature_...
#from utils import *
import Lexicon
import FeatureOntology

DanziDict = dict()

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
        self._roots = []    #only used when constructing.
        #self.graph = {}     #son ->edge->parent
        self._subgraphs = []     #this is only used when constructing from nodelist.
        self.graph = set()
        self.root = -1

    def transform(self, nodelist):    #Transform from SentenceLinkedList to Depen
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Start to transform:\n {}".format(jsonpickle.dumps(nodelist)))
        root = nodelist.head
        if root.text == '' and utils.FeatureID_JS in root.features:
            root = root.next        #ignore the first empty (virtual) JS node
        _subgraphs = []
        # Collect all the leaf nodes into self.nodes.
        while root != None:
            #each "root" has a tree, independent from others.
            node = root
            nodestack = set()
            while node:
                if node.sons:
                    if len(node.sons) == 2 and len(node.text) == 2 and len(node.sons[0].text) == 1 and len(node.sons[1].text) == 1:
                        DanziDict.update({node: node.sons})
                    if node.next:
                        nodestack.add(node.next)
                    node = node.sons[0]
                else:
                    if not (node.text == '' and utils.FeatureID_JM  in node.features):
                        self.nodes.update({node.ID : copy.deepcopy(node)})      # add leaf node to self.nodes.

                    if node == root:    #if node is in root level, don't get next.
                        if nodestack:
                            node = nodestack.pop()
                        else:
                            node = None
                        continue

                    node = node.next
                    if node == None and nodestack:
                        node = nodestack.pop()
            if not (root.text == '' and utils.FeatureID_JM in root.features):
                _subgraphs.append(SubGraph(root))
                self._roots.append(root.ID)
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
                    else:   # this is a leaf node.
                        subnode = self.nodes[subnode.ID]  #  use the copy in self.nodes to apply feature modification
                        if utils.FeatureID_H in subnode.features:
                            subgraph.headID = subnode.ID
                            subnode.features.update(subgraph.startnode.features)
                            Lexicon.ApplyWordLengthFeature(subnode)
                        else:
                            if not(subnode.text == '' and utils.FeatureID_JM  in subnode.features):
                                subgraph.leaves.append([subnode.ID, subnode.UpperRelationship])
                        subnode = subnode.next
                        if subnode == None and nodestack:
                            subnode = nodestack.pop()
            else:
                subgraph.headID = subgraph.startnode.ID

            self._subgraphs.append(subgraph)     # add to the permanent subgraphs

        # now set the roots, from the top node to the head.
        for i in range(len(self._roots)):
            if self._roots[i] not in self.nodes:
                for _subgraph in self._subgraphs:
                    if _subgraph.startnode.ID == self._roots[i]:
                        self._roots[i] = _subgraph.headID

        # now process the non-leaf, non-H points.
        # copy information to self.graph
        for subgraph in self._subgraphs:
            for relation in subgraph.leaves:
                if relation[0] not in self.nodes:
                    for _subgraph in self._subgraphs:
                        if _subgraph.startnode.ID == relation[0]:
                            relation[0] = _subgraph.headID
                            #print("The previous ID" + str(relation[0]) + " is replaced by head ID" + str(_subgraph.headID))
                            break
                self._AddEdge(relation[0], relation[1], subgraph.headID)

        self._MarkNext()
        self.root = self._roots[0]

    #for multiple roots, mark "next" to make all nodes in one graph.
    def _MarkNext(self):
        if len(self._roots) == 1:
            return

        order = sorted(self._roots, key=lambda nodeid: self.nodes[nodeid].StartOffset)
        for i in range(1, len(order)):
            self._AddEdge(order[i], "next", order[i-1])

        self._roots = [order[0]]

    def __str__(self):
        output = "Nodes:\n"
        for node in self.nodes:
            output += "\t" + str(node) + ":" + self.nodes[node].text + "\n"
        output += "_roots:\n"
        for root in self._roots:
            output += "\t" + str(root) + ":" + self.nodes[root].text + "\n"
        output += "_subgraphs:\n"
        for subgraph in self._subgraphs:
            output += "\t" + str(subgraph) + "\n"

        output += "digraph output:\n{}".format(self.digraph())
        output += "\nRoot: {}".format(self.root)
        return output

    def onlyOneRelation(self, startnode):
        relation = 0
        for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
            if startnode == edge[2]:
                relation = relation + 1

        if relation == 1:
            return True
        return False

    def getDanzi(self, nodeid):
        for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
            if edge[2] == nodeid:
                if  len(self.nodes[nodeid].text) == 1 and len(self.nodes[edge[0]].text) == 1 and self.onlyOneRelation(edge[2]):
                    if self.nodes[edge[0]].StartOffset < self.nodes[nodeid].StartOffset:
                        parent =  self.nodes[edge[0]].text + self.nodes[nodeid].text
                    else:
                        parent =  self.nodes[nodeid].text + self.nodes[edge[0]].text

                    for node in DanziDict.keys():
                        if node.text == parent:
                            return parent
        return None

    #the output is in DOT language, compatible with Graphviz, Viz.js, d3-graphviz.
    def digraph(self, Type='graph'):
        if logging.root.isEnabledFor(logging.INFO):
            logging.info("Start making diagraph of {}. graph is:{}".format(Type, self.graph))
        output = ""
        if Type == 'simplegraph' :
            for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
                output += """{}{{{}->{}}}; """.format(edge[1],
                                self.nodes[edge[2]].text,
                                self.nodes[edge[0]].text   )
        elif Type == 'simple2':
            for nodeid in sorted(self.nodes):
                output += """{}"{}" """.format(nodeid, self.nodes[nodeid].text)
            output += "{"
            for edge in sorted(self.graph, key= lambda e: e[2]):
                output += """{}->{} [{}]; """.format(edge[2], edge[0], edge[1])
            output += "}"
        else:
            output = "{"
            for nodeid in sorted(self.nodes):
                danzi = self.getDanzi(nodeid)
                if danzi:
                    output +=  "{} [label=\"{}\" tooltip=\"{}\"];\n".format(nodeid, danzi, self.nodes[nodeid].GetFeatures())
                else:
                    output += "{} [label=\"{}\" tooltip=\"{}\"];\n".format(nodeid, self.nodes[nodeid].text,
                                                                           self.nodes[nodeid].GetFeatures())

            output += "//edges:\n"
            for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
                    output += "\t{}->{} [label=\"{}\"];\n".format(edge[2], edge[0], edge[1])

            output += "}"
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("output = {}".format(output))
        return output

    def _AddEdge(self, node1id, relation, node2id):
        #find the write relation to add, if already have a child relation for the same nodes.
        self.graph.add((node1id, relation, node2id, FeatureOntology.GetFeatureID(relation)))

        #Set the parent to have the relation.
        hasFeatureID = FeatureOntology.GetFeatureID("has" + relation)
        if hasFeatureID >= 0:
            self.nodes[node2id].ApplyFeature(hasFeatureID)
        else:
            logging.error("There is no has{} feature in the feature.txt!".format(relation))

    def _RemoveEdge(self, node1id, relation, node2id):
        relationid = FeatureOntology.GetFeatureID(relation)

        for edge in [ x for x in self.graph if x[0] == node1id and x[2] == node2id]:
            if relationid == edge[3] or relationid in FeatureOntology.SearchFeatureOntology(edge[3]).ancestors:
                self.graph.remove(edge)

    #because the "|" sign in SubtreePointer is expanded during compilation(_ExpandOrToken(OneList))
    #it is not longer process here.
    def FindPointerNode(self, openID, SubtreePointer):
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Dag.FindPointerNode for {}".format(SubtreePointer))
        if SubtreePointer[0] == '^':
            SubtreePointer = SubtreePointer[1:]

        nodeID = None
        for AndCondition in SubtreePointer.split("+"):
            Negation = False
            if len(AndCondition) > 1 and AndCondition[0] == "!":
                logging.warning("FindPointerNode: Negation! {}".format(SubtreePointer))
                Negation = True
                AndCondition = AndCondition[1:]

            if "." in AndCondition:
                pointer, relations = AndCondition.split(".", 1)
            else:
                pointer, relations = [AndCondition, ""]
            #pointers = SubtreePointer.split(".")  # Note: here Pointer (subtreepointer) does not have "^"
            #logging.debug("tree:{}".format(pointers))
            # if len(pointers) <=1:
            #     #logging.error("Should have more than 1 pointers! Can't find {} in graph {}".format(SubtreePointer, self.graph))
            #     return openID
            nodeID = None
            if pointer == '':
                nodeID = openID
            else:
                #logging.info("Finding pointer node {} from TempPointer".format(pointers[0]))
                for nodeid in sorted(self.nodes):
                    #logging.debug("DAG.FindPointerNode: evaluating temppointer {} with pointer {}".format(self.nodes[nodeid].TempPointer, pointer))
                    if self.nodes[nodeid].TempPointer == "^"+pointer:
                        nodeID = nodeid
                        break
            if nodeID and relations:
                for relation in relations.split("."):
                    relationid = FeatureOntology.GetFeatureID(relation)
                    Found = False
                    for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
                        #logging.debug("Evaluating edge{} with relation {}, node {}".format(edge, relation, nodeID))
                        if edge[2] == nodeID:
                            if relationid == edge[3]: # or relationid in FeatureOntology.SearchFeatureOntology(edge[3]):
                                nodeID = edge[0]
                                Found = True
                                if logging.root.isEnabledFor(logging.DEBUG):
                                    logging.debug("   Found!")
                                break
                            else:
                                edgerelationnode = FeatureOntology.SearchFeatureOntology(edge[3])
                                if edgerelationnode and relationid in edgerelationnode.ancestors:
                                    nodeID = edge[0]
                                    Found = True
                                    if logging.root.isEnabledFor(logging.DEBUG):
                                        logging.debug("   Found ontology ancesstor relation!")
                                    break

                    if not Found:
                        if not Negation:
                            return None
                        #logging.warning("Failed to find pointer {} in graph {}".format(SubtreePointer, self))
                        #return None     #Can't find the pointers.

                    #logging.info("Found this node {} for these pointers:{}".format(nodeID, pointers))

        if nodeID:
            return nodeID
        else:
            return None


    def ClearVisited(self):
        for nodeid in self.nodes:
            self.nodes[nodeid].visited = False


    def ClearApplied(self):
        for nodeid in self.nodes:
            self.nodes[nodeid].applied = False


    def TokenMatch(self, Rule, nodeID, ruletoken, OpenNodeID):
        #logging.debug("DAG.TokenMatch: comparint ruletoken {} with nodeid {}".format(ruletoken, self.nodes[nodeID]))
        import LogicOperation
        logicmatch = LogicOperation.LogicMatch_notpointer(self.nodes[nodeID], ruletoken)
        if not logicmatch:
            return False
        #might need open node for pointer
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Dag.TokenMatch for SubtreePointer {} in rule token {}".format(ruletoken.SubtreePointer, ruletoken))
        if not ruletoken.SubtreePointer:
            return True

        for AndCondition in ruletoken.SubtreePointer.split("+"):
            Negation = False
            #logging.warning("AndCondition:{}".format(AndCondition))
            if AndCondition[0] == "!":
                logging.warning("FindPointerNode: Negation! {}".format(Rule.SubtreePointer))
                Negation = True
                AndCondition = AndCondition[1:]

            if "." in AndCondition:
                pointer, relations = AndCondition.split(".", 1)
            else:
                pointer, relations = [AndCondition, ""]
            #pointers = SubtreePointer.split(".")  # Note: here Pointer (subtreepointer) does not have "^"
            #logging.debug("tree:{}".format(pointers))
            # if len(pointers) <=1:
            #     #logging.error("Should have more than 1 pointers! Can't find {} in graph {}".format(SubtreePointer, self.graph))
            #     return openID
            nodeID = None
            if pointer == '':
                nodeID = OpenNodeID
            else:
                logging.info("Looking for pointer node {} from TempPointer".format(pointer[0]))
                for nodeid in sorted(self.nodes):
                    logging.debug("DAG.FindPointerNode: evaluating temppointer {} with pointer {}".format(self.nodes[nodeid].TempPointer, pointer))
                    if self.nodes[nodeid].TempPointer == "^"+pointer:
                        nodeID = nodeid
                        break

            if nodeID and relations:
                for relation in relations.split("."):
                    relationid = FeatureOntology.GetFeatureID(relation)
                    Found = False
                    for edge in sorted(self.graph, key=operator.itemgetter(2, 1, 0)):
                        #logging.debug("Evaluating edge{} with relation {}, node {}".format(edge, relation, nodeID))
                        if edge[2] == nodeID:
                            if relationid == edge[3]:
                                nodeID = edge[0]
                                Found = True
                                if logging.root.isEnabledFor(logging.DEBUG):
                                    logging.debug("   Found!")
                                break
                            else:
                                edgerelationnode = FeatureOntology.SearchFeatureOntology(edge[3])
                                if edgerelationnode and relationid in edgerelationnode.ancestors:
                                    nodeID = edge[0]
                                    Found = True
                                    if logging.root.isEnabledFor(logging.DEBUG):
                                        logging.debug("   Found ontology ancesstor relation!")
                                    break
                    #logging.debug("After evaluating all graph for {}, Found is {}".format(relation, Found))
                    if not Found and not Negation:
                        if logging.root.isEnabledFor(logging.DEBUG):
                            logging.debug(
                                "Dag.TokenMatch(): False because can't find the pointer and Negation is False")
                        return False
                        # logging.warning("Failed to find pointer {} in graph {}".format(SubtreePointer, self))
                        # return None     #Can't find the pointers.

                    # logging.info("Found this node {} for these pointers:{}".format(nodeID, pointers))

            if (not Negation and nodeID) or ( Negation and not nodeID) :
                if logging.root.isEnabledFor(logging.DEBUG):
                    logging.debug("Dag.TokenMatch(): True because Negation is {} and nodeID is {}".format(Negation, nodeID))
                return True
            else:
                if logging.root.isEnabledFor(logging.DEBUG):
                    logging.debug("Dag.TokenMatch(): False because Negation is {} and nodeID is {}".format(Negation, nodeID))
                return False


    def ApplyDagActions(self, OpenNode, node, actinstring):
        #self.FailedRuleTokens.clear()
        Actions = actinstring.split()
        #logging.debug("Word:" + self.text)

        if "^.---" in Actions:
            #logging.info("DAG Action: Removing all edges to this node {}. before:{}".format(node.ID, self.graph))
            self.graph = set([edge for edge in self.graph if edge[0] != node.ID])
            Actions.pop(Actions.index("^.---"))

        HasBartagAction = False

        for Action in Actions:
            if Action[0] == '^':
                ParentPointer = Action[:Action.rfind('.')]  #find pointer up the the last dot "."
                parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer)
                #logging.warning("DAG Action: This action {} to apply, parent id={}".format(Action, parentnodeid))
                if Action[-1] == "-":   # remove
                    relation = Action[Action.rfind('.')+1:-1]
                    self._RemoveEdge(node.ID, relation, parentnodeid)
                else:
                    relation = Action[Action.rfind('.')+1:]
                    newedge = [node.ID, relation, parentnodeid]
                    if logging.root.isEnabledFor(logging.DEBUG):
                        logging.debug("DAG Action:Adding new edge: {}".format(newedge))

                    self._AddEdge(node.ID, relation, parentnodeid)

                    RelationActionID = FeatureOntology.GetFeatureID(relation)
                    if RelationActionID != -1:
                        node.ApplyFeature(RelationActionID)
                    else:
                        logging.warning(
                            "Wrong Relation Action to apply: {} in action string: {}".format(relation, actinstring))
                continue

            if Action[-1] == "-":
                FeatureID = FeatureOntology.GetFeatureID(Action.strip("-"))
                if FeatureID in node.features:
                    node.features.remove(FeatureID)
                continue

            if Action[-1] == "+":
                if Action[-2] == "+":
                    if Action[-3] == "+":    #"+++"
                        logging.error("There should be no +++ operation in DAG.")
                    else:                   #"X++":
                        FeatureID = FeatureOntology.GetFeatureID(Action.strip("++"))
                        node.ApplyFeature(FeatureID)
                else:                       #"X+"
                    for bar0id in FeatureOntology.BarTagIDs[0]:
                        if bar0id in node.features:
                            node.features.remove(bar0id)

                    for bar0id in [utils.FeatureID_AC, utils.FeatureID_NC, utils.FeatureID_VC]:
                        if bar0id in node.features:
                            node.features.remove(bar0id)

                    FeatureID = FeatureOntology.GetFeatureID(Action.strip("+"))
                    node.ApplyFeature(FeatureID)
                continue

            if Action[0] == '\'':
                #Make the norm of the token to this key
                node.norm = Action[1:-1]
                continue
            if Action[0] == '/':
                #Make the atom of the token to this key
                node.atom = Action[1:-1]
                continue
            ActionID = FeatureOntology.GetFeatureID(Action)
            if ActionID != -1:
                node.ApplyFeature(ActionID)
            else:
                logging.warning("Wrong Action to apply:" + Action +  " in action string: " + actinstring)

        if HasBartagAction:     #only process bartags if there is new bar tag++
            FeatureOntology.ProcessBarTags(node.features)


if __name__ == "__main__":

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    # import ProcessSentence
    # ProcessSentence.LoadCommon()
    #
    # Sentence = "保罗法狄（BAOLUOFADI）字母条纹圆领短袖T恤"
    #
    # nodelist, _, _ = ProcessSentence.LexicalAnalyze(Sentence)
    #
    # nodelist_str = jsonpickle.dumps(nodelist)
    # print(nodelist_str)
    #

    # Sentence = "为什么是他不是她？"
    nodelist_str = """{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 8, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 105, 22]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "是", "ID": 15, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "为什么是他不是她？", "features": {"py/set": [2304, 2432, 1162, 2444, 272, 22, 23, 2331, 548, 2340, 550, 293, 552, 294, 554, 556, 37, 430, 175, 295, 2105, 193, 1986, 453, 1607, 1366, 102, 2279, 103, 105, 250, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "", "ID": 9, "StartOffset": 9, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [192, 2432, 103, 23, 102, 22]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "为什么是他不是她?", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "是", "ID": 14, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "H", "atom": "为什么是他不是她", "features": {"py/set": [2304, 2432, 1986, 453, 1607, 1162, 2444, 272, 1366, 90, 2331, 548, 2340, 550, 293, 552, 294, 554, 555, 2279, 105, 430, 250, 1064, 175, 2105, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "", "ID": 7, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "X", "atom": "？", "features": {"py/set": [192, 193, 1, 292, 102, 103, 1162, 107, 22, 23, 542]}, "next": null, "norm": "?", "prev": {"py/id": 6}, "sons": [], "text": "？"}, "norm": "为什么是他不是她", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "R", "atom": "为什么", "features": {"py/set": [193, 546, 1, 194, 198, 1607, 200, 2409, 1162, 105, 107, 12, 430, 175, 13, 1785, 2393, 1979, 220, 2398]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "是", "ID": 13, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是他不是她", "features": {"py/set": [2304, 2432, 1162, 2444, 272, 273, 2331, 548, 549, 2340, 293, 294, 430, 2105, 1986, 453, 1607, 203, 1877, 1366, 90, 2279, 1023]}, "next": null, "norm": "是他不是她", "prev": {"py/id": 10}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "是", "ID": 12, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是他", "features": {"py/set": [2304, 2432, 1986, 453, 1607, 1162, 2444, 272, 273, 1366, 90, 2331, 545, 2340, 293, 294, 2279, 2347, 430, 2291, 2105, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "是", "ID": 11, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "CN", "atom": "不是她", "features": {"py/set": [2304, 2432, 1986, 2435, 453, 1607, 1162, 2444, 1550, 272, 273, 1366, 2331, 2105, 546, 2340, 293, 294, 2279, 40, 2347, 430, 2291, 250, 1023]}, "next": null, "norm": "不是她", "prev": {"py/id": 13}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "是", "ID": 10, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "H", "atom": "不是", "features": {"py/set": [2304, 545, 2432, 293, 453, 1607, 2279, 249, 1162, 294, 90, 2444, 1550, 430, 1366, 2105, 250, 2331, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 6, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "CN", "atom": "她", "features": {"py/set": [2432, 1, 2435, 1732, 2310, 1607, 1162, 144, 145, 1052, 542, 1697, 293, 294, 295, 1704, 40, 1582, 1519, 176, 430, 1528, 380]}, "next": null, "norm": "她", "prev": {"py/id": 16}, "sons": [], "text": "她"}, "norm": "不是", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 3, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "O", "atom": "他", "features": {"py/set": [2432, 1, 1732, 2310, 1607, 1162, 144, 145, 18, 157, 542, 1697, 164, 293, 294, 295, 1704, 107, 1582, 1519, 176, 430, 1528, 380]}, "next": null, "norm": "他", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 2, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是", "features": {"py/set": [2304, 2432, 1, 453, 2310, 1607, 293, 2279, 1098, 1162, 236, 430, 1366, 2105, 90, 2331, 542, 1023]}, "next": {"py/id": 19}, "norm": "是", "prev": {"py/id": 10}, "sons": [], "text": "是"}, "sons": [], "text": "他"}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 4, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "R", "atom": "不", "features": {"py/set": [2432, 1, 194, 198, 1607, 200, 1162, 12, 13, 527, 542, 293, 107, 430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 5, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "是", "features": {"py/set": [2304, 2432, 1, 2310, 1162, 1550, 2331, 542, 293, 430, 2105, 453, 1607, 1098, 203, 1877, 1366, 90, 2279, 236, 1023]}, "next": null, "norm": "是", "prev": {"py/id": 24}, "sons": [], "text": "是"}, "norm": "不", "prev": {"py/id": 19}, "sons": [], "text": "不"}, {"py/id": 25}], "text": "不是"}, {"py/id": 17}], "text": "不是她"}, "norm": "是他", "prev": {"py/id": 10}, "sons": [{"py/id": 20}, {"py/id": 19}], "text": "是他"}, {"py/id": 14}], "text": "是他不是她"}, "norm": "为什么", "prev": {"py/id": 1}, "sons": [], "text": "为什么"}, {"py/id": 11}], "text": "为什么是他不是她"}, {"py/id": 7}], "text": "为什么是他不是她？"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["为什么是他不是她?", "是"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}"""
    # Sentence = "为啥是他，而不是她？"
    # nodelist_str = """{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 10, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 105, 22]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "是", "ID": 15, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "为什么是他", "features": {"py/set": [2304, 2432, 1162, 2444, 272, 2331, 548, 549, 2340, 293, 294, 1064, 430, 175, 2105, 1986, 453, 1607, 1366, 2279, 105, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 4, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "", "atom": "，", "features": {"py/set": [192, 2432, 1, 39, 38, 22, 1162, 542]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "是", "ID": 16, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "", "atom": "而不是她", "features": {"py/set": [2304, 2432, 1162, 2444, 1550, 272, 2331, 547, 2340, 293, 294, 1064, 430, 175, 2105, 1986, 453, 1607, 1366, 2279, 250, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 9, "StartOffset": 10, "TempPointer": "", "UpperRelationship": "", "atom": "？", "features": {"py/set": [192, 193, 1, 102, 103, 1162, 22, 23, 542]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 11, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [192, 2432, 103, 23, 102, 22]}, "next": null, "norm": "", "prev": {"py/id": 5}, "sons": [], "text": ""}, "norm": "?", "prev": {"py/id": 4}, "sons": [], "text": "？"}, "norm": "而不是她", "prev": {"py/id": 3}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 5, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "Z", "atom": "而", "features": {"py/set": [2432, 1, 2310, 1607, 71, 1162, 12, 22, 542, 293, 297, 107, 430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "是", "ID": 14, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "H", "atom": "不是她", "features": {"py/set": [2304, 2432, 1162, 2444, 1550, 272, 273, 2331, 546, 2340, 293, 294, 430, 2105, 1986, 453, 1607, 1366, 90, 2279, 250, 1023]}, "next": null, "norm": "不是她", "prev": {"py/id": 10}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "是", "ID": 12, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "H", "atom": "不是", "features": {"py/set": [2304, 2432, 1986, 453, 1607, 1162, 2444, 1550, 272, 1366, 90, 2331, 2105, 545, 2340, 293, 294, 2279, 2347, 430, 2291, 249, 250, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "", "ID": 8, "StartOffset": 9, "TempPointer": "", "UpperRelationship": "O", "atom": "她", "features": {"py/set": [2432, 1, 1732, 2310, 1607, 1162, 144, 145, 18, 1052, 157, 542, 1697, 164, 293, 294, 295, 1704, 107, 1582, 1519, 176, 430, 1528, 380]}, "next": null, "norm": "她", "prev": {"py/id": 13}, "sons": [], "text": "她"}, "norm": "不是", "prev": {"py/id": 10}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 6, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "R", "atom": "不", "features": {"py/set": [2432, 1, 194, 198, 1607, 200, 1162, 12, 13, 527, 542, 293, 107, 430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "", "ID": 7, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "H", "atom": "是", "features": {"py/set": [2304, 2432, 1, 2310, 1162, 1550, 2331, 542, 293, 430, 2105, 453, 1607, 1098, 203, 1877, 1366, 90, 2279, 236, 1023]}, "next": null, "norm": "是", "prev": {"py/id": 17}, "sons": [], "text": "是"}, "norm": "不", "prev": {"py/id": 10}, "sons": [], "text": "不"}, {"py/id": 18}], "text": "不是"}, {"py/id": 14}], "text": "不是她"}, "norm": "而", "prev": {"py/id": 3}, "sons": [], "text": "而"}, {"py/id": 11}], "text": "而不是她"}, "norm": ",", "prev": {"py/id": 2}, "sons": [], "text": "，"}, "norm": "为什么是他", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "R", "atom": "为什么", "features": {"py/set": [193, 546, 1, 194, 198, 1607, 200, 2409, 1162, 105, 107, 12, 430, 175, 13, 1785, 2393, 1979, 220, 2398]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "是", "ID": 13, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是他", "features": {"py/set": [2304, 2432, 1986, 453, 1607, 1162, 2444, 272, 273, 1877, 1366, 90, 2331, 545, 2340, 293, 294, 2279, 430, 2105, 1023]}, "next": null, "norm": "是他", "prev": {"py/id": 24}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 2, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是", "features": {"py/set": [2304, 2432, 1, 1986, 453, 2310, 1607, 1098, 1162, 272, 1366, 90, 2331, 542, 2340, 293, 2279, 2347, 236, 430, 2291, 2105, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 3, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "O", "atom": "他", "features": {"py/set": [2432, 1, 1732, 2310, 1607, 1162, 144, 145, 18, 157, 542, 1697, 164, 293, 294, 295, 1704, 107, 1582, 1519, 176, 430, 1528, 380]}, "next": null, "norm": "他", "prev": {"py/id": 27}, "sons": [], "text": "他"}, "norm": "是", "prev": {"py/id": 24}, "sons": [], "text": "是"}, {"py/id": 28}], "text": "是他"}, "norm": "为什么", "prev": {"py/id": 1}, "sons": [], "text": "为什么"}, {"py/id": 25}], "text": "为什么是他"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}, "3": {"py/id": 4}, "4": {"py/id": 5}, "5": {"py/id": 6}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["为什么是他", "是"]}, {"py/tuple": [",", ""]}, {"py/tuple": ["而不是她", "是"]}, {"py/tuple": ["?", ""]}, {"py/tuple": ["", ""]}], "size": 6, "tail": {"py/id": 6}}"""
    #Sentence = "为什么是他不是她"
    #nodelist_str="""{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 7, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 105, 22]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "是", "ID": 13, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "为什么是他不是她", "features": {"py/set": [2304, 2432, 1986, 453, 1607, 1162, 2444, 272, 1366, 23, 2331, 548, 2340, 550, 293, 552, 294, 554, 555, 2279, 105, 430, 103, 250, 1064, 175, 2105, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 8, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [192, 2432, 103, 23, 102, 22]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "为什么是他不是她", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "R", "atom": "为什么", "features": {"py/set": [193, 546, 1, 194, 198, 1607, 200, 2409, 1162, 105, 107, 12, 430, 175, 13, 1785, 2393, 1979, 220, 2398]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "是", "ID": 12, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是他不是她", "features": {"py/set": [2304, 2432, 1162, 2444, 272, 273, 23, 2331, 548, 549, 2340, 293, 294, 430, 2105, 1986, 453, 1607, 203, 1877, 1366, 90, 2279, 103, 1023]}, "next": null, "norm": "是他不是她", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "是", "ID": 11, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是他", "features": {"py/set": [2304, 2432, 1986, 453, 1607, 1162, 2444, 272, 273, 1366, 90, 2331, 545, 2340, 293, 294, 2279, 2347, 430, 2291, 2105, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "是", "ID": 10, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "CN", "atom": "不是她", "features": {"py/set": [2304, 2432, 2435, 1162, 2444, 1550, 272, 273, 23, 2331, 546, 2340, 293, 294, 40, 2347, 430, 2105, 1986, 453, 1607, 1366, 2279, 103, 2291, 250, 1023]}, "next": null, "norm": "不是她", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "是", "ID": 9, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "H", "atom": "不是", "features": {"py/set": [2304, 545, 2432, 293, 453, 1607, 2279, 249, 1162, 294, 90, 2444, 1550, 430, 1366, 2105, 250, 2331, 1023]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 6, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "CN", "atom": "她", "features": {"py/set": [2432, 1, 2435, 2310, 1162, 144, 145, 23, 1052, 542, 1697, 293, 294, 295, 1704, 40, 1582, 430, 176, 1732, 1607, 103, 1519, 1528, 380]}, "next": null, "norm": "她", "prev": {"py/id": 12}, "sons": [], "text": "她"}, "norm": "不是", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 3, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "O", "atom": "他", "features": {"py/set": [2432, 1, 1732, 2310, 1607, 1162, 144, 145, 18, 157, 542, 1697, 164, 293, 294, 295, 1704, 107, 1582, 1519, 176, 430, 1528, 380]}, "next": null, "norm": "他", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 2, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "是", "features": {"py/set": [2304, 2432, 1, 453, 2310, 1607, 293, 2279, 1098, 1162, 236, 430, 1366, 2105, 90, 2331, 542, 1023]}, "next": {"py/id": 15}, "norm": "是", "prev": {"py/id": 6}, "sons": [], "text": "是"}, "sons": [], "text": "他"}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 4, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "R", "atom": "不", "features": {"py/set": [2432, 1, 194, 198, 1607, 200, 1162, 12, 13, 527, 542, 293, 107, 430]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 5, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "是", "features": {"py/set": [2304, 2432, 1, 2310, 1162, 1550, 2331, 542, 293, 430, 2105, 453, 1607, 1098, 203, 1877, 1366, 90, 2279, 236, 1023]}, "next": null, "norm": "是", "prev": {"py/id": 20}, "sons": [], "text": "是"}, "norm": "不", "prev": {"py/id": 15}, "sons": [], "text": "不"}, {"py/id": 21}], "text": "不是"}, {"py/id": 13}], "text": "不是她"}, "norm": "是他", "prev": {"py/id": 6}, "sons": [{"py/id": 16}, {"py/id": 15}], "text": "是他"}, {"py/id": 10}], "text": "是他不是她"}, "norm": "为什么", "prev": {"py/id": 1}, "sons": [], "text": "为什么"}, {"py/id": 7}], "text": "为什么是他不是她"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["为什么是他不是她", "是"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}"""
    #Sentence = "被他巧妙躲了过去"
    ###nodelist_str="""{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 7, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 22, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "被", "features": {"py/set": [2193, 162, 386, 1523, 498, 1, 104, 2314, 1099]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "巧妙", "ID": 11, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "", "atom": "他巧妙躲了过去", "features": {"py/set": [260, 261, 1732, 7, 264, 265, 9, 1099, 1734, 204, 1872, 1681, 533, 23, 1566, 1569, 227, 37, 102, 171, 1901, 880, 1586, 381, 437, 1718, 504, 1081, 506, 508, 509, 1599]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 8, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [23, 101, 22, 102, 185, 2314]}, "next": null, "norm": "", "prev": {"py/id": 3}, "sons": [], "text": ""}, "norm": "他巧妙躲了过去", "prev": {"py/id": 2}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "巧妙", "ID": 10, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "他巧妙", "features": {"py/set": [260, 261, 7, 264, 265, 9, 1681, 533, 1566, 1569, 37, 171, 1586, 437, 1718, 1081, 1599, 1732, 1734, 1099, 204, 1872, 89, 227, 1901, 880, 502, 381]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "躲", "ID": 9, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "NX", "atom": "躲了过去", "features": {"py/set": [225, 930, 1121, 260, 2214, 102, 234, 1099, 2187, 235, 236, 2162, 242, 23, 148, 1846, 503]}, "next": null, "norm": "躲了过去", "prev": {"py/id": 7}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 4, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "躲", "features": {"py/set": [1, 260, 1095, 1099, 2187, 89, 225, 930, 1121, 2214, 234, 235, 236, 2162, 498, 1846, 1593]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 5, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "X", "atom": "了", "features": {"py/set": [1, 386, 259, 226, 258, 2314, 2187, 1099, 106, 2193, 498, 1523, 22, 222]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 6, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "B", "atom": "过去", "features": {"py/set": [1, 386, 259, 2314, 2187, 1099, 2193, 21, 23, 280, 1500, 1438, 31, 1440, 1505, 226, 102, 106, 2092, 1901, 302, 2098, 1523, 501, 191]}, "next": null, "norm": "过去", "prev": {"py/id": 11}, "sons": [], "text": "过去"}, "norm": "了", "prev": {"py/id": 10}, "sons": [], "text": "了"}, "norm": "躲", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 3, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "H", "atom": "巧妙", "features": {"py/set": [1, 1732, 5, 1734, 7, 264, 265, 8, 1099, 260, 261, 9, 204, 1872, 1681, 533, 89, 1566, 1569, 227, 171, 1901, 880, 1586, 180, 437, 1718, 501, 1081, 381, 1599]}, "next": null, "norm": "巧妙", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 2, "Head0Text": "", "ID": 2, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "S", "atom": "他", "features": {"py/set": [129, 1601, 386, 260, 261, 259, 1, 199, 2314, 1099, 143, 144, 2193, 18, 340, 213, 1499, 1629, 1438, 1447, 106, 172, 498, 1523, 1594]}, "next": {"py/id": 15}, "norm": "他", "prev": {"py/id": 2}, "sons": [], "text": "他"}, "sons": [], "text": "巧妙"}, "sons": [], "text": "躲"}, {"py/id": 11}, {"py/id": 12}], "text": "躲了过去"}, "norm": "他巧妙", "prev": {"py/id": 2}, "sons": [{"py/id": 16}, {"py/id": 15}], "text": "他巧妙"}, {"py/id": 8}], "text": "他巧妙躲了过去"}, "norm": "被", "prev": {"py/id": 1}, "sons": [], "text": "被"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}, "3": {"py/id": 4}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["被", ""]}, {"py/tuple": ["他巧妙躲了过去", "巧妙"]}, {"py/tuple": ["", ""]}], "size": 4, "tail": {"py/id": 4}}"""
    #Sentence = "广州革命政府领导国民革命军进行了北伐战争"
    # nodelist_str = """{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 13, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 105, 22]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "同", "ID": 21, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "味道不同", "features": {"py/set": [1536, 1161, 9, 2443, 1549, 2446, 1784, 22, 546, 293, 294, 37, 298, 429, 175, 1606, 464, 105, 237, 2415, 376, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "个", "ID": 16, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "", "atom": "这个", "features": {"py/set": [544, 292, 293, 1542, 1606, 840, 1161, 2309, 1581, 1518, 429, 689, 53, 54, 1527, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 6, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "", "atom": "更好", "features": {"py/set": [544, 1, 1666, 1858, 5, 1798, 2438, 297, 298, 1161, 1836, 237, 1492, 2005, 1402, 1822]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "开盖", "ID": 22, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "", "atom": "%20讲真开盖", "features": {"py/set": [1161, 2443, 212, 1623, 23, 2330, 547, 2339, 549, 293, 551, 552, 2278, 2345, 103, 37, 294, 175, 1976, 249, 2303]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "", "ID": 14, "StartOffset": 15, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [192, 103, 23, 102, 22, 2431]}, "next": null, "norm": "", "prev": {"py/id": 5}, "sons": [], "text": ""}, "norm": "%20讲真开盖", "prev": {"py/id": 4}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "20", "ID": 19, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "S", "atom": "%20", "features": {"py/set": [160, 1, 34, 161, 107, 207, 850, 18, 1527, 221]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "开盖", "ID": 20, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "H", "atom": "讲真开盖", "features": {"py/set": [546, 2339, 293, 1623, 2278, 103, 1161, 2345, 2443, 90, 186, 175, 272, 212, 23, 1976, 249, 2330, 2303]}, "next": null, "norm": "讲真开盖", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "", "ID": 18, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "R", "atom": "讲真", "features": {"py/set": [544, 1, 194, 198, 200, 1161, 107, 12, 13, 1978, 1628]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "", "ID": 17, "StartOffset": 13, "TempPointer": "", "UpperRelationship": "H", "atom": "开盖", "features": {"py/set": [1, 1161, 2443, 203, 272, 1876, 23, 1623, 2330, 90, 544, 2339, 293, 2278, 103, 2345, 2346, 235, 2290, 2303]}, "next": null, "norm": "开盖", "prev": {"py/id": 12}, "sons": [], "text": "开盖"}, "norm": "讲真", "prev": {"py/id": 9}, "sons": [], "text": "讲真"}, {"py/id": 13}], "text": "讲真开盖"}, "norm": "%20", "prev": {"py/id": 4}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "", "ID": 7, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "", "atom": "%", "features": {"py/set": [1713, 292, 213, 1]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 8, "StartOffset": 9, "TempPointer": "", "UpperRelationship": "H", "atom": "20", "features": {"py/set": [1, 34, 850, 790, 1527, 90]}, "next": null, "norm": "20", "prev": {"py/id": 17}, "sons": [], "text": "20"}, "norm": "%", "prev": {"py/id": 4}, "sons": [], "text": "%"}, {"py/id": 18}], "text": "%20"}, {"py/id": 10}], "text": "%20讲真开盖"}, "norm": "更好", "prev": {"py/id": 3}, "sons": [], "text": "更好"}, "norm": "这个", "prev": {"py/id": 2}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 4, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "M", "atom": "这", "features": {"py/set": [1, 292, 2438, 840, 1097, 1161, 107, 12, 1581, 176, 144, 116, 1527, 1241, 60, 541, 126, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 5, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "H", "atom": "个", "features": {"py/set": [128, 513, 1, 292, 2309, 1542, 1606, 1161, 1581, 1518, 429, 689, 1527, 90, 541, 2431]}, "next": null, "norm": "个", "prev": {"py/id": 23}, "sons": [], "text": "个"}, "norm": "这", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "同", "ID": 15, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "H", "atom": "不同", "features": {"py/set": [1536, 1606, 8, 1161, 9, 1549, 2446, 464, 1784, 22, 90, 544, 293, 294, 298, 429, 237, 2415, 175, 376, 2431]}, "next": null, "norm": "不同", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 2, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "S", "atom": "味道", "features": {"py/set": [128, 1, 1542, 1161, 207, 144, 145, 18, 221, 544, 293, 294, 297, 105, 427, 107, 1581, 1518, 1527, 314, 2173]}, "next": {"py/id": 26}, "norm": "味道", "prev": {"py/id": 1}, "sons": [], "text": "味道"}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 2, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "r", "atom": "不", "features": {"py/set": [1, 198, 1606, 200, 1161, 13, 526, 1873, 541, 292, 107, 429, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 3, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "同", "features": {"py/set": [1536, 1, 5, 1606, 1161, 298, 429, 2446, 559, 464, 237, 1549, 2415, 22, 376, 90, 541, 2431]}, "next": null, "norm": "同", "prev": {"py/id": 30}, "sons": [], "text": "同"}, "norm": "不", "prev": {"py/id": 27}, "sons": [], "text": "不"}, {"py/id": 31}], "text": "不同"}, "sons": [], "text": "这"}, {"py/id": 24}], "text": "这个"}, "norm": "味道不同", "prev": {"py/id": 1}, "sons": [{"py/id": 27}, {"py/id": 26}], "text": "味道不同"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}, "3": {"py/id": 4}, "4": {"py/id": 5}, "5": {"py/id": 6}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["味道不同", "同"]}, {"py/tuple": ["这个", "个"]}, {"py/tuple": ["更好", ""]}, {"py/tuple": ["%20讲真开盖", "开盖"]}, {"py/tuple": ["", ""]}], "size": 6, "tail": {"py/id": 6}}"""
    # Sentence = "我买了红色的香奈儿眉笔"
    #nodelist_str="""{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 20, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [104, 22, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 26, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "我买了红色de香奈儿眉笔", "features": {"py/set": [512, 2051, 260, 261, 2187, 23, 287, 1059, 37, 2214, 2223, 2237, 1599, 2240, 1603, 1608, 1099, 204, 1614, 1872, 594, 1881, 2270, 102, 104, 234, 236, 494, 241, 626, 2162, 504, 506, 508, 510]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 21, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [514, 23, 101, 22, 102, 185, 2314]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "我买了红色的香奈儿眉笔", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 13, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "S", "atom": "我", "features": {"py/set": [129, 1601, 1539, 260, 261, 386, 259, 1, 199, 2314, 1099, 143, 144, 2193, 18, 340, 213, 1499, 1629, 1438, 1447, 104, 106, 172, 498, 1523, 1594]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 25, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "买了红色de香奈儿眉笔", "features": {"py/set": [512, 2051, 260, 2187, 23, 287, 1059, 2214, 2223, 2237, 1599, 2240, 1603, 1608, 1099, 204, 1614, 1872, 594, 1881, 89, 2270, 102, 234, 236, 494, 241, 626, 2162, 242, 504, 506, 508, 510]}, "next": null, "norm": "买了红色的香奈儿眉笔", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "买", "ID": 23, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "买了", "features": {"py/set": [2051, 260, 2187, 287, 1059, 2214, 2223, 2230, 2237, 1599, 2240, 1603, 1608, 1099, 1614, 594, 89, 1881, 2270, 234, 235, 236, 494, 241, 626, 2162, 501, 2174]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "眉笔", "ID": 24, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "O", "atom": "红色de香奈儿眉笔", "features": {"py/set": [129, 260, 261, 1099, 1164, 524, 588, 143, 144, 18, 23, 153, 1499, 1629, 1438, 160, 1958, 1447, 1702, 102, 106, 369, 1462, 504, 505, 506, 508, 2111, 510, 511]}, "next": null, "norm": "红色的香奈儿眉笔", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 16, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "M", "atom": "红色", "features": {"py/set": [129, 1, 1412, 390, 264, 1099, 12, 1487, 661, 1754, 1499, 1438, 1312, 1447, 106, 1324, 115, 501, 1462, 1718, 125, 127]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 6, "Head0Text": "", "ID": 17, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "X", "atom": "de", "features": {"py/set": [1, 258, 386, 259, 2314, 1099, 2193, 1510, 106, 498, 1523]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "眉笔", "ID": 22, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "H", "atom": "香奈儿眉笔", "features": {"py/set": [129, 260, 135, 1099, 1164, 524, 588, 23, 89, 1499, 1629, 1438, 1958, 1447, 1702, 102, 369, 1462, 504, 505, 2111]}, "next": null, "norm": "香奈儿眉笔", "prev": {"py/id": 13}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 9, "Head0Text": "", "ID": 18, "StartOffset": 6, "TempPointer": "", "UpperRelationship": "M", "atom": "香奈儿", "features": {"py/set": [1088, 129, 1601, 1, 1447, 1543, 138, 1099, 1515, 106, 12, 1521, 115, 125, 662, 502, 472, 1499, 1629, 127]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 19, "StartOffset": 9, "TempPointer": "", "UpperRelationship": "H", "atom": "眉笔", "features": {"py/set": [129, 1, 1164, 524, 23, 1438, 1958, 1447, 1702, 1324, 1462, 2111, 1099, 588, 89, 1499, 1629, 102, 369, 501, 118, 127]}, "next": null, "norm": "眉笔", "prev": {"py/id": 16}, "sons": [], "text": "眉笔"}, "norm": "香奈儿", "prev": {"py/id": 13}, "sons": [], "text": "香奈儿"}, {"py/id": 17}], "text": "香奈儿眉笔"}, "norm": "的", "prev": {"py/id": 12}, "sons": [], "text": "的"}, "norm": "红色", "prev": {"py/id": 9}, "sons": [], "text": "红色"}, {"py/id": 13}, {"py/id": 14}], "text": "红色的香奈儿眉笔"}, "norm": "买了", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 2, "Head0Text": "", "ID": 14, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "H", "atom": "买", "features": {"py/set": [2240, 1, 2051, 1603, 1608, 2187, 1099, 1614, 594, 89, 2270, 287, 225, 1059, 2214, 234, 494, 626, 2162, 498, 2237, 1599]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 15, "StartOffset": 2, "TempPointer": "", "UpperRelationship": "X", "atom": "了", "features": {"py/set": [1, 386, 259, 226, 258, 2314, 2187, 1099, 106, 2193, 498, 1523, 22, 222]}, "next": null, "norm": "了", "prev": {"py/id": 23}, "sons": [], "text": "了"}, "norm": "买", "prev": {"py/id": 6}, "sons": [], "text": "买"}, {"py/id": 24}], "text": "买了"}, {"py/id": 10}], "text": "买了红色的香奈儿眉笔"}, "norm": "我", "prev": {"py/id": 1}, "sons": [], "text": "我"}, {"py/id": 7}], "text": "我买了红色的香奈儿眉笔"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["我买了红色的香奈儿眉笔", "买"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}"""

    Sentence = "钱桂春、孙桂林、郭进等同学"
    nodelist_str="""{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 13, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [21, 102, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "同学", "ID": 22, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "钱桂春、孙桂林、郭进等同学", "features": {"py/set": [1160, 1164, 1804, 143, 144, 1174, 1175, 1176, 22, 544, 546, 290, 548, 1189, 550, 291, 552, 1708, 1592, 1209, 1600, 72, 1615, 101, 1382, 103, 1769, 1774, 1778, 1655, 377]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "", "ID": 14, "StartOffset": 13, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [100, 21, 101, 22, 2504, 191]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "钱桂春、孙桂林、郭进等同学", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "郭进", "ID": 21, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "equivM", "atom": "钱桂春、孙桂林、郭进", "features": {"py/set": [130, 135, 1160, 138, 11, 1804, 1171, 1174, 544, 546, 290, 548, 1189, 550, 552, 559, 1592, 1600, 2507, 978, 979, 103, 1769, 106, 1776, 115, 1655, 377, 125]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 11, "StartOffset": 10, "TempPointer": "", "UpperRelationship": "X", "atom": "等", "features": {"py/set": [288, 289, 1, 69, 2375, 2504, 233, 426, 1160, 2380, 2381, 2350, 106, 1680, 21, 2358, 538]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "", "ID": 12, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "H", "atom": "同学", "features": {"py/set": [1600, 1, 101, 1382, 72, 1769, 1160, 1804, 1708, 1774, 1615, 1778, 22, 1655, 1592, 377, 88, 541, 127]}, "next": null, "norm": "同学", "prev": {"py/id": 7}, "sons": [], "text": "同学"}, "norm": "等", "prev": {"py/id": 6}, "sons": [], "text": "等"}, "norm": "钱桂春、孙桂林、郭进", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "孙桂林", "ID": 20, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "CN", "atom": "钱桂春、孙桂林", "features": {"py/set": [1600, 130, 131, 135, 1160, 1609, 138, 1804, 1174, 1494, 1246, 544, 546, 1570, 548, 549, 1189, 290, 1446, 1449, 1769, 683, 684, 103, 39, 559, 1776, 1775, 1655, 1592, 377]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 8, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "X", "atom": "、", "features": {"py/set": [288, 1, 58, 38, 2504, 1160, 106, 21, 538, 191]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "", "ID": 15, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "H", "atom": "郭进", "features": {"py/set": [1600, 1, 130, 290, 1160, 1769, 138, 1804, 559, 1776, 1655, 1592, 377, 88, 541, 127]}, "next": null, "norm": "郭进", "prev": {"py/id": 13}, "sons": [], "text": "郭进"}, "norm": "、", "prev": {"py/id": 12}, "sons": [], "text": "、"}, "norm": "钱桂春、孙桂林", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "桂春", "ID": 18, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "钱桂春", "features": {"py/set": [1, 130, 131, 1160, 138, 1804, 1174, 1050, 542, 290, 559, 1592, 1600, 1609, 1246, 103, 1769, 1775, 1776, 1655, 377]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 4, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "X", "atom": "、", "features": {"py/set": [288, 1, 58, 38, 2504, 1160, 106, 21, 538, 191]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "桂林", "ID": 19, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "孙桂林", "features": {"py/set": [1600, 1, 130, 131, 1160, 1609, 138, 1804, 1174, 1494, 88, 542, 1246, 1570, 290, 1446, 1449, 1769, 683, 684, 559, 1776, 1775, 1655, 1592, 377]}, "next": null, "norm": "孙桂林", "prev": {"py/id": 19}, "sons": [], "text": "孙桂林"}, "norm": "、", "prev": {"py/id": 18}, "sons": [], "text": "、"}, "norm": "钱桂春", "prev": {"py/id": 1}, "sons": [], "text": "钱桂春"}, {"py/id": 19}, {"py/id": 20}], "text": "钱桂春、孙桂林"}, {"py/id": 13}, {"py/id": 14}], "text": "钱桂春、孙桂林、郭进"}, {"py/id": 7}, {"py/id": 8}], "text": "钱桂春、孙桂林、郭进等同学"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["钱桂春、孙桂林、郭进等同学", "同学"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}"""

    Sentence = "花多少钱这药方咱也得买下来"
    nodelist_str = """{"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 31, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [21, 102, 103]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "买", "ID": 41, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "花多少钱这药方咱得买下来", "features": {"py/set": [1160, 2061, 1166, 534, 22, 1176, 667, 1181, 2461, 544, 1184, 546, 1186, 548, 1187, 550, 1191, 552, 290, 1574, 1062, 1192, 36, 174, 2353, 291, 2240, 320, 2378, 2519, 1120, 2405, 101, 103, 2414, 1777, 1781, 246, 1786, 635, 2428, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "", "ID": 32, "StartOffset": 13, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [100, 21, 101, 22, 2507, 191]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": ""}, "norm": "花多少钱这药方我也得买下来", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 40, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "H", "atom": "花多少钱这药方咱得买", "features": {"py/set": [1160, 2061, 1166, 534, 1176, 667, 1181, 2461, 544, 1184, 546, 1186, 548, 1187, 550, 290, 552, 1574, 1062, 1192, 36, 174, 2353, 291, 2240, 320, 2378, 2519, 88, 1120, 2405, 103, 2414, 1777, 1781, 246, 1786, 635, 2428, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 13, "Head0Text": "", "ID": 30, "StartOffset": 11, "TempPointer": "", "UpperRelationship": "X", "atom": "下来", "features": {"py/set": [288, 289, 1, 2405, 101, 232, 1129, 2378, 2507, 426, 1133, 1160, 106, 2353, 1683, 22, 536, 541]}, "next": null, "norm": "下来", "prev": {"py/id": 6}, "sons": [], "text": "下来"}, "norm": "花多少钱这药方我也得买", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "花", "ID": 38, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "S", "atom": "花多少钱", "features": {"py/set": [128, 261, 1160, 2061, 1166, 1807, 143, 17, 144, 1176, 1817, 1050, 1181, 799, 1184, 2081, 543, 290, 36, 291, 1062, 2472, 174, 1076, 1595, 1597, 192, 1603, 2378, 1612, 206, 2519, 88, 219, 1757, 103, 106, 2414, 2421, 1658, 1659, 1662]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 39, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "这药方咱得买", "features": {"py/set": [1160, 2061, 1166, 534, 1176, 667, 1181, 2461, 544, 1184, 546, 1186, 548, 549, 1187, 290, 1574, 1062, 1192, 36, 291, 174, 2353, 2240, 320, 2378, 2519, 88, 1120, 2405, 2414, 1777, 2421, 1781, 246, 1786, 635, 2428, 2431]}, "next": null, "norm": "这药方我也得买", "prev": {"py/id": 10}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "药方", "ID": 36, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "O", "atom": "这药方", "features": {"py/set": [1603, 839, 1160, 1164, 1807, 143, 144, 1618, 17, 1658, 407, 1176, 1177, 1178, 2139, 156, 542, 1310, 290, 291, 163, 122, 106, 1332, 629, 887, 1530, 1595]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 37, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "H", "atom": "咱得买", "features": {"py/set": [2240, 320, 1160, 2378, 269, 1166, 534, 2519, 1176, 88, 667, 2461, 543, 1120, 1186, 1187, 290, 2405, 1574, 1062, 1192, 36, 291, 174, 2353, 1777, 1781, 246, 1786, 635, 2428, 2431]}, "next": null, "norm": "我也得买", "prev": {"py/id": 13}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 26, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "S", "atom": "咱", "features": {"py/set": [1, 1603, 1160, 2507, 206, 143, 1807, 2384, 17, 1683, 538, 219, 289, 1705, 426, 106, 1772, 175, 1779, 377, 1658, 1595]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "买", "ID": 35, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "H", "atom": "得买", "features": {"py/set": [1160, 534, 1176, 667, 2461, 542, 290, 1574, 1062, 1192, 174, 2353, 2240, 320, 2378, 2519, 88, 1120, 2405, 1777, 1781, 245, 246, 1786, 635, 2428, 2431]}, "next": null, "norm": "也得买", "prev": {"py/id": 16}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "", "ID": 34, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "Z", "atom": "得", "features": {"py/set": [1, 69, 1160, 2378, 2507, 11, 1743, 2384, 81, 1683, 21, 541, 289, 2081, 293, 426, 106, 117, 1912, 1914]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 11, "Head0Text": "", "ID": 29, "StartOffset": 10, "TempPointer": "", "UpperRelationship": "H", "atom": "买", "features": {"py/set": [2240, 320, 1, 1160, 2378, 534, 88, 538, 667, 2461, 1120, 2405, 1574, 1062, 232, 174, 2353, 1777, 1781, 1786, 635, 2428, 2431]}, "next": null, "norm": "买", "prev": {"py/id": 19}, "sons": [], "text": "买"}, "norm": "也得", "prev": {"py/id": 16}, "sons": [], "text": "也得"}, {"py/id": 20}], "text": "也得买"}, "norm": "我", "prev": {"py/id": 13}, "sons": [], "text": "咱"}, {"py/id": 17}], "text": "咱也得买"}, "norm": "这药方", "prev": {"py/id": 10}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 5, "Head0Text": "", "ID": 24, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "M", "atom": "这", "features": {"py/set": [289, 1, 1603, 839, 1096, 1319, 1160, 2507, 106, 11, 175, 143, 2514, 538, 115, 1658, 59, 125]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 25, "StartOffset": 5, "TempPointer": "", "UpperRelationship": "H", "atom": "药方", "features": {"py/set": [1, 1603, 839, 1160, 2139, 1807, 887, 1530, 1618, 1332, 629, 1658, 407, 88, 122, 1595, 541, 1310, 127]}, "next": null, "norm": "药方", "prev": {"py/id": 25}, "sons": [], "text": "药方"}, "norm": "这", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "钱", "ID": 33, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "O", "atom": "多少钱", "features": {"py/set": [1160, 137, 1807, 1935, 143, 144, 2451, 17, 1658, 407, 1176, 156, 542, 1310, 2081, 290, 291, 163, 421, 1192, 2472, 1578, 174, 312, 1595, 192, 65, 66, 1603, 1860, 1612, 1614, 1871, 481, 106, 1521, 1270, 1272, 1274]}, "next": null, "norm": "多少钱", "prev": {"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 21, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "H", "atom": "花", "features": {"py/set": [128, 1, 1603, 261, 1096, 1160, 2378, 1612, 2061, 1166, 1807, 1431, 88, 1817, 1050, 1659, 538, 1757, 1181, 799, 1184, 2081, 1176, 2211, 103, 232, 556, 2414, 560, 1076, 2421, 1658, 1595, 1597, 1662]}, "next": {"py/id": 28}, "norm": "花", "prev": {"py/id": 1}, "sons": [], "text": "花"}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 3, "Head0Text": "", "ID": 22, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "Z", "atom": "多少", "features": {"py/set": [33, 289, 1603, 2467, 1, 293, 2472, 1160, 426, 2507, 106, 11, 1935, 1683, 1270, 1272, 541]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 23, "StartOffset": 3, "TempPointer": "", "UpperRelationship": "H", "atom": "钱", "features": {"py/set": [192, 65, 66, 1603, 1, 1272, 1860, 1160, 137, 1274, 1612, 1614, 1807, 1935, 1871, 2451, 407, 88, 538, 1310, 2081, 312, 481, 421, 2472, 1578, 174, 1521, 1270, 568, 1658, 1595, 127, 1023]}, "next": null, "norm": "钱", "prev": {"py/id": 32}, "sons": [], "text": "钱"}, "norm": "多少", "prev": {"py/id": 29}, "sons": [], "text": "多少"}, {"py/id": 33}], "text": "多少钱"}, "sons": [], "text": "这"}, {"py/id": 26}], "text": "这药方"}, {"py/id": 14}], "text": "这药方咱也得买"}, "norm": "花多少钱", "prev": {"py/id": 1}, "sons": [{"py/id": 29}, {"py/id": 28}], "text": "花多少钱"}, {"py/id": 11}], "text": "花多少钱这药方咱也得买"}, {"py/id": 7}], "text": "花多少钱这药方咱也得买下来"}, "norm": "", "prev": null, "sons": [], "text": ""}, "1": {"py/id": 2}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["花多少钱这药方我也得买下来", "买"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}
"""
    newnodelist = jsonpickle.loads(nodelist_str)
    print(newnodelist.root().CleanOutput().toJSON())

    x = DependencyTree()
    x.transform(newnodelist)
    print(x)
    print(x.digraph('graph'))
    print(x.digraph('simple'))
    print("^.O is: {}".format(x.FindPointerNode(x.root, "^.O")))