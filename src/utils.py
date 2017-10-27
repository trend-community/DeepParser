import logging, re, json

url = "http://localhost:5001"
url_ch = "http://localhost:8080"


# return -1 if failed. Should throw error?
def _SearchPair_old(string, tagpair):
    depth = 0
    i = 0
    currentTagIndex = 0
    targetTagIndex = 1

    while 0<=i<len(string):
        if string[i] == tagpair[targetTagIndex]:
            depth -= 1
            if depth == -1: # found!
                return i
        if string[i] == tagpair[currentTagIndex]:
            depth += 1
        i += 1
    logging.error(" Can't find a pair tag " + tagpair[0] + " in:" + string)
    raise RuntimeError(" Can't find a pair tag!" + string)
    #return -1

from functools import lru_cache
# return -1 if failed. Should throw error?
@lru_cache(1000000)
def SearchPair(string, tagpair, Reverse=False):
    depth = 0
    if Reverse:
        i = len(string)-1
        currentTagIndex = 1
        targetTagIndex = 0
        direction = -1
    else:
        i = 0
        currentTagIndex = 0
        targetTagIndex = 1
        direction = 1
    while 0<=i<len(string):
        if string[i] == tagpair[targetTagIndex]:
            depth -= 1
            if depth == -1: # found!
                return i
        if string[i] == tagpair[currentTagIndex]:
            depth += 1
        i += direction
    logging.error(" Can't find a pair tag " + tagpair[0] + " in:" + string)
    raise RuntimeError(" Can't find a pair tag!" + string)
    #return -1


def _SeparateComment(line):
    line = line.strip()
    SlashLocation = line.find("//")
    if SlashLocation < 0:
        return line, ""
    else:
        return line[:SlashLocation].strip(), line[SlashLocation+2:].strip()

def SeparateComment(multiline):
    blocks = [x.strip() for x in re.split("\n", multiline) ]
    content = ""
    comment = ""
    for block in blocks:
        _content, _comment = _SeparateComment(block)
        if _content:
            content += "\n" + _content
        if _comment:
            comment += " //" + _comment
    return content.strip(), comment.strip()


#Can be expand for more scenario.
# unicode numbers (or English "one", "two"...) should be in lexicon to have "CD" feature.
#       so not to be included in here.
def IsCD(word):
    try:
        _ = float(word)
        return True
    except ValueError:
        return False


def IsAscii(Sentence):
    if isinstance(Sentence, list):
        Sentence = "".join(Sentence)
    try:
        Sentence.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True


def RemoveExcessiveSpace(Content):
    #Remove any whitespace around | sign, so it ismade as a word.
    r = re.compile("\s*\|\s*", re.MULTILINE)
    Content = r.sub("|", Content)

    r = re.compile("<\s*", re.MULTILINE)
    Content = r.sub("<", Content)

    r = re.compile("\s*>", re.MULTILINE)
    Content = r.sub(">", Content)

    Content = Content.strip(";")

    return Content



SignsToIgnore = "{};"
Pairs = ['[]', '()', '""', '\'\'', '//']

# The previous step already search up to the close tag.
#   Now the task is to search after the close tag up the the end of this token,
#   close at a space, or starting of next token.
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
def GetPrefix(Name):
    match = re.findall("(.*?)_\d", Name)
    if match:
        return match[0]
    else:
        return Name


def OutputStringTokens_json(strTokens):
    from collections import OrderedDict
    output = json.dumps(OrderedDict([{'word': token.stem, 'feature': token.GetFeatures()} for token in strTokens if token.stem]), sort_keys=False, ensure_ascii=False)

    return output


def OutputStringTokens_oneliner(strTokens, NoFeature=False):
    output = ""
    for token in strTokens:
        if token.Gone:
            continue
        if not token.stem:
            continue
        if output:
            output += "/"

        for _ in range(token.StartTrunk):
            output += "<"
        if NoFeature:
            output += token.stem
        else:
            output += token.oneliner()
        for _ in range(token.EndTrunk):
            output += ">"
    return output


#Replace % and & sign before using "GET" to query webservice.
def URLEncoding(Sentence):
    #Sentence = Sentence.replace("%", "%25")
    #Sentence = Sentence.replace("&", "%26")
    #Sentence = Sentence.replace("/", "%2F")
    return Sentence
