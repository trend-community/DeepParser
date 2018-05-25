#!/bin/bash
# this is to run in the remote servers. executing as root.
# it is called as:  sh root@xxx ' su -m $nluuser  -c "cd $rootdirectory/parser/src && bash Deploy_remote.sh"'


cd ../../
tar xzvf parser_release.tar.gz

cd parser
nohup ./gitpull_restart.sh restartonly  >> log/restart.log 2>&1 &





