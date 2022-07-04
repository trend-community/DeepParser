# ==============================================================
# a simple server stress test program
# ==============================================================
# !/usr/bin/python2 -u
# -*- coding: utf8 -*-

timeout = 2
nThreads = 0
maxThreads = 50
completed = 0
urlprefix = "http://localhost:5001/LexicalAnalyze?Sentence="

import sys, logging
import time
import thread
import threading
import urllib
import urllib2
import codecs

lock = threading.Lock()


def get(chunk):
    global nThreads, completed
    to = timeout
    with lock:
        nThreads += 1
    chunk = '"' + chunk + '"'
    url = urlprefix + urllib.quote_plus(chunk.encode('utf8'))
    while True:
        try:
#            print url
            response = urllib2.urlopen(url, None, to*100)
            ret = response.read()
            #print ret
            completed += 1
            break
        except:
            logging.error( "to=" + str(to) + " Error:" + str(sys.exc_info()[1]))
            sys.stdout.flush()
            time.sleep(to)
            to += 1
    with lock:
        nThreads -= 1
    return


fin = codecs.open(sys.argv[1], 'rb', encoding='utf-8')
lNum = 0
for line in fin:
    line = line.strip()
    lNum += 1

    while True:
        with lock:
            exceed = (nThreads > maxThreads)
        if exceed:
            logging.error(   'completed=' + str(completed) + ' line number = ' + str(lNum) + ". " + str(nThreads))
            time.sleep(timeout) #wait for the threads to decrease nThreads
        else:
            break

    try:
        thread.start_new_thread(get, (line,))
    except:
        logging.error (  'Error:', line)
        sys.stdout.flush()

for i in range(timeout*10):
    if nThreads < 1:
        break
    time.sleep(1)
logging.warning (   'completed=' + str(completed) + ' line number = ' + str(lNum) + ". " + str(nThreads))

