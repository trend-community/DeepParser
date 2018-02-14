#!/usr/bin/env bash  

cd ~/git

cd fsa
#git checkout X/summaryLex.txt
git pull
 git log --pretty=format:'%h' -n 1 > ../parser/revision.txt 
cd X
sh SegmentSlash.sh
cd ..

#cd ../multisegmental
#git checkout .
#git pull
#mvn package
#find . -name "*.java" -delete


cd ../parser
#git checkout .
git pull
python3 -m compileall -b src
#find . -name "*.py" -delete
 echo -n " " >> revision.txt
 git log --pretty=format:'%h' -n 1 >> revision.txt
 echo "" >> revision.txt
 date >> revision.txt

