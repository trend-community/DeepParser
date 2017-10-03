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
    The fsa folder should be in
        git/fsa
    while this Readme.txt should be in
        git/parser/src
    and the MultiSegmental Java program should be in
        git/multisegmental/src
Environment:
	To support Chinese/Unicode better, set environment variable PYTHONIOENCODING=utf-8


1, Initial install:
pip install -r requirements.txt


2, Background service:
2.1, Run the MultiSegmental Java program as web service
    cd git/multisegmental
    mvn exec:java

2.2, Run the python program as web service 
    cd git/parser/src
    python RestfulService.py
If you modify the lexicon or rule files and you want to reload them to see how they perform, you need to press Ctrl-C to stop this process, and run the same command again.


3, MultiLevelSegment without program:
In your browser visit
    http://localhost:8080/Tokenize/?Sentence=中文切词分析句子
    http://localhost:5001/Tokenize/中文切词分析句子
    http://localhost:5001/MultiLevelSegmentation/中文切词分析句子


4, Running the MultiLevelSegment program
4.1 Prepare the source file, such as "test.txt". It is suggested to place this file in a separate folder, such as git/parser/temp folder

4.2 in current git/parser/src folder, execute:
	python MultiLevelSegment_RestfulService.py [NoFeature] ../temp/test.txt
Note: The error message and standard output are showing in the screen. If you want them to be in separate files, please execute:
    python MultiLevelSegment_RestfulService.py [NoFeature] ../temp/test.txt >../temp/output.txt 2>../temp/error.txt

4.3 Run the program locally (Still require support froom the web service of MultiSegmental Java Program in port 8080)
    python MultiLevelSegment.py ../temp/test.txt [NoFeature] >../temp/output.txt 2>../temp/error.txt


5, Running the ProcessSentence program
The ProcessSentence program apply all rule files, after MultiLevelSegment.
The rules keep changing, you can modify the list in LoadCommon() of "ProcessSentence.py".
Replace "MultiLevelSegment" with "ProcessSentence" for the commands in Section 4, you now have all commands you need to process test sentences.
