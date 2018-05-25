#!/bin/bash
# this is to run in a server (such as 172.22.290.95) which has direct network access to other servers.
# and the current user already setup key-based (passwordless) connection with root of other servers.

rootdirectory=/export/App/git
nluuser=nlu

set -x

# if it comes with a parameter, then ignore package creation, just do the deployment.
if [$# -eq 0]
then

    mkdir /tmp/git
    rm -rf /tmp/git/*
    cp -r $rootdirectory/parser /tmp/git
    cp -r $rootdirectory/fsa   /tmp/git

    cd /tmp/git/fsa
    rm -rf .git
    rm -rf test

    cd /tmp/git/parser
    rm -rf compiled/*
    rm -rf log/*
    rm -rf temp/*

    cd /tmp/git
    tar --no-same-owner -zcvf parser_release.tar.gz *

    echo /tmp/git/parser_release.tar.gz is created.
fi
read -p "Press [Enter] key to start deploying. Press Ctrl-C to stop."


scp /tmp/git/parser_release.tar.gz root@172.18.189.72:$rootdirectory
sh root@172.18.189.72 ' su -m $nluuser  -c "chown $nluuser $rootdirectory/parser_release.tar.gz && cd $rootdirectory/parser/src && bash Deploy_remote.sh"'


