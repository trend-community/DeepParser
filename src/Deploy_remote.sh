
#!/bin/bash
# this is to run in the remote servers. executing as root.
# it is called as:  sh root@xxx ' su -m $nluuser  -c "cd $rootdirectory/parser/src && bash Deploy_remote.sh"'

source /home/nlu/.bashrc

cd ../../
tar xzvf parser_release.tar.gz

cd parser
kill -9 $(ps aux | grep 'gitpull_restart.sh' | grep -v grep | awk {'print $2'})

nohup ./gitpull_restart.sh restartonly  >> log/restart.log 2>&1 &





