
mkdir 2 > nil 2>&1
rsync root@172.18.188.2:/export/App/git/parser/log/*.log 2/
mkdir 135 > nil 2>&1
rsync root@172.18.189.135:/export/App/git/parser/log/*.log 135/
mkdir 202 > nil 2>&1
rsync root@172.18.189.202:/export/App/git/parser/log/*.log 202/
mkdir 72 > nil 2>&1
rsync root@172.18.189.72:/export/App/git/parser/log/*.log 72/
mkdir 136 > nil 2>&1
rsync root@172.18.189.136:/export/App/git/parser/log/*.log 136/
mkdir 137 > nil 2>&1
rsync root@172.18.189.137:/export/App/git/parser/log/*.log 137/
mkdir 138 > nil 2>&1
rsync root@172.18.189.138:/export/App/git/parser/log/*.log 138/


for f in $(find .   -name "restful*.log")
do
  grep COMPLETE $f |grep -v "ab cd" | awk '{F=substr($0,1,10)".log";print >> F;close(F)}'
done

# sort and de-duplicate
# remove heart beat
for f in *.log
do
  sort -u $f   > $f.sorted.txt
  cut -d' ' -f 2 $f.sorted.txt | cut -d':' -f 1-2  > $f.time.txt
done

wc 2018-06-*.sorted.txt

for f in 2018-06-*.time.txt
do
 echo $f
 awk -F: '{a[$1]++}END{for(i in a) print i,a[i]}' $f | sort
done
