#Note: DAG is being used in this process, but actually the dependancytree is not pure DAG:
#    some of the graph can be cyclic.
# so it is required to have "root".

import jsonpickle, copy, logging, re
import operator
import utils    #for the Feature_...
#from utils import *
import Lexicon
import FeatureOntology
import LogicOperation

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
        temp_subgraphs = []
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
                temp_subgraphs.append(SubGraph(root))
                self._roots.append(root.ID)
            root = root.next

        #filling up the subgraphs.
        while temp_subgraphs:
            subgraph = temp_subgraphs.pop()
            node = subgraph.startnode

            if node.sons:
                subnode = node.sons[0]
                nodestack = set()
                while subnode:
                    if subnode.sons:
                        if utils.FeatureID_H not in subnode.features:
                            temp_subgraphs.append(SubGraph(subnode))    # non-leaf, non-H. it is a subgraph.
                            subgraph.leaves.append([subnode.ID, subnode.UpperRelationship])
                            subnode = subnode.next
                            if subnode == None and nodestack:
                                subnode = nodestack.pop()
                        else:
                            if subnode.next:
                                nodestack.add(subnode.next)
                            subnode = subnode.sons[0]
                    else:   # this is a leaf node.
                        #  use the copy in self.nodes to apply feature modification
                        if utils.FeatureID_H in subnode.features:
                            subgraph.headID = subnode.ID
                            self.nodes[subnode.ID].features.update(subgraph.startnode.features)
                            Lexicon.ApplyWordLengthFeature(self.nodes[subnode.ID])
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
        index = 0
        for node in sorted(self.nodes.values(), key=operator.attrgetter("StartOffset")):
            node.Index = index
            index +=  1

        self._MarkNext()
        self.root = self._roots[0]

        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("End of transform:\n {}".format(self))


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
            for edge in sorted(self.graph, key= operator.itemgetter(2, 0, 1)):
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
            for edge in sorted(self.graph, key= operator.itemgetter(2, 0, 1)):
                    output += "\t{}->{} [label=\"{}\"];\n".format(edge[2], edge[0], edge[1])

            output += "}"
        # if logging.root.isEnabledFor(logging.DEBUG):
        #     logging.debug("output = {}".format(output))
        return output


    def _AddEdge(self, node1id, relation, parentid):
        #find the write relation to add, if already have a child relation for the same nodes.
        self.graph.add((node1id, relation, parentid, FeatureOntology.GetFeatureID(relation)))
        # Use ontology to find the ancestors of the relation
        relationid = FeatureOntology.GetFeatureID(relation)
        if FeatureOntology.SearchFeatureOntology(relationid):
            for ancestor in FeatureOntology.SearchFeatureOntology(relationid).ancestors:
                ancestorname = FeatureOntology.GetFeatureName(ancestor)
                if (node1id, ancestorname, parentid,ancestor) in self.graph:
                    self.graph.remove((node1id, ancestorname, parentid,ancestor))

        #Set the parent to have the relation.
        hasFeatureID = FeatureOntology.GetFeatureID("has" + relation)
        if hasFeatureID >= 0:
            self.nodes[parentid].ApplyFeature(hasFeatureID)
        else:
            logging.error("There is no has{} feature in the feature.txt!".format(relation))


    def _RemoveEdge(self, node1id, relation, parentid):
        if relation[0] == "~":  #revert
            self._RemoveEdge(parentid, relation[1:], node1id)
            return

        relationid = FeatureOntology.GetFeatureID(relation)

        for edge in [ e for e in self.graph if e[0] == node1id and e[2] == parentid]:
            if relationid == edge[3] or relationid in FeatureOntology.SearchFeatureOntology(edge[3]).ancestors:
                self.graph.remove(edge)


    def _CheckEdge(self, node1id, relation, parentid):
        Reverse = False
        if relation[0] == "~":
            logging.debug("_CheckEdge: Reverse! {}".format(relation))
            Reverse = True
            relation = relation[1:]

        relationid = FeatureOntology.GetFeatureID(relation)
        if Reverse:
            edgecandidates = [e for e in self.graph if e[0] == parentid and e[2] == node1id]
        else:
            edgecandidates = [e for e in self.graph if e[0] == node1id and e[2] == parentid]

        for edge in sorted(edgecandidates, key = operator.itemgetter(2, 1, 0)):
            if relationid == edge[3]:
                return True
            else:
                edgerelationnode = FeatureOntology.SearchFeatureOntology(edge[3])
                if edgerelationnode and relationid in edgerelationnode.ancestors:
                    if logging.root.isEnabledFor(logging.DEBUG):
                        logging.debug("   Found ontology ancesstor relation!")
                    return True
        return False


    #because the "|" sign in SubtreePointer is expanded during compilation(_ExpandOrToken(OneList))
    #it is not longer process here.
    FindPointerNode_Cache = {}
    def FindPointerNode(self, openID, SubtreePointer, rule):
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Dag.FindPointerNode for {}".format(SubtreePointer))
        if (openID, SubtreePointer, rule.ID) in self.FindPointerNode_Cache:
            #logging.debug("FindPointerNode_Cache: hit!")
            return self.FindPointerNode_Cache[(openID, SubtreePointer, rule.ID)]

        if len(SubtreePointer) >= 1 and SubtreePointer[0] == '^':
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
                if pointer.isdigit():
                    pointer_num = int(pointer)
                    nodeID = rule.Tokens[pointer_num].MatchedNodeID
                else:
                    pointer = "^" + pointer
                    #logging.info("Finding pointer node {} from TempPointer".format(pointer))
                    for nodeid in sorted(self.nodes):
                        #logging.debug("DAG.FindPointerNode: evaluating temppointer {} in {} with pointer {}".format(self.nodes[nodeid].TempPointer, self.nodes[nodeid].text, pointer))
                        if self.nodes[nodeid].TempPointer == pointer:
                            #logging.debug("Matched nodeid {}".format(nodeid))
                            nodeID = nodeid
                            break
                #logging.warning("after looping over the nodes, nodeID={}".format(nodeID))
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
            self.FindPointerNode_Cache[(openID, SubtreePointer, rule.ID)] = nodeID
            return nodeID
        else:
            logging.warning("Can't find {} pointer in this rule{}".format(SubtreePointer, rule))
            return None


    def ClearVisited(self):
        for nodeid in self.nodes:
            self.nodes[nodeid].visited = False


    # Unification: <['^V-' ] [不] ^V[V|V0|v]> // Test: 学不学习； 侃不侃大山
    # In rule, start from RulePosition, seach for pointer:
    #   Start from left side, if not found, seach right side.
    # After that is found, use the offset to locate the token in StrTokens
    #  compare the pointertoken to the current token (both in StrTokens),
    #   return the compare result.
    # Update: ^N : 香味   0
    #           ^-N: PointerIsSuffix  味  1   ^N-: PointerIsPrefix  香     2
    #           -^-N: '-味'          臭味  3   ^N--:  '香-'          香气   4
    #           ^-N-: '味-'          味道  5   -^N-:  '-香'          夜来香  6

    def PointerMatch(self, openID, rule, nodeID, Pointer, matchtype='norm'):
        if re.match("-\^(.+)-", Pointer):
            P = "^" + Pointer[2:-1]
            PointerType = 6
        elif re.match("\^-(.+)-", Pointer):
            P = "^" + Pointer[2:-1]
            PointerType = 5
        elif re.match("\^(.+)--", Pointer):
            P = "^" + Pointer[1:-2]
            PointerType = 4
        elif re.match("-\^-(.+)", Pointer):
            P = "^" + Pointer[3:]
            PointerType = 3
        elif re.match("\^(.+)-", Pointer):
            P = "^" + Pointer[1:-1]
            PointerType = 2
        elif re.match("\^-(.+)", Pointer):
            P = "^" + Pointer[2:]
            PointerType = 1
        else:
            P = "^" + Pointer[1:]  # should be ^N
            PointerType = 0

        StrPointerToken = self.nodes[self.FindPointerNode(openID, P, rule)]
        strToken = self.nodes[nodeID]

        if matchtype == "text":
            return strToken.text and StrPointerToken.text \
                   and ((PointerType == 0 and StrPointerToken.text == strToken.text)
                        or (PointerType == 1 and StrPointerToken.text.endswith(strToken.text))
                        or (PointerType == 2 and StrPointerToken.text.startswith(strToken.text))
                        or (PointerType == 3 and StrPointerToken.text.endswith(strToken.text[-1]))
                        or (PointerType == 4 and StrPointerToken.text.startswith(strToken.text[0]))
                        or (PointerType == 5 and StrPointerToken.text.endswith(strToken.text[0]))
                        or (PointerType == 6 and StrPointerToken.text.startswith(strToken.text[-1]))
                        )
        elif matchtype == "norm":
            return strToken.norm and StrPointerToken.norm \
                   and ((PointerType == 0 and StrPointerToken.norm == strToken.norm)
                        or (PointerType == 1 and StrPointerToken.norm.endswith(strToken.norm))
                        or (PointerType == 2 and StrPointerToken.norm.startswith(strToken.norm))
                        or (PointerType == 3 and StrPointerToken.norm.endswith(strToken.norm[-1]))
                        or (PointerType == 4 and StrPointerToken.norm.startswith(strToken.norm[0]))
                        or (PointerType == 5 and StrPointerToken.norm.endswith(strToken.norm[0]))
                        or (PointerType == 6 and StrPointerToken.norm.startswith(strToken.norm[-1]))
                        )
        elif matchtype == "atom":
            return strToken.atom and StrPointerToken.atom \
                   and ((PointerType == 0 and StrPointerToken.atom == strToken.atom)
                        or (PointerType == 1 and StrPointerToken.atom.endswith(strToken.atom))
                        or (PointerType == 2 and StrPointerToken.atom.startswith(strToken.atom))
                        or (PointerType == 3 and StrPointerToken.atom.endswith(strToken.atom[-1]))
                        or (PointerType == 4 and StrPointerToken.atom.startswith(strToken.atom[0]))
                        or (PointerType == 5 and StrPointerToken.atom.endswith(strToken.atom[0]))
                        or (PointerType == 6 and StrPointerToken.atom.startswith(strToken.atom[-1]))
                        )
        else:
            raise RuntimeError("The matchtype should be text/norm/atom. Please check syntax!")


    def TokenMatch(self, nodeID, ruletoken, OpenNodeID, rule):
        if ruletoken.AndText and "^" in ruletoken.AndText:
            # This is a pointer! unification comparison.
            if not self.PointerMatch(OpenNodeID, rule, nodeID, Pointer=ruletoken.AndText,
                                matchtype=ruletoken.AndTextMatchtype):
                return False
        node = self.nodes[nodeID]

        logicmatch = LogicOperation.LogicMatch_notpointer(node, ruletoken)
        if not logicmatch:
            return False
        #might need open node for pointer
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("DAG.TokenMatch: comparing ruletoken {} with nodeid {}".format(ruletoken, node))
            logging.debug("Dag.TokenMatch for SubtreePointer {} in rule token {}".format(ruletoken.SubtreePointer, ruletoken))
        if not ruletoken.SubtreePointer:
            return True

        SubtreePointer = ruletoken.SubtreePointer
        if ">>" in SubtreePointer:
            SubtreePointer, ReferenceNodePointer = SubtreePointer.split(">>", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule)
            if node.Index != self.nodes[ReferenceNodeID].Index + 1 :
                return False
        elif "<<" in SubtreePointer:
            SubtreePointer, ReferenceNodePointer = SubtreePointer.split("<<", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule)
            if node.Index != self.nodes[ReferenceNodeID].Index - 1 :
                return False
        elif ">" in SubtreePointer:     #on the left side of the other pointer
            SubtreePointer, ReferenceNodePointer = SubtreePointer.split(">", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule)
            if node.Index < self.nodes[ReferenceNodeID].Index :
                return False
        elif "<" in SubtreePointer:
            SubtreePointer, ReferenceNodePointer = SubtreePointer.split("<", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule)
            if node.Index > self.nodes[ReferenceNodeID].Index :
                return False

        for AndCondition in SubtreePointer.split("+"):
            Negation = False

            #logging.warning("AndCondition:{}".format(AndCondition))
            if AndCondition[0] == "!":
                #logging.warning("FindPointerNode: Negation! {}".format(ruletoken.SubtreePointer))
                Negation = True
                AndCondition = AndCondition[1:]

            if "." in AndCondition:
                pointer, relations = AndCondition.split(".", 1)
            else:
                pointer, relations = [AndCondition, ""]
            start_nodeID = None
            if pointer == '':
                start_nodeID = OpenNodeID
            else:
                if pointer.isdigit():
                    pointer_num = int(pointer)
                    start_nodeID = rule.Tokens[pointer_num].MatchedNodeID
                else:
                    pointer = "^" + pointer
                    #logging.info("DAG.TokenMatch(): Looking for pointer node {} from TempPointer".format(pointer[0]))
                    for nodeid in sorted(self.nodes):
                        #logging.debug("DAG.TokenMatch: evaluating temppointer {} with pointer {}".format(node.TempPointer, pointer))
                        if self.nodes[nodeid].TempPointer == pointer:
                            start_nodeID = nodeid
                            break
            if not start_nodeID:
                Satisfied = False
            elif not relations:
                Satisfied = True

            elif start_nodeID and relations:

                relationlist = relations.split(".")
                if len(relationlist) == 1:
                    if relations in ("LINKNUM1", "LINKNUM2", "LINKNUM3"):
                        linkcount = len([e for e in self.graph if e[0] == nodeID and e[2] == start_nodeID])
                        logging.debug("\tLink count from parent {} to node {} is {}".format(self.nodes[start_nodeID], self.nodes[nodeID], linkcount))
                        if relations == "LINKNUM1":
                            Satisfied = linkcount == 1
                        elif relations == "LINKNUM2":
                            Satisfied = linkcount == 2
                        elif relations == "LINKNUM3":
                            Satisfied = linkcount == 3
                    else:
                        Satisfied = self._CheckEdge( nodeID, relationlist[0], start_nodeID)
                elif len(relationlist) == 2:
                    for second_nodeID in self.nodes:
                        Satisfied = self._CheckEdge( nodeID, relationlist[1], second_nodeID) and \
                                        self._CheckEdge(second_nodeID, relationlist[0], start_nodeID)
                        if Satisfied:
                            break
                elif len(relationlist) == 3:
                    for second_nodeID in self.nodes:
                        for third_nodeID in self.nodes:
                            Satisfied = self._CheckEdge(nodeID, relationlist[2], third_nodeID) and \
                                            self._CheckEdge(third_nodeID, relationlist[1], second_nodeID) and \
                                            self._CheckEdge(second_nodeID, relationlist[0], start_nodeID)
                            if Satisfied:
                                break
                        if Satisfied:
                            break
                else:
                    logging.error("DAG.TokenMatch(): Not yet implemented for multiple dots: {}".format(ruletoken.SubtreePointer))

            if ( Negation and Satisfied) or ( not Negation and not Satisfied) :
                if logging.root.isEnabledFor(logging.DEBUG):
                    logging.debug("Dag.TokenMatch(): False because Negation is {} and nodeID is {}".format(Negation, start_nodeID))
                return False
        return True


    def ApplyDagActions(self, OpenNode, node, actinstring, rule):
        Actions = actinstring.split()
        #logging.debug("Word:" + self.text)

        for Action in copy.copy(Actions):
            if "---" in Action:
                ParentPointer = Action[:Action.rfind('.')]  #find pointer up the the last dot "."
                parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer, rule)
                if "~---" in Action:
                    self.graph = set([edge for edge in self.graph if edge[0] != parentnodeid or edge[2] != node.ID])
                    logging.debug("Dag Action {}: Removed all edge from {} to {}".format(Action, parentnodeid, node.ID))
                else:
                    self.graph = set([edge for edge in self.graph if edge[0] != node.ID or edge[2] != parentnodeid])
                    logging.debug("Dag Action {}: Removed all edge from {} to {}".format(Action, parentnodeid, node.ID))
                Actions.pop(Actions.index(Action))

        for Action in sorted(Actions, key=lambda d:(d[-1])):
            if Action[0] == '^':
                ParentPointer = Action[:Action.rfind('.')]  #find pointer up the the last dot "."
                parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer, rule)
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


            if Action == "NEUTRAL":
                 FeatureOntology.ProcessSentimentTags(node.features)


