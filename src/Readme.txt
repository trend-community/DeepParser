#Folder location: git/parser/src
#Author: Ben Lin tianbing.lin@jd.com
#Date: 20170928

Note 1: This project is running with Python 3.x. If your default python is 2.x, you need to use "python3" to replace the "python" in the following commands, and use "pip3" to replace the "pip" in the following commands.
Note 2: By default the web services are only open for local access.

Feel free to use virtenv or anaconda python, if you know what you are doing.


0, Prerequists:
System:
    java/maven, python 3.
Folder structure:
	create an empty folder. For example "git".
	
	cd git
	git clone http://git.jd.com/ynlp/fsa 
	git clone http://git.jd.com/ynlp/multisegmental 
	git clone http://git.jd.com/ynlp/parser 

    The fsa folder should be in
        git/fsa
    while this Readme.txt should be in
        git/parser/src
    and the MultiSegmental Java program should be in
        git/multisegmental/src
Environment:
	To support Chinese/Unicode better, set environment variable PYTHONIOENCODING=utf-8


1, Initial install:
cd git/parser/src
pip install -r requirements.txt
cd git/multisegmental
mvn package


2, Background service:
2.1, Run the MultiSegmental Java program as web service
    cd git/multisegmental
    mvn exec:java &
		To use part other than 8080, use command as:
		 mvn exec:java -Dserver.port=9000
		and change parser/src/config.ini accordingly.

2.2, select either 2.2.1 or 2.2.2 to run the web service:
2.2.1, Run the python program as web service 
    cd git/parser/src
    python RestfulService.py
If you modify the lexicon or rule files and you want to reload them to see how they perform, you need to press Ctrl-C to stop this process, and run the same command again.

2.2.2, Run the python program as web service in Apache:
	2.2.2.1, Prerequists: Apache httpd service.
	2.2.2.2, Copy parser.conf into /etc/apache2/sites-enabled/parser.conf
	2.2.2.3, Edit /etc/apache2/sites-enabled/parser.conf to give a user account/group for the application (line 9). It is highly suggested not to use "root".
	2.2.2.3, Copy RestfulService.wsgi into /var/www/html/RestfulService.wsgi
	2.2.2.4, Edit /var/www/html/RestfulService.wsgi, modify "sys.path.insert(0, '/nlpengine/parser/src')" to correct path.
	2.2.2.5, Set the correct permission: at least allow that user account to read all files; write access in several folders:
				parser/temp, parser/compiled, fsa/X
	2.2.2.6, Restart apache service: 
				sudo service apache2 restart
				

3, LexicalAnalyze without program:
In your browser visit
    http://localhost:8080/Tokenize?Sentence=中文切词分析句子
    http://localhost:5001/LexicalAnalyze?Sentence='中文切词分析句子'
    http://localhost:5001/LexicalAnalyze?Type=json&Sentence='中文切词分析句子'
    http://localhost:5001/LexicalAnalyze?Type=simple&Sentence='中文切词分析句子'
    http://localhost:5001/LexicalAnalyze?Type=parsetree&Sentence='中文切词分析句子'

	The first link is a simple segmental program to confirm that part works, not meaningful.
	The second and third link are the same, output JSON format.
	The forth link is for simple format.
	The fifth link is the parse tree presentation.
	

4, Running the LexicalAnalyze program
4.1 Prepare the source file, such as "test.txt". It is suggested to place this file in a separate folder, such as git/parser/temp folder

4.2 in current git/parser/src folder, execute:
	python LexicalAnalyze_RestfulService.py  ../temp/test.txt 
Note: The error message and standard output are showing in the screen. If you want them to be in separate files, please execute:
    python LexicalAnalyze_RestfulService.py  ../temp/test.txt  >../temp/output.txt 2>../temp/error.txt

4.3 Run the program locally (Still require support from the web service of MultiSegmental Java Program in port 8080)
    python LexicalAnalyze.py ../temp/test.txt  >../temp/output.txt 2>../temp/error.txt



Extra:
crontab for server:


@reboot cd /nlpengine/multisegmental && mvn exec:java >> /nlpengine/multisegmental/log/restfulservice.log 2>&1

@reboot cd /nlpengine/parser/src && python RestfulService.pyc >> /nlpengine/parser/log/restfulservice.log  2>&1

*/2  *   *   *   *   flock -n /tmp/nlpengine_processfile.lock -c 'cd /nlpengine && sh gitpull.sh && cd /nlpengine/parser/src && sh ProcessFolder.sh '

