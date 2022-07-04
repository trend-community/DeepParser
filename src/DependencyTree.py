#Note: DAG is being used in this process, but actually the dependancytree is not pure DAG:
#    some of the graph can be cyclic.
# so it is required to have "root".

import utils    #for the Feature_...
from utils import *
import Lexicon
import FeatureOntology
import LogicOperation
from Rules import AndOrNotFeatures, SatisfiedFeatures

DanziDict = dict()

# class Variable: # for global variables in class
#     def __init__(self):
#         self.nodes = []
#
#     def __str(self):

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
        self.fulltext = ""
        self.fullnorm = ""
        self.fullatom = ""


    def transform(self, nodelist_origin):    #Transform from SentenceLinkedList to DAG
        try:
            nodelist = copy.deepcopy(nodelist_origin)   #don't modify the origin nodelist.
        except RecursionError:
            logging.error("The nodelist is too long ({} nodes) to transfer into DAG".format(nodelist_origin.size))
            raise Exception("Failed to transfer")
        except:
            logging.error("The nodelist is too long ({} nodes) to transfer into DAG. memory issue".format(nodelist_origin.size))
            raise Exception("Failed to transfer")
        self.fulltext = nodelist.root().text
        self.fullnorm = nodelist.root().norm
        self.fullatom = nodelist.root().atom
        root = nodelist.head
        if root.text == '' and utils.FeatureID_JS in root.features:
            root = root.next        #ignore the first empty (virtual) JS node

        temp_subgraphs = []
        # Collect all the leaf nodes into self.nodes. and subgraphs into temp_subgraphs
        while root is not None:
            #each "root" has a tree, independent from others.
            node = root
            nodestack = set()
            while node:
                if node.sons:
                    if len(node.sons) == 2 and len(node.text) == 2 and len(node.sons[0].text) == 1 and len(node.sons[1].text) == 1:
                        DanziDict.update({node: node.sons})     # kind of like single decendent node.
                    if node.next:
                        nodestack.add(node.next)
                    node = node.sons[0]
                else:
                    if not (node.text == '' and utils.FeatureID_JM  in node.features):
                        self.nodes.update({node.ID : copy.copy(node)})      # add leaf node to self.nodes.

                    if node == root:    #if node is in root level, don't get next.
                        if nodestack:
                            node = nodestack.pop()
                        else:
                            node = None
                        continue

                    node = node.next
                    if node is None and nodestack:
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
                            if subnode is None and nodestack:
                                subnode = nodestack.pop()
                        else:
                            if subnode.next:
                                nodestack.add(subnode.next)
                            subnode = subnode.sons[0]
                    else:   # this is a leaf node.
                        if subnode.ID not in self.nodes:
                            logging.warning("This leaf node {} is not in self.nodes list. Please check the rules. ".format(subnode))
                        else:
                            #  use the copy in self.nodes to apply feature modification, and copy pnorm
                            if utils.FeatureID_H in subnode.features:
                                subgraph.headID = subnode.ID
                                self.nodes[subnode.ID].features.update(subgraph.startnode.features)
                                if subgraph.startnode.pnorm:
                                    self.nodes[subnode.ID].pnorm = subgraph.startnode.pnorm
                                Lexicon.ApplyWordLengthFeature(self.nodes[subnode.ID])
                            else:
                                if not(subnode.text == '' and utils.FeatureID_JM  in subnode.features):
                                    subgraph.leaves.append([subnode.ID, subnode.UpperRelationship])
                        subnode = subnode.next
                        if subnode is None and nodestack:
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
        prevnode = None
        for node in sorted(self.nodes.values(), key=operator.attrgetter("StartOffset")):
            node.Index = index
            if prevnode:
                self._AddEdge(node.ID, "RIGHT", prevnode.ID)
                self._AddEdge(prevnode.ID, "LEFT", node.ID)
            prevnode = node
            index +=  1

        self._MarkNext()
        self.root = self._roots[0]

        # if logging.root.isEnabledFor(logging.DEBUG):
        #     logging.debug("End of transform:\n {}".format(self))


    #for multiple roots, mark "next" to make all nodes in one graph.
    def _MarkNext(self):
        if len(self._roots) == 1:
            return

        order = sorted(self._roots, key=lambda nodeid: self.nodes[nodeid].Index)
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
        for edge in self.graph:
            if startnode == edge[2]:
                relation = relation + 1

        if relation == 1:
            return True
        return False


    def getDanzi(self, nodeid):
        for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
            if edge[2] == nodeid:
                if  len(self.nodes[nodeid].text) == 1 and len(self.nodes[edge[0]].text) == 1 and self.onlyOneRelation(edge[0]):
                    if self.nodes[edge[0]].StartOffset < self.nodes[nodeid].StartOffset:
                        parent =  self.nodes[edge[0]].text + self.nodes[nodeid].text
                    else:
                        parent =  self.nodes[nodeid].text + self.nodes[edge[0]].text

                    for node in DanziDict.keys():
                        if node.text == parent:
                            return parent
        return None


    def pnorm(self):
        output = '{  "nodes": ['
        first = True
        for node in self.nodes.values():
            if node.pnorm:
                if first:
                    first = False
                else:
                    output += ", "

                if hasattr(node, "combinedtext"):
                    text = node.combinedtext
                else:
                    text = node.text
                output += """{{ "pnorm": "{}", "text": "{}", "offset": "{}"}}""".format(node.pnorm, text, node.StartOffset)

        output += '],'

        output += '"speciallinks": ['
        first = True
        for edge in sorted(self.graph, key=operator.itemgetter(2, 0)):
            if edge[1].startswith("#"):
                if first:
                    first = False
                else:
                    output += ", "
                output += """{{ "from": "{}", "link": "{}", "to": "{}"}}""".format(self.nodes[edge[2]].text, edge[1], self.nodes[edge[0]].text)

        output += '],'

        output += '"sentence_variables": ['
        first = True
        for key in [variablename for variablename in GlobalVariables if variablename.startswith("SENT_")]:
            if first:
                first = False
            else:
                output += ", "
            output += f"""{{ "{key}": "{GlobalVariables[key]} }}"""

        output += ']}'
        return output



    #the default output is in DOT language, compatible with Graphviz, Viz.js, d3-graphviz.
    def digraph(self, Type='graph'):
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Start making diagraph of {}. graph is:{}".format(Type, self.graph))
        output = ""
        if Type == 'simplegraph' :
            for edge in sorted(self.graph, key= operator.itemgetter(2, 0, 1)):
                if edge[1] != "LEFT" and edge[1] != "RIGHT":
                    output += """{}{{{}->{}}}; """.format(edge[1],
                                    self.nodes[edge[2]].text,
                                    self.nodes[edge[0]].text   )
        elif Type == 'simple2':
            for nodeid in sorted(self.nodes):
                output += """{}"{}" """.format(nodeid, self.nodes[nodeid].text)
            output += "{"
            for edge in sorted(self.graph, key= lambda e: e[2]):
                if edge[1] != "LEFT" and edge[1] != "RIGHT":
                    output += """{}->{} [{}]; """.format(edge[2], edge[0], edge[1])
            output += "}"
        elif Type == 'graphjson':
            output += '{  "nodes": ['
            first = True
            for node in sorted(self.nodes.values(), key=operator.attrgetter("Index")):
                if first:
                    first = False
                else:
                    output += ", "
                output += node.CleanOutput().toJSON()

            output += '],  "edges": ['
            first = True
            for edge in sorted(self.graph, key= operator.itemgetter(2, 0, 1)):
                if edge[1] != "LEFT" and edge[1] != "RIGHT":
                    if first:
                        first = False
                    else:
                        output += ", "

                    relation = edge[1]
                    if relation in Lexicon._LexiconlinkDisplay:
                        relation = Lexicon._LexiconlinkDisplay[relation]
                    output += '{{ "from":{}, "to":{}, "relation":"{}" }}'.format(edge[2], edge[0], relation)

            output += "]}"

        else:   #diagraph
            output = "digraph{"
            for node in sorted(self.nodes.values(), key=operator.attrgetter("Index")):
                nodeid = node.ID
                danzi = self.getDanzi(nodeid)
                tooltip = node.GetFeatures()
                if node.norm != node.text:
                    tooltip += " '{}'".format(node.norm.replace("\\", "\\\\\\\\").replace("\"", "\\\\\\\""))
                if node.atom != node.text:
                    tooltip += " /{}/".format(node.atom.replace("\\", "\\\\\\\\").replace("\"", "\\\\\\\""))
                if node.pnorm:
                    tooltip += " pnorm:{}".format(node.pnorm)
                if danzi:
                    output +=  "{} [label=\"{}\" tooltip=\"{}\"".format(nodeid, danzi, tooltip)
                    logging.warning(f"Danzi in {danzi} ")
                else:
                    if hasattr(node, "combinedtext"):
                        text = node.combinedtext
                    else:
                        text = node.text
                    escaptetext = text.replace("\\", "\\\\\\\\").replace("\"", "\\\\\\\"")
                    output += "{} [label=\"{}\" tooltip=\"{}\"".format(nodeid, escaptetext, tooltip)

                output += "];\n"
            output += "//edges:\n"
            for edge in sorted(self.graph, key= operator.itemgetter(2, 0, 1)):
                if edge[1] != "LEFT" and edge[1] != "RIGHT":
                    relation = edge[1]
                    if relation in Lexicon._LexiconlinkDisplay:
                        relation = Lexicon._LexiconlinkDisplay[relation]
                    output += "\t{}->{} [label=\"{}\"];\n".format(edge[2], edge[0], relation)

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
        self.nodes[node1id].ApplyFeature(FeatureOntology.GetFeatureID(relation))    #20201016 add.


    def _RemoveEdge(self, node1id, relation, parentid):
        if relation[0] == "~":  #revert
            self._RemoveEdge(parentid, relation[1:], node1id)
            return

        relationid = FeatureOntology.GetFeatureID(relation)

        for edge in [ e for e in self.graph if e[0] == node1id and e[2] == parentid]:
            edgefeature = FeatureOntology.SearchFeatureOntology(edge[3])
            if relationid == edge[3] or (edgefeature and relationid in edgefeature.ancestors):
                self.graph.remove(edge)


    def _CheckEdge(self, node1id, relation, parentid):
        relation = relation.strip()     # there were space.
        Reverse = False
        if relation[0] == "~":
            #logging.debug("_CheckEdge: Reverse! {}".format(relation))
            Reverse = True
            relation = relation[1:]

        relationid = FeatureOntology.GetFeatureID(relation)
        if Reverse:
            edgecandidates = [e for e in self.graph if e[0] == parentid and e[2] == node1id]
        else:
            edgecandidates = [e for e in self.graph if e[0] == node1id and e[2] == parentid]

        #for edge in sorted(edgecandidates, key = operator.itemgetter(2, 1, 0)):
        for edge in edgecandidates:
            if relationid == edge[3]:
                return True
            else:
                edgerelationnode = FeatureOntology.SearchFeatureOntology(edge[3])
                if edgerelationnode and relationid in edgerelationnode.ancestors:
                    return True
        return False


    # def LinearNodeOffset(self, nodeid, offset):
    #     startpoint = self.nodes[nodeid].Index
    #     targetindex = startpoint + offset
    #
    #     for n in  sorted(self.nodes.values(), key=operator.attrgetter("Index")):
    #         if n.Index == targetindex:
    #             return n.ID
    #     return None

    #because the "|" sign in SubtreePointer is expanded during compilation(_ExpandOrToken(OneList))
    #it is not longer process here.
    #FindPointerNode_Cache = {}         #not very safe to have this cache.
    def FindPointerNode(self, openID, SubtreePointer, rule, CurrentNodeID, ruletokenindex):
        #logging.debug("Dag.FindPointerNode for {}".format(SubtreePointer))
        # if (openID, SubtreePointer, rule.ID) in self.FindPointerNode_Cache:
        #     #logging.debug("FindPointerNode_Cache: hit!")
        #     return self.FindPointerNode_Cache[(openID, SubtreePointer, rule.ID)]

        if len(SubtreePointer) >= 1 and SubtreePointer[0] == '^':
            SubtreePointer = SubtreePointer[1:]

        nodeID = None
        for AndCondition in SubtreePointer.split("+"):
            Negation = False
            if len(AndCondition) > 1 and AndCondition[0] == "!":
                #logging.warning("FindPointerNode: Negation! {}".format(SubtreePointer))
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
            elif pointer == '~':
                #logging.warning("THIS POINTER in {}".format(rule))
                nodeID = CurrentNodeID
            elif pointer == 'Q':    #^Q point to the node that matchs the previous rule token.
                nodeID = rule.Tokens[ruletokenindex-1].MatchedNodeID
            else:
                if pointer.isdigit():
                    pointer_num = int(pointer)
                    try:
                        nodeID = rule.Tokens[pointer_num].MatchedNodeID
                    except AttributeError as e: #AttributeError: 'RuleToken' object has no attribute 'MatchedNodeID'
                        logging.error(e)
                        logging.error("FindPointerNode: The rule is written error, because the reference token is not yet matched. Please rewrite!")
                        logging.info(rule)
                        return None
                    except IndexError as e:
                        logging.error(e)
                        logging.error("FindPointerNode: The rule is written error, failed to find pointer {} IndexError!".format(pointer_num))
                        logging.info(rule)
                        return None

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
                    Found = False
                    # if relation == "LEFT":
                    #     nodeID = self.LinearNodeOffset(nodeID, -1)
                    #     if nodeID:
                    #         Found = True
                    # elif relation == "RIGHT":
                    #     nodeID = self.LinearNodeOffset(nodeID, 1)
                    #     if nodeID:
                    #         Found = True
                    # else:
                    relationid = FeatureOntology.GetFeatureID(relation)
                    for edge in sorted(self.graph, key= operator.itemgetter(2, 1, 0)):
                        #logging.debug("Evaluating edge{} with relation {}, node {}".format(edge, relation, nodeID))
                        if edge[2] == nodeID:
                            if relationid == edge[3]: # or relationid in FeatureOntology.SearchFeatureOntology(edge[3]):
                                nodeID = edge[0]
                                Found = True
                                logging.debug("   Found!")
                                break
                            else:
                                edgerelationnode = FeatureOntology.SearchFeatureOntology(edge[3])
                                if edgerelationnode and relationid in edgerelationnode.ancestors:
                                    nodeID = edge[0]
                                    Found = True
                                    logging.debug("   Found ontology ancesstor relation!")
                                    break

                    if not Found:
                        if not Negation:
                            return None
                        #logging.warning("Failed to find pointer {} in graph {}".format(SubtreePointer, self))
                        #return None     #Can't find the pointers.

                    #logging.info("Found this node {} for these pointers:{}".format(nodeID, pointers))

        if nodeID:
            #self.FindPointerNode_Cache[(openID, SubtreePointer, rule.ID)] = nodeID
            return nodeID
        else:
            logging.warning("Can't find {} pointer in this rule{}".format(SubtreePointer, rule))
            return None


    def ClearVisited(self):
        for nodeid in self.nodes:
            self.nodes[nodeid].visited = False


    def ClearHITFeatures(self):
        for nodeid in self.nodes:
            node = self.nodes[nodeid]
            if FeatureID_HIT in node.features:
                node.features.remove(FeatureID_HIT)
            if FeatureID_HIT2 in node.features:
                node.features.remove(FeatureID_HIT2)
            if FeatureID_HIT3 in node.features:
                node.features.remove(FeatureID_HIT3)

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

    def Unification(self, openID, rule, nodeID, Pointer, matchtype='norm'):
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

        _pointer = self.FindPointerNode(openID, P, rule, nodeID, -1)
        if _pointer and _pointer in self.nodes:
            StrPointerToken = self.nodes[_pointer]
            if not StrPointerToken:
                return False
        else:
            logging.error("can't find pointer: {}".format((openID, P, rule, nodeID, -1)))
            return False

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


    def MaxDistanceOfMatchNodes(self, rule):
        index_min = len(self.nodes)
        index_max = 0
        for i in range(rule.TokenLength):
            nodeID = rule.Tokens[i].MatchedNodeID
            node = self.nodes[nodeID]
            index_min = min(node.Index, index_min)
            index_max = max(node.Index, index_max)
        #logging.info("This rule, window size is {}; the MaxDistanceOfMatchNodes is {}.".format(rule.WindowLimit, index_max-index_min+1))
        return index_max-index_min+1


    def MaxDistanceToMatchedNodes(self, rule, _nodeID):
        _nodeIndex = self.nodes[_nodeID].Index
        index_max = 0
        for i in range(rule.TokenLength):
            if rule.Tokens[i].MatchedNodeID:
                nodeID = rule.Tokens[i].MatchedNodeID
                nodeIndex = self.nodes[nodeID].Index
                if abs(nodeIndex - _nodeIndex) > index_max:
                    index_max = abs(nodeIndex - _nodeIndex)

        return index_max


    # Part of Approximity
    def MatchAdjacency(self, Condition, OpenNodeID, rule, thisnode, ruletokenindex):
        if ">>" in Condition:
            _, ReferenceNodePointer = Condition.split(">>", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule, thisnode.ID, ruletokenindex)
            if not ReferenceNodeID  or thisnode.Index != self.nodes[ReferenceNodeID].Index + 1 :
                return False
        elif "<<" in Condition:
            _, ReferenceNodePointer = Condition.split("<<", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule, thisnode.ID, ruletokenindex)
            if not ReferenceNodeID  or thisnode.Index != self.nodes[ReferenceNodeID].Index - 1 :
                return False
        elif ">" in Condition:     #on the left side of the other pointer
            _, ReferenceNodePointer = Condition.split(">", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule, thisnode.ID, ruletokenindex)
            if not ReferenceNodeID  or thisnode.Index < self.nodes[ReferenceNodeID].Index :
                return False
        elif "<" in Condition:
            _, ReferenceNodePointer = Condition.split("<", 1)
            ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule, thisnode.ID, ruletokenindex)
            if not ReferenceNodeID  or thisnode.Index > self.nodes[ReferenceNodeID].Index :
                return False
        else:
            logging.error("MatchAdjacency: There should be either > or < in the Condition. \nrule:{}".format(rule))

        return True


    def TokenMatch(self, nodeID, ruletoken, OpenNodeID, rule, ruletokenindex):
        if ruletoken.AndText and "^" in ruletoken.AndText:
            # This is a pointer! unification comparison.
            if not self.Unification(OpenNodeID, rule, nodeID, Pointer=ruletoken.AndText,
                                matchtype=ruletoken.AndTextMatchtype):
                return False
        node = self.nodes[nodeID]

        try:
            logicmatch = LogicOperation.LogicMatch_notpointer(node, ruletoken)
        except RuntimeError as e:
            logging.error("Error in TokenMatch rule:" + str(rule))
            logging.error("Using " + ruletoken.word + " to match:" + node.text)
            logging.error(e)
            raise
        except Exception as e:
            logging.error("Using " + ruletoken.word + " to match:" + node.text)
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + ruletoken.word + " to match:" + node.text)
            logging.error(e)
            raise

        if not logicmatch:
            return False
        #might need open node for pointer
        # if logging.root.isEnabledFor(logging.DEBUG):
        #     logging.debug("DAG.TokenMatch: comparing ruletoken {} with nodeid {}".format(ruletoken, node))
        #     logging.debug("Dag.TokenMatch for SubtreePointer {} in rule token {}".format(ruletoken.SubtreePointer, ruletoken))

        # FOR DGAFSA, SubtreePointer and PointerCondition are the same.
        SubtreePointer = "+".join([ruletoken.SubtreePointer,ruletoken.PointerCondition]).strip("+")
        if not SubtreePointer:
            return True

        # if "~~"in SubtreePointer:
        #     SubtreePointer, ReferenceNodePointer = SubtreePointer.split("~~", 1)
        #     ReferenceNodeID = self.FindPointerNode(OpenNodeID, ReferenceNodePointer, rule)
        #     if abs(node.Index - self.nodes[ReferenceNodeID].Index ) > len(self.nodes)/3:
        #         return False

        # if not SubtreePointer:  #Apparently after comparing index with referencenode, the subtreepointer is not empty
        #     return True         # so the condition was like ^<
        #
        Satisfied = False
        for AndCondition in SubtreePointer.split("+"):
            if ">" in AndCondition or "<" in AndCondition:
                if not self.MatchAdjacency(AndCondition, OpenNodeID, rule, node, ruletokenindex):
                    return False
                continue
                # AndCondition = AndCondition.split(">", 1)[0]
                # AndCondition = AndCondition.split("<", 1)[0]

            Negation = False

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
            elif pointer == '~':
                start_nodeID = nodeID   # "this node"
            elif pointer == 'Q':    # ^Q point to the node that matchs the previous rule token.
                start_nodeID = rule.Tokens[ruletokenindex-1].MatchedNodeID
            else:
                if pointer.isdigit():
                    pointer_num = int(pointer)
                    if pointer_num == rule.Tokens.index(ruletoken):
                        start_nodeID = nodeID
                    else:
                        try:
                            start_nodeID = rule.Tokens[pointer_num].MatchedNodeID
                        except AttributeError as e: #AttributeError: 'RuleToken' object has no attribute 'MatchedNodeID'
                            logging.error(e)
                            logging.error("TokenMatch: The rule is written error, because the reference token is not yet matched. Please rewrite!")
                            logging.info(rule)
                            return False

                else:
                    pointer = "^" + pointer
                    for nodeid in sorted(self.nodes):
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
                        linkcount = len([e for e in self.graph if e[0] == nodeID and e[2] == start_nodeID and e[1] != "LEFT" and e[1] != "RIGHT"])
                        logging.debug("\tLink count from {}({}) to {}({}) is {}".format(self.nodes[start_nodeID].text,
                                self.nodes[start_nodeID].ID, self.nodes[nodeID].text, self.nodes[nodeID].ID, linkcount))
                        if relations == "LINKNUM1":
                            Satisfied = linkcount == 1
                        elif relations == "LINKNUM2":
                            Satisfied = linkcount == 2
                        elif relations == "LINKNUM3":
                            Satisfied = linkcount == 3
                    elif re.match("Link(\d\d?)", relations):   # LINKDIST0, LINKDIST1, LINKDIST2, LINKDIST3
                        distmatch = re.match("Link(\d\d?)", relations)
                        conditiondistance = int(distmatch.group(1))
                        linkdistance = self.NodeDistance(nodeID, start_nodeID, IgnoreNextLink=True, visitednodes=set())
                        # logging.info("\t.Link from {}({}) to {}({}) is {}".format(self.nodes[start_nodeID].text,
                        #         self.nodes[start_nodeID].ID, self.nodes[nodeID].text, self.nodes[nodeID].ID, linkdistance))

                        if linkdistance is None:
                            Satisfied = False
                        else:
                            Satisfied = linkdistance <= conditiondistance
                    elif re.match("Dist(\d\d?)", relations):   # Distance with Next, Left, Right
                        distmatch = re.match("Dist(\d\d?)", relations)
                        conditiondistance = int(distmatch.group(1))
                        linkdistance = self.NodeDistance(nodeID, start_nodeID, IgnoreNextLink=False, visitednodes=set())
                        # logging.info("\t.Dist from {}({}) to {}({}) is {}".format(self.nodes[start_nodeID].text,
                        #                                                                 self.nodes[start_nodeID].ID,
                        #                                                                 self.nodes[nodeID].text,
                        #                                                                 self.nodes[nodeID].ID,
                        #                                                                 linkdistance))
                        if linkdistance is None:
                            Satisfied = False
                        else:
                            Satisfied = linkdistance <= conditiondistance
                    elif re.match("Radius(\d\d?)", relations):   # Radius, text distance, or window size
                        distmatch = re.match("Radius(\d\d?)", relations)
                        conditiondistance = int(distmatch.group(1))
                        textdistance = abs(self.nodes[start_nodeID].Index - self.nodes[nodeID].Index)
                        # logging.debug("\t.Radius from {}({}) to {}({}) is {}".format(self.nodes[start_nodeID].text,
                        #         self.nodes[start_nodeID].ID, self.nodes[nodeID].text, self.nodes[nodeID].ID, textdistance))

                        Satisfied = textdistance <= conditiondistance
                    else:
                        Satisfied = self._CheckEdge( nodeID, relationlist[0], start_nodeID)
                        # if Satisfied:
                        #     logging.debug("Checked relations {} and found it works for start_node{}".format(relations, self.nodes[start_nodeID]))
                        #     logging.debug("\tnode:{}".format(self.nodes[nodeID]))
                        #     logging.debug("\tnodes:{}\ngraph:{}".format(["({})[{}]".format(self.nodes[n].ID, self.nodes[n].text) for n in self.nodes], self.graph))
                elif len(relationlist) == 2:
                    for second_nodeID in self.connectedtonode(nodeID):
                        Satisfied = self._CheckEdge( nodeID, relationlist[1], second_nodeID) and \
                                        self._CheckEdge(second_nodeID, relationlist[0], start_nodeID)
                        if Satisfied:
                            break
                elif len(relationlist) == 3:
                    for second_nodeID in self.connectedtonode(nodeID):
                        for third_nodeID in self.connectedtonode(second_nodeID):
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
                return False
        return True


    def connectedtonode(self, nodeid):
        return [e[0] for e in self.graph if e[2] == nodeid]


    #breadth first search, only way to do it right
    def NodeDistance(self, node1id, node2id, IgnoreNextLink, visitednodes):
        if  IgnoreNextLink:
            IgnoreEdges = (FeatureOntology.GetFeatureID('next'),
                         FeatureOntology.GetFeatureID('LEFT'),
                         FeatureOntology.GetFeatureID('RIGHT'))
        else:
            IgnoreEdges = ()

        visitednodes.add(node1id)
        distance = 0
        while True:
            if node2id in visitednodes:
                return distance

            node1neighbours = set()
            for edge in self.graph:
                if edge[3] in IgnoreEdges:
                    continue
                if edge[0] in visitednodes and edge[2] not in visitednodes:
                    node1neighbours.add(edge[2])
                elif edge[2] in visitednodes and edge[0] not in visitednodes:
                    node1neighbours.add(edge[0])

            if node1neighbours:
                visitednodes.update(node1neighbours)
            else:
                break
            distance += 1
        return None


    def CollectSonList_onelevel(self, nodeid):
        return [self.nodes[edge[0]] for edge in self.graph if edge[2] == nodeid and edge[1] != "next" and edge[1] != "NX" ]


    # the ideal way is to recursively traverse the graph, while avoiding repeat nodes (loop)
    # now doing it in 10 levels should be good enough to get the first and last node of the subgraph.
    def CollectSonList(self, nodeid, level=10):
        """
        Collect decendents of a node.
        :param level:
        :param nodeid:
        :return:
        """
        generations = [[nodeid]]    # generations[0] = [nodeid] as starting poin.

        for g in range(1, level):
            newgeneration = []
            for sonid in generations[g-1]:
                newgeneration += [edge[0] for edge in self.graph
                                if edge[2] == sonid and edge[1] not in ["next", "NX", "LEFT", "RIGHT"]
                                and edge[0] not in [ids for prevg in range(g) for ids in generations[prevg] ] ]
            if newgeneration :
                generations.append(newgeneration)
            else:
                break   #stop searching for next generation if this generation is blank .

        idlist = set( [ids for generation in generations for ids in generation ])

        return idlist

    #
