#!/bin/bash
# contact: tianbing.lin@jd.com

echo "start extracting."
for a in `ls -1 *.tar.gz`;  do mkdir $a.folder; gzip -dc $a | tar  xf  - -C $a.folder; done

mkdir backup
mv *.tar.gz backup

echo "start separating and merging files according to timestamp."
for f in $(find .   -name "info*.log" -o -name "catalina.out")
do
   echo "   merging $f "
  grep INFO $f | awk '{F=substr($0,1,10)".log";print >> F;close(F)}'
done

rm -rf *.folder

# sort and de-duplicate
echo "start sorting, de-duplicating, and getQEResponse."
for f in *.log
do
  echo "    processing $f"
  sort -u $f   > $f.sorted.txt
  grep getQEResponse $f.sorted.txt > $f.getQEResponse.txt
  cut -d' ' -f 3 $f.getQEResponse.txt | cut -d':' -f 1-2  > $f.time.txt
done

wc 2018-06-*.getQEResponse.txt

for f in 2018-06-*.time.txt
do
 echo $f
 awk -F: '{a[$1]++}END{for(i in a) print i,a[i]}' $f | sort
done
