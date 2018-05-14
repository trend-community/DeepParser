#!/usr/bin/env bash  
#echo "$(dirname "$0")"
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
mv log log.$(date +"%Y%m%dT%H%M")
mkdir log
cd src
for ((i=5001; i<=5004; i++)); do
    nohup python3 RestfulService.py --port $i >> ../log/restfulservice.$i.log 2>&1 &
done

echo 'RestfulService is restarted.'