#     def ApplyDagActions_IEPair(self, OpenNode, node, rule, ieaction):
#         ieaction = ieaction.strip("#")
#         if "=" not in ieaction:
#             node.iepair = "{}={}".format(ieaction, node.norm)
#             return
#
#         iekey, ievalue = ieaction.split("=", 1)
#         if "^" not in ievalue:
#             node.iepair = "{}={}".format(iekey, ievalue)
#             return
#         else:
#
#             if ievalue.endswith(".TREE"):
#                 ParentPointer = ievalue[:ievalue.rfind('.')]  # find pointer up the the last dot "."
#                 parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer, rule, node.ID)
#                 if not parentnodeid:
#                     return
#                 sonlist = self.CollectSonList(parentnodeid)
#                 value = ""
#                 for n in  sorted(sonlist, key=operator.attrgetter("StartOffset")):
#                     #logging.warning("node {}.norm={}".format(n.text, n.norm))
#                     value += n.norm
#
#                 node.iepair = "{}={}".format(iekey, value)
#                 return
#
#             if ievalue.endswith(".REST"):
#                 ParentPointer = ievalue[:ievalue.rfind('.')]  # find pointer up the the last dot "."
#                 parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer, rule, node.ID)
#                 if not parentnodeid:
#                     return
#
#                 node.iepair = "{}={}".format(iekey, self.fullnorm[self.nodes[parentnodeid].StartOffset:])
#                 return
#             else:
#                 pointernodeid =  self.FindPointerNode(OpenNode.ID, ievalue, rule, node.ID)
#                 if pointernodeid:
#                     node.iepair = "{}={}".format(iekey, self.nodes[pointernodeid].norm)
#                 else:
#                     logging.warning("Can't find this pointer {} in this node {}".format(ievalue, node.text))
# #        raise Exception("Todo: more ^A.S ^A ^A.O ie value: {}".format(ieaction))


    def LastNodeInFuzzyString(self, MatchString):
        if MatchString in self.fulltext:
            MatchMethod = "text"
        elif MatchString in self.fullnorm:
            MatchMethod = "norm"
        elif MatchString in self.fullatom:
            MatchMethod = "atom"
        else:
            logging.error("Not matched Fuzzy String. Should not get to LastNodeInFuzzyString()")
            raise RuntimeError("Wrong logic to LastNodeInFuzzyString()")

        nodestring = ""
        for node in sorted(self.nodes.values(), key=operator.attrgetter("StartOffset")):
            if MatchMethod == "text":
                nodetext = node.text
            elif MatchMethod == "norm":
                nodetext = node.norm
            else:
                nodetext = node.atom

            if nodestring:
                nodestring += nodetext
                if nodestring not in MatchString:
                    nodestring = ""     #reset to blank.

            if not nodestring and MatchString.startswith(nodetext):
                nodestring = nodetext

            if nodestring == MatchString:
                return node

        logging.error("Failed to get LastNodeInFuzzyString()")
        raise RuntimeError("Failed to get LastNodeInFuzzyString()")


    def ApplyDagActions(self, OpenNode, node, actinstring, rule, ruletokenindex):
        # iepairmatch = re.search("(#.*#)", actinstring)
        # if iepairmatch:
        #     ieaction = iepairmatch.group(1)
        #     actinstring = actinstring.replace(iepairmatch.group(1), '')
        #     self.ApplyDagActions_IEPair( OpenNode, node, rule, ieaction)

        Actions = actinstring.split()

        for Action in copy.copy(Actions):
            if "---" in Action:
                ParentPointer = Action[:Action.rfind('.')]  #find pointer up the the last dot "."
                parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer, rule, node.ID, ruletokenindex)
                if not parentnodeid:
                    return

                if parentnodeid == node.ID: # ^~.--- , remove every edge of current node
                    self.graph = set([edge for edge in self.graph if edge[0] != node.ID and edge[2] != parentnodeid])
                    logging.debug("Dag Action {}: Removed all edge of {} ".format(Action, node.ID))
                elif "~---" in Action:
                    self.graph = set([edge for edge in self.graph if edge[0] != parentnodeid or edge[2] != node.ID])
                    logging.debug("Dag Action {}: Removed all edge from {} to {}".format(Action, parentnodeid, node.ID))
                else:
                    self.graph = set([edge for edge in self.graph if edge[0] != node.ID or edge[2] != parentnodeid])
                    logging.debug("Dag Action {}: Removed all edge from {} to {}".format(Action, parentnodeid, node.ID))
                Actions.pop(Actions.index(Action))

        _ToAddIntoGlobalTempLexicon = False
        for Action in sorted(Actions, key=lambda d:(d[-1])):
            if "=" in Action:
                #logging.warning(f"Action:{Action}")

                variable_k, variable_v = Action.split("=", 1)
                variable_v = variable_v.replace("\\SPACE", " ")  # use \SPACE for space
                EqualSignNum = Action.count("=")
                if EqualSignNum > 1:
                    logging.warning(f"This action has more than 1 equal sign: {Action}. The original actionstring is {actinstring}. The rule is: {rule}")
                    logging.warning(f"Now it is parsed as '{variable_k}' == '{variable_v}'. Please confirm!")


                oldvalue = None
                if variable_k.endswith("+"):    # when the equation is "abc+=THIS", keep the oldvalue.
                    variable_k = variable_k[:-1]
                    if variable_k in utils.GlobalVariables:
                        oldvalue = utils.GlobalVariables[variable_k]

                if variable_k.startswith("SVO"):    #SVO add the nodes id to a set
                    tempkeyname = "temp_" + variable_k
                    if tempkeyname not in utils.GlobalVariables:
                        utils.GlobalVariables[tempkeyname] = set()


                if variable_v == """THIS""" or variable_v == """'THIS'""":
                    utils.GlobalVariables[variable_k] = node.norm
                elif variable_v == """\"THIS\"""":
                    utils.GlobalVariables[variable_k] = node.text
                elif variable_v == """/THIS/""":
                    utils.GlobalVariables[variable_k] = node.atom
                else:
                    # abc="句子中心:"+^1+"..."+^2.obj+"..."+^6   (20210111)
                    if "+" in variable_v or "^" in variable_v:
                        segments = variable_v.split("+")
                        result = ""
                        for segment in segments:
                            if segment[0] == "\"" and segment[-1] == "\"":
                                result += segment[1:-1].replace("\\SPACE", " ")
                            else:
                                if segment[0] == "^":
                                    if segment[1] == "*":   # ^*(feature1 feature2)
                                        idlist = self.CollectSonList(node.ID, level=2)
                                        idlist.add(node.ID)  # add node.id into the son list as whole tree.

                                        if len(segment) < 3:    # only "^*", then return all nodes
                                            if variable_k.startswith("SVO"):  # SVO add the nodes id to a set
                                                tempkeyname = "temp_" + variable_k
                                                utils.GlobalVariables[tempkeyname].update(idlist)
                                            else:
                                                result += "".join([self.nodes[node_id].text for node_id in idlist])

                                        else:
                                            _AndFeatures, _OrFeatureGroups, _NotFeatures = AndOrNotFeatures(segment[3:-1])
                                            for _node in sorted([self.nodes[node_id] for node_id in idlist ] , key=lambda x: x.Index):
                                                if SatisfiedFeatures(_node.features, _AndFeatures, _OrFeatureGroups, _NotFeatures):
                                                    if variable_k.startswith("SVO"):  # SVO add the nodes id to a set
                                                        tempkeyname = "temp_" + variable_k
                                                        utils.GlobalVariables[tempkeyname].add(_node.ID)
                                                    else:
                                                        result += _node.text

                                    elif segment[1] == "(":  # ^(.obj|.subj)(feature1 feature2)
                                        pass
                                    else:   # normal ^.2.obj
                                        pointtotokenid = self.FindPointerNode(OpenNode.ID, segment, rule, node.ID, ruletokenindex)
                                        if pointtotokenid:
                                            result += self.nodes[pointtotokenid].text
                                        else:
                                            logging.warning(f"Can't find this pointer {segment} in this action {Action}. ignore")
                                else:
                                    logging.warning(f"Wrong in action {Action}: don't know how to deal with {segment} ")
                        utils.GlobalVariables[variable_k] = result
                    else:
                        if variable_v[0] == "\"" and variable_v[-1] == "\"":
                            utils.GlobalVariables[variable_k] = variable_v[1:-1].replace("\\SPACE", " ")
                        else:
                            utils.GlobalVariables[variable_k] = variable_v

                if oldvalue:
                    if utils.LanguageType == "WESTERN":
                        utils.GlobalVariables[variable_k] = oldvalue + " " + utils.GlobalVariables[variable_k]
                    else:
                        utils.GlobalVariables[variable_k] = oldvalue + utils.GlobalVariables[variable_k]
                continue    #

            if Action[0] == '^':
                ParentPointer = Action[:Action.rfind('.')]  #find pointer up the the last dot "."
                parentnodeid = self.FindPointerNode(OpenNode.ID, ParentPointer, rule, node.ID, ruletokenindex)
                if not parentnodeid:
                    return

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
                        # combine all sons text, if adjacent, to this node.
                        logging.info(f"DAG Combine +++ for node {node.text}")
                        self.CombineNode(node)

                        #logging.error("There should be no +++ operation in DAG.")
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

                    avn = Action.strip("+").lower()
                    if avn in ['a', 'v', 'n']:
                        Blocklist = avn + "Blocklist"
                        for f in FeatureOntology._AppendixLists[Blocklist]:
                            if f in node.features:
                                node.features.remove(f)

                continue

            if Action[0] == '\'':
                #Make the norm of the token to this key
                node.norm = Action[1:-1]
                continue
            if Action[0] == '%':
                # Make the pnorm of the token to this key
                node.pnorm = Action[1:-1]
                logging.info(f" pnorm:{Action}")
                continue
            if Action[0] == '/':
                #Make the atom of the token to this key
                if Action[1] == "+":
                    node.atom = node.atom + Action[1:-1]
                else:
                    node.atom = Action[1:-1]
                node.features.update(Lexicon.StemFeatures(node.atom))
                continue
            if Action[0] == '+': # discontinuous concatenation
                TargetPointer = Action.strip("+")
                TargetToken = None
                for _node in self.nodes:
                    if self.nodes[_node].TempPointer == TargetPointer:
                        TargetToken = self.nodes[_node]
                        break
                if TargetToken:
                    node.atom += TargetToken.atom
                    node.norm += TargetToken.norm
                else:
                    logging.warning("Can't find {} in this rule.".format(Action))
                continue

            ActionID = FeatureOntology.GetFeatureID(Action)
            if ActionID == utils.FeatureID_GLOBAL:
                _ToAddIntoGlobalTempLexicon = True      # apply this action after all feature are applied.
            else:
                if ActionID != -1:
                    #logging.debug(f"DAG: Apply feature {Action} ID {ActionID} to node {node.text}")
                    node.ApplyFeature(ActionID)
                else:
                    logging.warning("Wrong Action to apply:" + Action +  " in action string: " + actinstring)


            if Action == "NEUTRAL":
                 FeatureOntology.ProcessSentimentTags(node.features)

        if _ToAddIntoGlobalTempLexicon:
            Lexicon.AddDocumentTempLexicon(node.text, node.features)


    def OutputSpecialLinks(self):
        output = ""
        for edge in sorted(self.graph, key=operator.itemgetter(2, 0)):
            if edge[1].startswith("#"):
                output += "{} {} = {}\n".format(self.nodes[edge[2]].text, edge[1], self.nodes[edge[0]].text)
        return output


    def pnorm_text(self):
        output = ""
        for node in sorted(self.nodes.values(), key=operator.attrgetter("StartOffset")):
            if node.pnorm:
                if hasattr(node, "combinedtext"):
                    text = node.combinedtext
                else:
                    text = node.text
                output += "{} : {}\n".format(node.pnorm, text)
        return output


    def CombineNode(self, node):
        # if hasattr(node, "combined") and node.combined:
        #     logging.info("This node is combined. don't do it again")
        #     return

        sonids = self.CollectSonList(node.ID)
        sons = sorted([self.nodes[node_id] for node_id in sonids ] , key=lambda x: x.Index)

        sonindexes = sorted([n.Index for n in sons])
        CenterIndex = node.Index

        StartIndex = CenterIndex
        for i in range(CenterIndex-1, 0-1, -1):
            if i in sonindexes:
                StartIndex = i
            else:
                break   # when there is one discontinue, stop.

        EndIndex = CenterIndex
        for i in range(CenterIndex + 1, max(sonindexes)+1, +1):
            if i in sonindexes:
                EndIndex = i
            else:
                break  # when there is one discontinue, stop.

        logging.info(f"The combination of {node.text} is from {StartIndex} to {EndIndex}")
        NewText = ""
        for i in range(sonindexes.index( StartIndex), sonindexes.index(EndIndex)+1):
            NewText += sons[i].text
            logging.info(f"adding {sons[i].text} it's Index is {sons[i].Index}, it's StartIndex={sons[i].StartIndex}. it's ID={sons[i].ID}")

        node.combinedtext = NewText
        logging.info(f"New Text: {NewText}")


