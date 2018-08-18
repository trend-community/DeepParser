import logging, re, json, jsonpickle, configparser, os
import sqlite3
from functools import lru_cache


ParserConfig = configparser.ConfigParser()
ParserConfig.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.ini'))
maxcachesize = int(ParserConfig.get("main", "maxcachesize"))
runtype = ParserConfig.get("main", "runtype").lower()

ChinesePattern = re.compile(u'[\u4e00-\u9fff]')
jsonpickle.set_encoder_options('json', ensure_ascii=False)

FeatureID_JS = None
FeatureID_JS2 = None
FeatureID_JM2 = None
FeatureID_JM = None
FeatureID_0 = -8
FeatureID_CD = None
FeatureID_punc = None
FeatureID_SYM = None
FeatureID_NNP = None
FeatureID_External = None
FeatureID_OOV = None
FeatureID_CM = None
FeatureID_NEW = None
FeatureID_SpaceQ = None
FeatureID_SpaceH = None
FeatureID_FULLSTRING = None

FeatureID_VB = None
FeatureID_Ved = None
FeatureID_Ving = None

FeatureID_H = None
FeatureID_Subj = None
FeatureID_Obj = None
FeatureID_Pred = None

FeatureID_AC = None
FeatureID_NC = None
FeatureID_VC = None

FeatureID_comPair = None


IMPOSSIBLESTRING = "@#$%@impossible@"
IMPOSSIBLESTRINGLP = "@#$%@leftparenthesis@"
IMPOSSIBLESTRINGRP = "@#$%@rightparenthesis@"
IMPOSSIBLESTRINGSQ = "@#$%@singlequote@"
IMPOSSIBLESTRINGCOLN = "@#$%@coln@"
IMPOSSIBLESTRINGEQUAL = "@#$%@equal@"
IMPOSSIBLESTRINGSLASH = "@#$%@slash@"   #for the norms only.
IMPOSSIBLESTRINGGREATER = "@#$%@greater@"   #for chunks only.
IMPOSSIBLESTRINGLESS = "@#$%@less@"   #for chunks only.

# for baseline format
SYM_PAIR_HEAD = ('H', '^')
SYM_HYPHEN = '-'
SYM_PARENTHESIS = { # key is embeddig depth, starting from 0
        0 : ['<', '>'],
        1 : ['(', ')'],
        2 : ['[', ']'],
        3 : ['{', '}']
        }

from enum import Enum
class LexiconLookupSource(Enum):
    Exclude = 0
    defLex = 1
    External = 2
    oQcQ = 3


def InitGlobalFeatureID():
    global FeatureID_JS, FeatureID_JS2, FeatureID_JM2, FeatureID_JM, FeatureID_0
    global FeatureID_CD, FeatureID_punc, FeatureID_SYM, FeatureID_NNP, FeatureID_External
    global FeatureID_OOV,FeatureID_CM, FeatureID_NEW, FeatureID_SpaceQ, FeatureID_SpaceH, FeatureID_FULLSTRING
    global FeatureID_VB, FeatureID_Ved, FeatureID_Ving
    global FeatureID_H, FeatureID_Subj, FeatureID_Obj, FeatureID_Pred
    global FeatureID_AC, FeatureID_NC, FeatureID_VC, FeatureID_comPair
    if not FeatureID_JS2:
        import FeatureOntology
        FeatureID_JS = FeatureOntology.GetFeatureID("JS")
        FeatureID_JS2 = FeatureOntology.GetFeatureID("JS2")
        FeatureID_JM2 = FeatureOntology.GetFeatureID("JM2")
        FeatureID_JM = FeatureOntology.GetFeatureID("JM")
        FeatureID_0 = FeatureOntology.GetFeatureID("0")
        FeatureID_CD = FeatureOntology.GetFeatureID("CD")
        FeatureID_punc = FeatureOntology.GetFeatureID("punc")
        FeatureID_SYM = FeatureOntology.GetFeatureID("SYM")
        FeatureID_NNP = FeatureOntology.GetFeatureID("NNP")
        FeatureID_External = FeatureOntology.GetFeatureID("External")
        FeatureID_OOV = FeatureOntology.GetFeatureID("OOV")
        FeatureID_CM = FeatureOntology.GetFeatureID("CM")
        FeatureID_NEW = FeatureOntology.GetFeatureID("NEW")
        FeatureID_SpaceQ = FeatureOntology.GetFeatureID("spaceQ")
        FeatureID_SpaceH = FeatureOntology.GetFeatureID("spaceH")
        FeatureID_FULLSTRING = FeatureOntology.GetFeatureID("FULLSTRING")
        FeatureID_VB = FeatureOntology.GetFeatureID("VB")
        FeatureID_Ved = FeatureOntology.GetFeatureID("Ved")
        FeatureID_Ving = FeatureOntology.GetFeatureID("Ving")

        FeatureID_H = FeatureOntology.GetFeatureID("H")
        FeatureID_Subj = FeatureOntology.GetFeatureID("Subj")
        FeatureID_Obj = FeatureOntology.GetFeatureID("Obj")
        FeatureID_Pred = FeatureOntology.GetFeatureID("Pred")

        FeatureID_AC = FeatureOntology.GetFeatureID("AC")
        FeatureID_NC = FeatureOntology.GetFeatureID("NC")
        FeatureID_VC = FeatureOntology.GetFeatureID("VC")

        FeatureID_comPair = FeatureOntology.GetFeatureID("comPair")

        FeatureOntology.BarTagIDs = [[FeatureOntology.GetFeatureID(t) for t in row] for row in FeatureOntology.BarTags]
        for IDList in FeatureOntology.BarTagIDs:
            FeatureOntology.BarTagIDSet.update(set(IDList))
        FeatureOntology.SentimentTagIDSet = [FeatureOntology.GetFeatureID(t) for t in FeatureOntology.SentimentTags]
        FeatureOntology.SentimentTagIDSet = set(FeatureOntology.SentimentTagIDSet)

