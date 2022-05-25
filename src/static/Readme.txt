#Folder location: git/parser/src
#Author: Ben Lin BEN@FADSHOP.NET
#Date: 20170928

#Major update on 20180309:
# Remove the usage of multisegmental project, and apache website hosting.
#Major update on 20180810:
# Add graph operation

Note 1: This project is running with Python 3.x. If your default python is 2.x, you need to use "python3" to replace the "python" in the following commands, and use "pip3" (or "python3 -m pip") to replace the "pip" in the following commands.
Note 2: Feel free to use virtenv or anaconda python, if you know what you are doing.


0, Prerequists:
System:
     python 3.
Folder structure:
	create an empty folder. For example "git".

	cd git
	git clone https://gitlab.com/BenLin0/deepparser
	git clone https://github.com/BenLin0/fsa


Environment:
	To support Chinese/Unicode better, set environment variable PYTHONIOENCODING=utf-8


1, Initial install:
cd git/cyclonenlp1/parser/src
pip install -r requirements.txt
copy the appropriate .ini file as config.ini (depend on different project)

cd git/parser/data
cp parser.empty.db parser.db


2, Background Restful Service:
2.1, Run the python program as web service :
    cd git/cyclonenlp1/parser/src
    python RestfulService.py
    Note 0: Use "nohup" or other method to run it in background for 24/7 use.
    Note 1: The default port number is 5001. It can be modified by changing the value in config.ini [website][port] section.
2.2, To run the python program in Flask framework:
    cd git/cyclonenlp1/parser/src
    python flaskapp.py
    Note: The default port number is 5000. Not configurable through config.ini
2.3, To run it in gunicorn framework with multi process:
    sudo pip install gunicorn3
    cd git/cyclonenlp1/parser/src
    gunicorn3 flaskapp:app
    (or gunicorn3 –workers=4 flaskapp:app to specify 4 processes)
    Note: The default port number is 8000. Not configurable through config.ini

3, LexicalAnalyze without program:
	In your browser visit  http://localhost:5001, it will give you a WebUI to input sentence to analyze.

3.1, Below is list of all Restful APIs:
	/GetFeatureID/CL		# return the feature id of "CL"
	/GetFeatureName/23		# return the feature name of id 23
	/LexicalAnalyze:
		Key: Required. Authorization key. Please contact NLU team for this key.

		Sentence: Required. The sentence to process. Quoted in single quotes.

		type: [json (default), segmentation, simple, simpleEx, graph, graphjson, pnorm, simplegraph, parsetree]
			json: current default output.
			segmentation: segmentation format "中文/分词/方法"
                        keyword: segmentation format, only show words with "keyWord" feature.
			simple/simpleEx: simple presentation of the json format.
			graph: DOT format of graph
                        graphjson: JSON format of graph
			simpleggraph: simple presentation of the graph format "M{分词->中文}; M{方法->分词}; "
			parsetree: for web presentation only, not to use as API.
			pnorm: only show the pnorm keywords.

		schema: [full (default), segonly, shallowcomplete]
			full: default. Run the whole deep-parsing pipeline.
			segonly: stop running pipeline after the lexical analysis.
			shallowcomplete: stop running pipeline after shallow parsing.

		action: [none (default), headdown]
			none: default. no extra action to apply.
			headdown: Subj/Obj/Pred is propagated from upper node to head leaf node.

		Debug: when Type is parsetree and Debug is true, show some extra debug information.
		ResetGlobalValue: if it is "true", then reset the Global Variables.
		DocumentClass, ParagraphClass, SentenceClass: Apply the values for analysis if given.

	/DocumentAnalyze  Call method: post
	    Key: Required. Authorization key. Please contact NLU team for this key.
		type: [parsetree (default), pnorm, graphjson]
			parsetree: for web presentation only, not to use as API.
			graphjson: JSON format of graph
			pnorm: only show the pnorm keywords.
		schema: [full (default), segonly, shallowcomplete]
			full: default. Run the whole deep-parsing pipeline.
			segonly: stop running pipeline after the lexical analysis.
			shallowcomplete: stop running pipeline after shallow parsing.
		Debug: when Type is parsetree and Debug is true, show some extra debug information.
		ResetGlobalValue: if it is "true", then reset the Global Variables.
		DocumentClass, ParagraphClass, SentenceClass: Apply the values for analysis if given.
		Document: The document to analyze.


4, Running the standalone LexicalAnalyze program
4.1 Prepare the source file, such as "test.txt".

4.2 in current git/parser/src folder, execute:
	python LexicalAnalyze_RestfulService.py  test.txt
Note: The error message and standard output are showing in the screen. If you want them to be in separate files, please execute:
    python LexicalAnalyze_RestfulService.py  test.txt  >../temp/output.txt 2>../temp/error.txt

4.3 Run the program locally, without support of background service:
    python LexicalAnalyze.py ../temp/test.txt  >../temp/output.txt 2>../temp/error.txt


5, Extra:
crontab for server:

#Start the background Restful Service after each reboot:
@reboot cd /nlpengine/parser/src && python RestfulService.pyc >> /nlpengine/parser/log/restfulservice.log  2>&1

#execute LexicalAnalyze.py for all files in the fsa/test/input/ folder every 2 hours:
*/2  *   *   *   *   flock -n /tmp/nlpengine_processfile.lock -c 'cd /nlpengine/parser && sh gitpull.sh && cd /nlpengine/parser/src && sh ProcessFolder.sh '

