#Folder location: git/parser/src
#Author: Ben Lin tianbing.lin@jd.com
#Date: 20170928

Note 1: This project is running with Python 3.x. If your default python is 2.x, you need to use "python3" to replace the "python" in the following commands, and use "pip3" to replace the "pip" in the following commands.

Feel free to use virtenv or anaconda python.

0, Prerequists:
python 3.
Folder structure: the fsa folder should be in
	git/fsa
while this Readme.txt should be in
	git/parser/src
and the MultiSegmental Java program should be in 
	git/multisegmental/src


1, Initial install:
pip install -r requirements.txt

2, Backgroun service:
2.1, Run the MultiSegmental Java program as web service

2.2, Run the python program as web service 
 	this step is for running SentenceTest_RestfulService.py. The advantage is that you don't need to load lexicon/rules each time.

3, Running the program
3.1 Prepare the source file, such as "test.txt". It is suggested to place this file in another folder, such as git/parser/temp folder
3.2 in current git/parser/src folder, execute:
	python SentenceTest_RestfulService.py ../temp/test.txt