# return -1 if failed. Should throw error?
@lru_cache(1000000)
def SearchPair(string, tagpair, Reverse=False):
    depth = 0
    if Reverse:
        i = len(string)-1
        direction = -1
        currentTag = tagpair[1]
        targetTag = tagpair[0]
    else:
        i = 0
        direction = 1
        currentTag = tagpair[0]
        targetTag = tagpair[1]
    while 0<=i<len(string):
        if string[i] == targetTag:
            depth -= 1
            if depth == -1: # found!
                return i
        elif string[i] == currentTag:
            depth += 1
        i += direction
    logging.error(" Can't find a pair tag " + tagpair[0] + " in:" + string)
    return -1
    #raise RuntimeError(" Can't find a pair tag!" + string)
    #return -1


@lru_cache(100000)
def _SeparateComment(line):
    line = line.strip()
    SlashLocation = line.find("//")
    if SlashLocation < 0:
        return line, ""
    else:
        return line[:SlashLocation].strip(), line[SlashLocation+2:].strip()


@lru_cache(50000)
def SeparateComment(multiline):
    lines = multiline.splitlines()
    content = ""
    comment = ""
    for line in lines:
        _content, _comment = _SeparateComment(line)
        if _content:
            content += "\n" + _content
        if _comment:
            comment += " //" + _comment
    return content.strip(), comment.strip()


@lru_cache(100000)
#Can be expand for more scenario.
# unicode numbers (or English "one", "two"...) should be in lexicon to have "CD" feature.
#       so not to be included in here.
def IsCD(word):
    try:
        _ = float(word)
        return True
    except ValueError:
        return False


def IsAscii_List(Sentences):
    if isinstance(Sentences, list):
        Sentence = "".join(Sentences)
        return IsAscii(Sentence)
    else:
        logging.error("This is not a list")
        return False


@lru_cache(50000)
def IsAscii(Sentence):
    try:
        Sentence.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True


@lru_cache(50000)
def IsAlphaLetter(Sentence):
    if not hasattr(IsAlphaLetter, "letters"):
        IsAlphaLetter.letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    for c in Sentence:
        if c not in IsAlphaLetter.letters:
            return False
    return True


@lru_cache(50000)
def RemoveExcessiveSpace(Content):
    #Remove any whitespace around | sign, so it is made as a word.
    r = re.compile("\s*\|\s*", re.MULTILINE)
    Content = r.sub("|", Content)

    r = re.compile("<\s*", re.MULTILINE)
    Content = r.sub("<", Content)

    r = re.compile("\s*>", re.MULTILINE)
    Content = r.sub(">", Content)

    Content = Content.strip(";")    # ";" sign at the end of rule is not useful.

    return Content


SignsToIgnore = "{};"
Pairs = ['[]', '()', '""', '\'\'', '//']

# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or starting of next token.
@lru_cache(100000)
def SearchToEnd(string, Reverse=False):
    if not string:      # if it is empty
        return 0
    if Reverse:
        i = len(string)-1
        targetTagIndex = 1
        direction = -1
    else:
        i = 0
        targetTagIndex = 0
        direction = 1
    while 0<=i<len(string):
        modified = False
        for pair in Pairs:
            if string[i] == pair[targetTagIndex]:
                #if i>0 and string[i-1] == "|":
                if i > 0 and "|" in string[:i]: # for case as: "[a]|^V[b]"
                    endofpair = SearchPair(string[i+1:], pair, Reverse)
                    if endofpair >= 0:
                        if Reverse:
                            i -= endofpair +1
                        else:
                            i += endofpair +1
                        modified = True
                    else:
                        raise RuntimeError("Can't find a pair in _SearchToEnd()")
                        #return -1   # error. stop the searching immediately.
        if string[i] in SignsToIgnore:
            return i-direction
        if string[i].isspace():
            return i-direction

        # if string[i] in "[(":   #start of next token
        #     return i-direction
        if not modified:
            for pair in Pairs:
                if string[i] == pair[targetTagIndex]:
                    return i-direction
        i += direction
    return i


