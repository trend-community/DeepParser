#!/bin/bash

cd fsa
git checkout X/summaryLex.txt
git pull


cd ../multisegmental
#git checkout .
git pull
mvn package
#find . -name "*.java" -delete


cd ../parser
#git checkout .
git pull
python3 -m compileall -b src
#find . -name "*.py" -delete


