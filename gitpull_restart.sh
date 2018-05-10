#!/usr/bin/env bash  
#echo "$(dirname "$0")"
cd "$(dirname "$0")/.."

cd fsa
git checkout X/summaryLex.txt
#rm X/AllLexicon_Extra.txt
#git checkout X/AllLexicon_Extra.txt
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
# mac centos
pid=`ps aux | grep 'python3 RestfulService.py' | grep -v grep | awk {'print $2'}`
if [[ ! -z $pid ]];then
    kill -9 $pid
fi
#ubuntu
kill -9 $(ps aux | grep 'python3 RestfulService.py' | grep -v grep | awk {'print $2'})


# 2.restart  parser
mkdir log
cd src
mv ../log/restfulservice.log "../log/restfulservice.$(date +"%Y%m%dT%H%M").log"
for ((i=5001; i<=5016; i++)); do
    nohup python3 RestfulService.py --port $i >> ../log/restfulservice.$i.log 2>&1 &
done

echo 'RestfulService is restarted.'
