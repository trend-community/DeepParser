#!/usr/bin/env bash  
# if it comes with a parameter, then ignore gitpull, just do the restart.
if [ $# -eq 0 ]
then
#use the gitpull.sh for normal process.
    bash gitpull.sh
fi

# 1.stop  parser service
#echo '-------------------'
#echo 'stop parser'
# mac centos
#pid=`ps aux | grep ' RestfulService.py' | grep -v grep | awk {'print $2'}`
#if [[ ! -z $pid ]];then
#    kill -9 $pid
#fi
#ubuntu
#kill -9 $(ps aux | grep ' RestfulService.py' | grep -v grep | awk {'print $2'})


# 2.restart  parser
cd log
newlog=`date +"%Y%m%dT%H%M"`
#tar czf    log_$newlog.tar.gz *.log	#for future. not easy to search text.
mkdir log_$newlog
mv *.log log_$newlog

cd ../src
total=10
for ((i=5001; i<5001+$total; i++)); do
    echo starting $i of $total ...

    nohup python3 RestfulService.py --port $i >> ../log/restfulservice.$i.log 2>&1 &
    sleep 100s
done

echo 'RestfulService is restarted.'
