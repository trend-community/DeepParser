
mkdir 135
rsync root@172.18.189.135:/export/App/git/parser/log/*.log 135/


for f in $(find .   -name *.log)
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
