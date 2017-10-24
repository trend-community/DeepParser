#!/usr/bin/python -u

#==============================================================
# isNonHanzi()
#==============================================================
def isNonHanzi(s): return all( (ord(c) < 0x4e00 or ord(c) > 0x9fff) for c in s)

#==============================================================
# command line
#==============================================================
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("input", help="input query unigram file")
parser.add_argument("output", help="output phrase unigram text file")
parser.add_argument("dict", help="output phrase unigram pickle dict")
args = parser.parse_args()
print (str(args))

#==============================================================
# normalize queries by taking space delimited chunks as phrases
# and by adding spaces in between 'words'
# Here a 'word' is defined as English word or single Chinese character
#
# The most useful output is the pickle'd dictionary of phrases 
# with accumulated frequencies.
#==============================================================
import pickle
import codecs
fin = codecs.open(args.input, 'rb', encoding='utf-8')

from viterbi1 import *

N = 0
for line in fin:
	line = line.strip()
	# print line.encode('utf8')
	try:
		[query, freqstring] = line.split("", 2)
		freq = int(freqstring)
		for chunk in query.split():
			phrase = normalize(chunk)
			querydict[phrase] = querydict.get(phrase, 0) + freq
			N = N + freq
	except:
		print("error in processing \n\t" + line)
		continue
fin.close()

querydict[''] = N
pickle.dump( querydict, open(args.dict, "wb") )

fout = codecs.open(args.output, 'wb', encoding='utf-8')
for phrase in querydict: fout.write(phrase + '\t' + str(querydict[phrase]) + '\n')
fout.close()
