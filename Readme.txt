#Folder location: git/parser/src
#Author: Ben Lin tianbing.lin@jd.com
#Date: 20170928

#Major update on 20180309:
# Remove the usage of multisegmental project, and apache website hosting.


Note 1: This project is running with Python 3.x. If your default python is 2.x, you need to use "python3" to replace the "python" in the following commands, and use "pip3" to replace the "pip" in the following commands.
Note 2: Feel free to use virtenv or anaconda python, if you know what you are doing.


0, Prerequists:
System:
     python 3.
Folder structure:
	create an empty folder. For example "git".
	
	cd git
	git clone http://git.jd.com/ynlp/fsa 
	git clone http://git.jd.com/ynlp/parser 

    The fsa folder should be in
        git/fsa
    while this Readme.txt should be in
        git/parser/src
Environment:
	To support Chinese/Unicode better, set environment variable PYTHONIOENCODING=utf-8


1, Initial install:
cd git/parser/src
pip install -r requirements.txt

cd git/parser/data
cp parser.empty.db parser.db

2, Background Restful Service:
2.1, Run the python program as web service :
    cd git/parser/src
    python RestfulService.py
    Note 0: Use "nohup" or other method to run it in background for 24/7 use.
    Note 1: The default port number is 5001. It can be modified by changing the value in config.ini [website][port] section.
	Note 2: If you modify the lexicon or rule files and you want to reload them to see how they perform, you need to press Ctrl-C to stop this process, and run the same command again.
		

3, LexicalAnalyze without program:
In your browser visit
    http://localhost:5001/LexicalAnalyze?Sentence='中文切词分析句子'
    http://localhost:5001/LexicalAnalyze?Type=json&Sentence='中文切词分析句子'
    http://localhost:5001/LexicalAnalyze?Type=simple&Sentence='中文切词分析句子'
    http://localhost:5001/LexicalAnalyze?Type=parsetree&Sentence='中文切词分析句子'

	The first and second link are the same, output JSON format.
	The third link is for simple segmentation format.
	The forth link is the parse tree presentation.
	
3.1, Below is list of all Restful APIs:
	/GetFeatureID/CL		# return the feature id of "CL"
	/GetFeatureName/23		# return the feature name of id 23
	/LexicalAnalyze: Type: [json (default), simple, parsetree]
					Debug: when Type is parsetree and Debug is true, show some debug information.
	

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

