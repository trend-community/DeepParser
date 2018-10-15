#!/bin/bash
# this is to run in a server (such as 172.22.290.95) which has direct network access to other servers.
# and the current user already setup key-based (passwordless) connection with root of other servers.

rootdirectory_local=../../
temp_local=/tmp/git$USER

set -x

# if it comes with a parameter, then ignore package creation, just do the deployment.
if [ $# -eq 0 ]
then

    mkdir $temp_local
    rm -rf $temp_local/*
    cp -r $rootdirectory_local/parser $temp_local
    cp -r $rootdirectory_local/fsa   $temp_local

    cd $temp_local/fsa
    rm -rf .git
    rm -rf test
    rm -rf extra

    cd $temp_local/parser
    rm -rf .git
    rm -rf compiled/*
    rm -rf log/*
    rm -rf temp/*

    cd data
    find . ! -name 'parser*.db' -type f -exec rm -f {} +
    cd ..

    find . -name "*.pyc" -delete

    cd $temp_local
    tar --no-same-owner -zcf parser_release.tar.gz *

    echo $temp_local/parser_release.tar.gz is created.
fi
#read -p "Press [Enter] key to start deploying. Press Ctrl-C to stop."
echo "Option 1: Deploying to SV office ( should have total=10 in the gitpull_restart.sh "
echo "Option 2: Deploying to Production  ( should have total=32 in the gitpull_restart.sh "
echo "Option 3: Deploying to Production Neo4j ( should have total=4 in the gitpull_restart.sh "
echo "Option 4: Deploying to Big Memory Production  ( should have total=32 in the gitpull_restart.sh "

PS3='Please enter your choice: '
options=("Option 1" "Option 2" "Option 3" "Option 4" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Option 1")
        echo "Option 1: Deploying to SV office"
rootdirectory_remote=/nlpengine
nluuser=team

scp $temp_local/parser_release.tar.gz team@10.153.152.253:$rootdirectory_remote
ssh team@10.153.152.253 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh "
scp $temp_local/parser_release.tar.gz team@10.153.152.254:$rootdirectory_remote
ssh team@10.153.152.254 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh "
scp $temp_local/parser_release.tar.gz team@10.153.152.251:$rootdirectory_remote
ssh team@10.153.152.251 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh "
break;;

        "Option 2")
        echo "Option 2: Deploying to Production"
rootdirectory_remote=/export/App/git
nluuser=nlu

scp $temp_local/parser_release.tar.gz root@172.18.188.2:$rootdirectory_remote
ssh root@172.18.188.2 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz  && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@172.18.189.72:$rootdirectory_remote
ssh root@172.18.189.72 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz  && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@172.18.189.136:$rootdirectory_remote
ssh root@172.18.189.136 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz  && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@172.18.189.137:$rootdirectory_remote
ssh root@172.18.189.137 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@172.18.189.138:$rootdirectory_remote
ssh root@172.18.189.138 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "
break;;

        "Option 3")
        echo "Option 3: Deploying to Production neo4j servers"
rootdirectory_remote=/export/App/git
nluuser=nlu
scp $temp_local/parser_release.tar.gz root@172.18.189.135:$rootdirectory_remote
ssh root@172.18.189.135 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@172.18.189.202:$rootdirectory_remote
ssh root@172.18.189.202 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "
break;;
        "Option 4")
        echo "Option 4: Deploying to Production 1T servers"
rootdirectory_remote=/export/App/git
nluuser=nlu

scp $temp_local/parser_release.tar.gz root@11.7.151.98:$rootdirectory_remote
ssh root@11.7.151.98 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.99:$rootdirectory_remote
ssh root@11.7.151.99 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.100:$rootdirectory_remote
ssh root@11.7.151.100 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.101:$rootdirectory_remote
ssh root@11.7.151.101 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.102:$rootdirectory_remote
ssh root@11.7.151.102 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.132:$rootdirectory_remote
ssh root@11.7.151.132 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.133:$rootdirectory_remote
ssh root@11.7.151.133 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.134:$rootdirectory_remote
ssh root@11.7.151.134 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.162:$rootdirectory_remote
ssh root@11.7.151.162 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.163:$rootdirectory_remote
ssh root@11.7.151.163 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp $temp_local/parser_release.tar.gz root@11.7.151.164:$rootdirectory_remote
ssh root@11.7.151.164 " cd $rootdirectory_remote && tar xzf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "
break;;
        "Quit")
            break
            ;;
        *) echo "invalid option $REPLY";;
    esac
done