#Return the word before the first "_";
# If there is no "_", return the whole word
@lru_cache(100000)
def GetPrefix(Name):
    match = re.findall("(.*?)_\d", Name)
    if match:
        return match[0]
    else:
        return Name


def OutputStringTokens_json(strTokens):
    from collections import OrderedDict
    output = json.dumps(OrderedDict([{'word': token.text, 'feature': token.GetFeatures()} for token in strTokens if token.stem]), sort_keys=False, ensure_ascii=False)

    return output


def OutputStringTokens_oneliner(strTokenList, NoFeature=False):
    output = ""
    node = strTokenList.head
    while node:
        if output:
            output += " "
        output += node.oneliner(NoFeature)
        node = node.next
    return output


def OutputStringTokensSegment_oneliner(strTokenList):
    output = ""
    node = strTokenList.head
    while node:
        # if output:
        #     output += " "
        output += node.onelinerSegment()
        node = node.next
    output = output[:-1]
    return output


def OutputStringTokens_onelinerSA(dag):
    # print("Dag:{}".format(dag))
    output = ""
    TargetFeature = "Target"
    ProFeature = "Pro"
    ConFeature = "Con"
    PosEmo = "PosEmo"
    NegEmo = "NegEmo"
    Neutral = "Neutral"
    Needed = "Needed"
    Key = "Key"
    Value = "Value"
    nodes = dag.nodes
    nodelist = list(nodes.values())
    nodelist.sort(key=lambda x:x.StartOffset)
    for node in nodelist:
        output += node.text + "/"
        featureString = node.GetFeatures()
        featureSet = featureString.split(",")
        # print (featureSet)
        if TargetFeature in featureSet:
            output +=  TargetFeature + " "
        if ProFeature in featureSet:
            output +=  ProFeature + " "
        if ConFeature in featureSet:
            output += ConFeature + " "
        if PosEmo in featureSet:
            output +=  PosEmo + " "
        if NegEmo in featureSet:
            output +=  NegEmo + " "
        if Needed in featureSet:
            output += Needed + " "
        if Neutral in featureSet:
            output += Neutral + " "
        if Key in featureSet:
            output +=  Key + " "
        if Value in featureSet:
            output +=  Value + " "
        if output.endswith("/"):
            output = output[:-1]
    return output

def OutputStringTokens_oneliner_merge(strTokenList):
    output = ""
    node = strTokenList.head
    while node:
        if output:
            output += " "
        layer_counter = 0
        node_output, _ = node.oneliner_merge(layer_counter)
        output += node_output
        node = node.next
    output = re.sub('[<>]', '', output)
    output = re.sub(' ', '/', output)
    return output


def OutputStringTokens_oneliner_ex(strTokenList):
    output = ""
    node = strTokenList.head
    while node:
        if output:
            output += " "
        layer_counter = 0
        node_output, _ = node.oneliner_ex(layer_counter)
        output += node_output
        node = node.next

    # ugly resolution for SPACE format
    output = re.sub('(\(\S*?) +', r'\1  ', output)
    output = re.sub('(\[\S*?) +', r'\1   ', output)
    output = re.sub('(\{\S*?) +', r'\1    ', output)

    output = re.sub('(\S*?)(\)\)|\))', r'\1  \2', output)
    output = re.sub('(\S*?)(\]\]|\])', r'\1   \2', output)
    output = re.sub('(\S*?)(\}\}|\})', r'\1    \2', output)

    output = re.sub('\> +\<', '> <', output)
    output = re.sub('\) +\(', ')  (', output)
    output = re.sub('\] +\[', ']   [', output)
    output = re.sub('\} +\{', '}    {', output)
    return output


# #Replace % and & sign before using "GET" to query webservice.
# def URLEncoding(Sentence):
#     #Sentence = Sentence.replace("%", "%25")
#     #Sentence = Sentence.replace("&", "%26")
#     #Sentence = Sentence.replace("/", "%2F")
#     return Sentence


def IndexIn2DArray(x, array):
    for i in range(len(array)):
        for j in range(len(array[i])):
            if x == array[i][j]:
                return i, j
    return -1, -1


def LastItemIn2DArray(xlist, array):
    for i in reversed(range(len(array))):
        for j in reversed(range(len(array[i]))):
            if  array[i][j] in xlist:
                return array[i][j]
    return None


