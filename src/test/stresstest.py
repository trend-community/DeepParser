# ==============================================================
# a simple server stress test program
# ==============================================================
# !/usr/bin/python2 -u
# -*- coding: utf8 -*-

timeout = 1
nThreads = 0
maxThreads = 80
completed = 0
urlprefix = "http://10.15.252.3:5001/LexicalAnalyze?Sentence="

import sys
import time
import thread
import threading
import urllib
import urllib2
import codecs

lock = threading.Lock()


def get(chunk):
    global nThreads, completed
    with lock:
        nThreads += 1
    chunk = '"' + chunk + '"'
    url = urlprefix + urllib.quote_plus(chunk.encode('utf8'))
    while True:
        try:
            response = urllib2.urlopen(url, None, timeout*10)
            ret = response.read()
#            print ret
            completed += 1
            break
        except:
            print    sys.exc_info()[1]
            sys.stdout.flush()
            time.sleep(timeout)
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
            print   'completed=', completed, ' line number = ', lNum, nThreads
            time.sleep(timeout) #wait for the threads to decrease nThreads
        else:
            break

    try:
        thread.start_new_thread(get, (line,))
    except:
        print   'Error:', line
        sys.stdout.flush()

time.sleep(10)
print   'completed=', completed, ' line number = ', lNum, nThreads

