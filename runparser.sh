#!/usr/bin/env bash  
#set -x

if [ $# -eq 0 ]
then
	language="X"
else
	language=$1
fi

if  [ $language = 'Y' ]; then
    port=6001
elif [ $language = 'E' ]; then
    port=6002
elif [ $language = 'F' ]; then
    port=6003
else
    port=5001
fi 


cd ~/git/parser/src 
rm config.ini 
cp "config.$language.ini" config.ini 
python3 RestfulService.py --port $port 2>&1 | grep -E --color "WARNING|ERROR|Errno| "  