def InitDB():
    global DBCon
    try:
        DBCon = sqlite3.connect('../data/parser.db')
        #DBCon.setLockingEnabled(False);
        cur = DBCon.cursor()
        cur.execute("PRAGMA read_uncommitted = true;")
        #cur.execute("PRAGMA synchronous=OFF;")
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA TEMP_STORE=MEMORY;")  # reference: https://www.sqlite.org/wal.html
        cur.close()
        #DBCon.commit()
        logging.info("DBCon Init")
        #atexit.register(CloseDB, (DBCon,))
    except sqlite3.OperationalError:
        logging.error("Database file does not exists!")



def CloseDB(tempDB):
    try:
        tempDB.commit()
        tempDB.close()
        logging.info("DBCon closed.")
    except sqlite3.ProgrammingError:
        logging.info("DBCon is closed.")
# try:
#     if not DBCon:
#         InitDB()    #initialize this
# except NameError:
#     DBCon = None
#     InitDB()


DBCon = None
#
#tablefields and values are lists.
def DBInsertOrGetID(DBConnection, tablename, tablefields, values):
    cur = DBConnection.cursor()
    strsql = "SELECT ID from " + tablename + " where " + " AND ".join(field + "=?" for field in tablefields ) + "  limit 1"
    logging.info(strsql)
    cur.execute(strsql, values)
    resultrecord = cur.fetchone()
    if resultrecord:
        resultid = resultrecord[0]
    else:
        try:
            strsql = "INSERT into " + tablename + " (" + ",".join(tablefields) + ") VALUES(" + ",".join("?" for field in tablefields) + ")"
            logging.info(strsql)
            cur.execute(strsql, values)
            resultid = cur.lastrowid
        except (sqlite3.OperationalError,sqlite3.DatabaseError) as e:
            logging.warning("data writting error. ignore")
            logging.warning(str(e))
            resultid = -1
        DBConnection.commit()
    cur.close()
    return resultid

def DBInsertOrUpdate(DBConnection, tablename, keyfield, keyvalue, tablefields, values):
    cur = DBConnection.cursor()
    strsql = "SELECT ID from " + tablename + " where " + keyfield + "=?  limit 1"
    logging.info(strsql)
    logging.info("keyvalue:" + keyvalue)
    cur.execute(strsql, (keyvalue,))
    resultrecord = cur.fetchone()
    if resultrecord:
        resultid = resultrecord[0]
        try:
            strsql = "update  " + tablename + "set " + ",".join([ field + " = ?" for field in tablefields])  \
                    + " , verifytime=DATETIME('now') where ID=?"

            logging.info(strsql)
            cur.execute(strsql, values.extend([resultid]))
            resultid = cur.lastrowid
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logging.warning("data writting error. ignore")
            logging.warning(str(e))
            resultid = -1
        DBConnection.commit()
    else:
        try:
            strsql = "INSERT into " + tablename + " (" + ",".join(tablefields) + ", createtime) VALUES(" \
                     + ",".join("?" for _ in tablefields) + ", DATETIME('now'))"
            logging.info(strsql)
            cur.execute(strsql, values)
            resultid = cur.lastrowid
        except (sqlite3.OperationalError,sqlite3.DatabaseError) as e:
            logging.warning("data writting error. ignore")
            logging.warning(str(e))
            resultid = -1
        DBConnection.commit()
    cur.close()
    return resultid

def DBInsertOrIgnore(DBConnection, tablename, keyfield, keyvalue, tablefields, values):
    cur = DBConnection.cursor()
    strsql = "SELECT ID from " + tablename + " where " + keyfield + "=?  limit 1"
    logging.info(strsql)
    logging.info("keyvalue:" + keyvalue)
    cur.execute(strsql, (keyvalue,))
    resultrecord = cur.fetchone()
    if resultrecord:
        resultid = resultrecord[0]
    else:
        try:
            strsql = "INSERT into " + tablename + " (" + ",".join(tablefields) + ", createtime) VALUES(" \
                     + ",".join("?" for _ in tablefields) + ", DATETIME('now'))"
            cur.execute(strsql, values)
            resultid = cur.lastrowid
        except (sqlite3.OperationalError,sqlite3.DatabaseError) as e:
            logging.warning("data writting error. ignore")
            logging.warning(str(e))
            resultid = -1
        DBConnection.commit()
    cur.close()
    return resultid


def format_parenthesis(text, count):
    # get symbol by layer count
    left_p = SYM_PARENTHESIS[count%4][0] * int(count/4 + 1)
    right_p = SYM_PARENTHESIS[count%4][1] * int(count/4 + 1)
    text += right_p # add right parenthesis
    return text.replace(IMPOSSIBLESTRINGLP, left_p) # replace left symbol

def has_overlap(listA, listB):
    if len([i for i in listA if i in listB]) > 0:
        return True
    return False