if __name__ == "__main__":

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    # import ProcessSentence
    # ProcessSentence.LoadCommon()
    #
    # Sentence = "买了香奈儿眉笔"
    #
    # nodelist, _, _ = ProcessSentence.LexicalAnalyze(Sentence)
    #
    # nodelist_str = jsonpickle.dumps(nodelist)
    # print(nodelist_str)

    nodelist_str = """ {"py/object": "Tokenization.SentenceLinkedList", "get_cache": {"0": {"py/object": "Tokenization.SentenceNode", "EndOffset": 0, "Head0Text": "", "ID": 47, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "", "features": {"py/set": [108, 107, 28, 1438]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 50, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "", "atom": "，你看看", "features": {"py/set": [2565, 198, 1193, 106, 105, 108, 1434, 571, 28, 29, 1438]}, "next": null, "norm": ",你看看", "pnorm": "", "prev": {"py/id": 1}, "sons": [{"py/object": "Tokenization.SentenceNode", "EndOffset": 1, "Head0Text": "", "ID": 44, "StartOffset": 0, "TempPointer": "", "UpperRelationship": "X", "atom": "，", "features": {"py/set": [1, 2565, 198, 1193, 108, 44, 45, 566, 28, 1438]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 49, "StartOffset": 1, "TempPointer": "", "UpperRelationship": "X", "atom": "你看看", "features": {"py/set": [1280, 1, 2568, 206, 207, 208, 404, 1434, 2459, 28, 29, 1827, 2406, 1831, 1193, 106, 2414, 2096, 2424, 570, 316, 317, 1278, 2431]}, "next": {"py/object": "Tokenization.SentenceNode", "EndOffset": 4, "Head0Text": "", "ID": 48, "StartOffset": 4, "TempPointer": "", "UpperRelationship": "H", "atom": "", "features": {"py/set": [93, 2565, 198, 105, 106, 28, 29, 1434]}, "next": null, "norm": "", "pnorm": "", "prev": {"py/id": 5}, "sons": [], "text": "", "visited": false}, "norm": "你看看", "pnorm": "", "prev": {"py/id": 4}, "sons": [], "text": "你看看", "visited": false}, "norm": ",", "pnorm": "", "prev": {"py/id": 1}, "sons": [], "text": "，", "visited": false}, {"py/id": 5}, {"py/id": 6}], "text": "，你看看", "visited": false}, "norm": "", "pnorm": "", "prev": null, "sons": [], "text": "", "visited": false}, "1": {"py/id": 2}}, "head": {"py/id": 1}, "isPureAscii": false, "norms": [{"py/tuple": ["", ""]}, {"py/tuple": [",你看看", ""]}], "size": 2, "tail": {"py/id": 2}}
"""
    newnodelist = jsonpickle.loads(nodelist_str)
    print(newnodelist.root().CleanOutput().toJSON())

    #
    # _x = DependencyTree()
    # x.transform(newnodelist)
    # print(x)
    # print(x.digraph('graph'))
    # print(x.digraph('simple'))
    # print(x.digraph('simplegraph'))
    # #print("^.O is: {}".format(x.FindPointerNode(x.root, "^.O", None)))