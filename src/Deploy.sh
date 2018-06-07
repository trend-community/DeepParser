#!/bin/bash
# this is to run in a server (such as 172.22.290.95) which has direct network access to other servers.
# and the current user already setup key-based (passwordless) connection with root of other servers.

rootdirectory_local=~/git
rootdirectory_remote=/export/App/git
nluuser=nlu

set -x

# if it comes with a parameter, then ignore package creation, just do the deployment.
if [ $# -eq 0 ]
then

    mkdir /tmp/git
    rm -rf /tmp/git/*
    cp -r $rootdirectory_local/parser /tmp/git
    cp -r $rootdirectory_local/fsa   /tmp/git

    cd /tmp/git/fsa
    rm -rf .git
    rm -rf test
    rm -rf extra

    cd /tmp/git/parser
    rm -rf .git
    rm -rf compiled/*
    rm -rf log/*
    rm -rf temp/*

    find . -name "*.pyc" -delete

    cd /tmp/git
    tar --no-same-owner -zcvf parser_release.tar.gz *

    echo /tmp/git/parser_release.tar.gz is created.
fi
read -p "Press [Enter] key to start deploying. Press Ctrl-C to stop."

#for testing in dev.
#scp /tmp/git/parser_release.tar.gz root@172.22.190.95:$rootdirectory_remote
#ssh root@172.22.190.95 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

#for parsers without neo4j

scp /tmp/git/parser_release.tar.gz root@172.18.188.2:$rootdirectory_remote
ssh root@172.18.188.2 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp /tmp/git/parser_release.tar.gz root@172.18.189.72:$rootdirectory_remote
ssh root@172.18.189.72 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp /tmp/git/parser_release.tar.gz root@172.18.189.136:$rootdirectory_remote
ssh root@172.18.189.136 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp /tmp/git/parser_release.tar.gz root@172.18.189.137:$rootdirectory_remote
ssh root@172.18.189.137 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

scp /tmp/git/parser_release.tar.gz root@172.18.189.138:$rootdirectory_remote
ssh root@172.18.189.138 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

# for parses WITH neo4j
#scp /tmp/git/parser_release.tar.gz root@172.18.189.135:$rootdirectory_remote
#ssh root@172.18.189.135 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "

#scp /tmp/git/parser_release.tar.gz root@172.18.189.202:$rootdirectory_remote
#ssh root@172.18.189.202 " cd $rootdirectory_remote && tar xzvf parser_release.tar.gz && chown -R $nluuser . && su -m $nluuser  -c ' cd $rootdirectory_remote/parser/src && bash Deploy_remote.sh' "
