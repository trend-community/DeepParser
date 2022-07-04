
#make web service from viterbi1 (g1.sent.py)
import logging
from flask import Flask, request
from viterbi1 import *
app = Flask(__name__)

@app.route("/QuerySegment/<sentence>")
def QuerySegment(sentence):
	norm = normalize(sentence)
	return ''.join(viterbi1(norm, len(norm)))

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

	init()
	port = 5003
	print("Running in port " + str(port))
	print(QuerySegment(normalize("鼠标和苹果手机")))
	app.run(host="0.0.0.0", port=port, debug=False)	
	