if __name__ == "__main__":

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    # import ProcessSentence
    # ProcessSentence.LoadCommon()
    # #
    #
    # Sentence = "买了香奈儿眉笔"
    #
    # nodelist, _, _ = ProcessSentence.LexicalAnalyze(Sentence)
    #
    # nodelist_str = jsonpickle.dumps(nodelist)
    # print(nodelist_str)

    nodelist_str = """ {"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 10, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [108, 1433, 107, 28]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 22, "Head0Text": "会晤", "ID": 18, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "总统特朗普和朝鲜总统金正恩首次面对面会晤", "features": {"py/set": [2565, 2446, 405, 1429, 663, 1433, 1820, 29, 1824, 1188, 1572, 1192, 43, 1204, 180, 440, 571, 316, 701, 573, 575, 1088, 577, 1218, 579, 1214, 317, 1222, 2393, 346, 106, 108, 251, 2418, 1275, 1278]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 22, "Head0Text": "", "ID": 11, "StartOffset": 22, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [1429, 198, 2552, 105, 106, 28, 29]}, "next": null, "norm": "", "prev": {"py/id": 2}, "sons": [], "text": "", "visited": false}, "norm": "美国总统特朗普和朝鲜总统金正恩首次面对面会晤", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "金正恩", "ID": 16, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "synS", "atom": "总统特朗普和朝鲜总统金正恩", "features": {"py/set": [1537, 133, 135, 142, 147, 404, 148, 1815, 24, 1433, 2459, 1821, 1822, 1188, 1702, 1192, 2091, 1200, 1204, 1205, 1850, 571, 316, 573, 317, 575, 577, 579, 1239, 1240, 2273, 1636, 1644, 108, 110, 2555]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 22, "Head0Text": "会晤", "ID": 17, "StartOffset": 15, "TempPointer": "", "UpperRelationship": "H", "atom": "首次面对面会晤", "features": {"py/set": [576, 1088, 2565, 701, 2446, 405, 1429, 663, 2393, 346, 1820, 29, 93, 1824, 1188, 1572, 1192, 106, 251, 1266, 2418, 1204, 180, 440, 250, 571, 316, 573, 1214, 575]}, "next": null, "norm": "首次面对面会晤", "prev": {"py/id": 6}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 17, "Head0Text": "", "ID": 7, "StartOffset": 15, "TempPointer": "", "UpperRelationship": "R", "atom": "首次", "features": {"py/set": [2560, 1, 200, 2123, 1611, 204, 206, 17, 18, 1188, 1255, 110, 1207, 568]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 22, "Head0Text": "会晤", "ID": 15, "StartOffset": 17, "TempPointer": "", "UpperRelationship": "H", "atom": "面对面会晤", "features": {"py/set": [2565, 2446, 405, 1429, 663, 2393, 346, 1820, 29, 93, 1824, 1188, 1572, 1192, 106, 251, 1266, 2418, 1204, 316, 440, 250, 571, 572, 701, 1214]}, "next": null, "norm": "面对面会晤", "prev": {"py/id": 9}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 20, "Head0Text": "", "ID": 8, "StartOffset": 17, "TempPointer": "", "UpperRelationship": "R", "atom": "面对面", "features": {"py/set": [320, 321, 1, 5, 200, 204, 206, 17, 18, 1188, 110, 2031, 879, 569]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 22, "Head0Text": "", "ID": 9, "StartOffset": 20, "TempPointer": "", "UpperRelationship": "H", "atom": "会晤", "features": {"py/set": [1, 2446, 405, 1429, 663, 2393, 346, 1820, 29, 93, 1824, 1572, 1188, 440, 1192, 106, 237, 2418, 1266, 1204, 568, 701, 1214]}, "next": null, "norm": "会晤", "prev": {"py/id": 12}, "sons": [], "text": "会晤", "visited": false}, "norm": "面对面", "prev": {"py/id": 9}, "sons": [], "text": "面对面", "visited": false}, {"py/id": 13}], "text": "面对面会晤", "visited": false}, "norm": "首次", "prev": {"py/id": 6}, "sons": [], "text": "首次", "visited": false}, {"py/id": 10}], "text": "首次面对面会晤", "visited": false}, "norm": "美国总统特朗普和朝鲜总统金正恩", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "特朗普", "ID": 12, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "CN", "atom": "总统特朗普", "features": {"py/set": [576, 1537, 133, 139, 142, 147, 404, 148, 1815, 1433, 1050, 1822, 1188, 1636, 1702, 1192, 317, 1644, 108, 46, 1204, 1205, 1207, 1850, 571, 316, 573, 575]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 8, "Head0Text": "", "ID": 3, "StartOffset": 7, "TempPointer": "", "UpperRelationship": "X", "atom": "和", "features": {"py/set": [1, 453, 401, 28, 1188, 39, 565, 2552, 2425, 1726]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "金正恩", "ID": 14, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "H", "atom": "朝鲜总统金正恩", "features": {"py/set": [1537, 133, 135, 142, 147, 404, 148, 1815, 2459, 1821, 1822, 1188, 1702, 1192, 1204, 1205, 1207, 1850, 571, 316, 573, 317, 575, 576, 1239, 1240, 93, 1636, 1644]}, "next": null, "norm": "朝鲜总统金正恩", "prev": {"py/id": 19}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 12, "Head0Text": "总统", "ID": 13, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "equivM", "atom": "朝鲜总统", "features": {"py/set": [129, 133, 17, 147, 404, 148, 1430, 1815, 119, 1754, 1850, 1824, 1188, 1636, 1702, 1192, 1644, 1005, 1004, 110, 1204, 1205, 316, 1207, 570, 1659, 188, 317]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 15, "Head0Text": "", "ID": 6, "StartOffset": 12, "TempPointer": "", "UpperRelationship": "H", "atom": "金正恩", "features": {"py/set": [1537, 1, 131, 134, 135, 142, 404, 1815, 2459, 93, 1821, 1822, 1636, 1188, 1702, 1192, 1644, 1204, 1205, 1207, 569, 1850, 316]}, "next": null, "norm": "金正恩", "prev": {"py/id": 22}, "sons": [], "text": "金正恩", "visited": false}, "norm": "朝鲜总统", "prev": {"py/id": 19}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 10, "Head0Text": "", "ID": 4, "StartOffset": 8, "TempPointer": "", "UpperRelationship": "M", "atom": "朝鲜", "features": {"py/set": [1857, 1, 131, 129, 134, 1353, 2187, 2189, 142, 1614, 1489, 17, 1492, 796, 797, 1636, 1188, 1702, 1644, 110, 950, 119, 568, 1657, 1850, 1659, 188]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 12, "Head0Text": "", "ID": 5, "StartOffset": 10, "TempPointer": "", "UpperRelationship": "H", "atom": "总统", "features": {"py/set": [1, 131, 133, 404, 1430, 1815, 1754, 93, 1824, 1636, 1188, 1702, 1192, 1644, 1204, 1205, 1207, 568, 1850, 1659, 188]}, "next": null, "norm": "总统", "prev": {"py/id": 26}, "sons": [], "text": "总统", "visited": false}, "norm": "朝鲜", "prev": {"py/id": 19}, "sons": [], "text": "朝鲜", "visited": false}, {"py/id": 27}], "text": "朝鲜总统", "visited": false}, {"py/id": 23}], "text": "朝鲜总统金正恩", "visited": false}, "norm": "和", "prev": {"py/id": 18}, "sons": [], "text": "和", "visited": false}, "norm": "美国总统特朗普", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 1, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "M", "atom": "总统", "features": {"py/set": [1, 129, 131, 133, 17, 404, 86, 1815, 1430, 1433, 1754, 1824, 1636, 1188, 1702, 1644, 108, 110, 570, 119, 1850, 188]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 7, "Head0Text": "", "ID": 2, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "特朗普", "features": {"py/set": [1537, 1, 131, 134, 142, 404, 1815, 1049, 1050, 93, 1822, 1636, 1188, 1702, 1192, 1644, 1204, 1205, 1207, 569, 1850, 316]}, "next": null, "norm": "特朗普", "prev": {"py/id": 32}, "sons": [], "text": "特朗普", "visited": false}, "norm": "美国总统", "prev": {"py/id": 1}, "sons": [], "text": "美国总统", "visited": false}, {"py/id": 33}], "text": "美国总统特朗普", "visited": false}, {"py/id": 19}, {"py/id": 20}], "text": "美国总统特朗普和朝鲜总统金正恩", "visited": false}, {"py/id": 7}], "text": "美国总统特朗普和朝鲜总统金正恩首次面对面会晤", "visited": false}, "norm": "", "prev": null, "sons": [], "text": "", "visited": false}, "1": {"py/id": 2}, "2": {"py/id": 3}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": ["美国总统特朗普和朝鲜总统金正恩首次面对面会晤", "会晤"]}, {"py/tuple": ["", ""]}], "size": 3, "tail": {"py/id": 3}}
"""
    newnodelist = jsonpickle.loads(nodelist_str)
    print(newnodelist.root().CleanOutput().toJSON())


    x = DependencyTree()
    x.transform(newnodelist)
    print(x)
    print(x.digraph('graph'))
    print(x.digraph('simple'))
    print(x.digraph('simplegraph'))
    #print("^.O is: {}".format(x.FindPointerNode(x.root, "^.O", None)))