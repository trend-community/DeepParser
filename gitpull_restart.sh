#!/usr/bin/env bash  
#use the gitpull.sh for normal process.
bash gitpull.sh


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
cd log
newlog=`date +"%Y%m%dT%H%M"`
mkdir log_$newlog
mv *.txt log_$newlog
mv ../log_* log

cd ../src
total=10
for ((i=5001; i<5001+$total; i++)); do
    echo starting $i of $total ...
    nohup python3 RestfulService.py --port $i >> ../log/restfulservice.$i.log 2>&1 &
    sleep 10s
done

echo 'RestfulService is restarted.'
