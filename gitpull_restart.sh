#!/usr/bin/env bash  
#echo "$(dirname "$0")"
cd "$(dirname "$0")/.."

cd fsa
git checkout X/summaryLex.txt
rm X/AllLexicon_Extra.txt
git checkout X/AllLexicon_Extra.txt
git checkout X/SegmentSlash.txt
git fetch
git pull
 git log --pretty=format:'%h' -n 1 > ../parser/revision.txt 
cd X
sh SegmentSlash.sh

cd ../../parser


git pull
python3 -m compileall -b src
#find . -name "*.py" -delete
# echo -n " " >> revision.txt
echo " \c" >> revision.txt
 git log --pretty=format:'%h' -n 1 >> revision.txt
 echo "" >> revision.txt
 date >> revision.txt

#cd ../parser/data
#cp parser.empty.db parser.db
#cd ..

# 1.stop  parser service
echo '-------------------'
echo 'stop parser'
pid=`ps aux | grep 'python3 RestfulService.py' | grep -v grep | awk {'print $2'}`
if [[ ! -z $pid ]];then
    kill -9 $pid
fi

# 2.restart  parser
mkdir log
cd src

nohup python3 RestfulService.py > ../log/restfulservice.log 2>&1 &
echo 'RestfulService is restarted.'
