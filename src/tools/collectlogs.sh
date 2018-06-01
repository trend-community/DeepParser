
mkdir 135
rsync root@172.18.189.135:/export/App/git/parser/log/*.log 135/


for f in $(find . -maxdepth 1 -name *.log)
do
  awk '{F=substr($0,1,10)".txt";print >> F;close(F)}' $f
done

# sort and de-duplicate
# remove heart beat
for f in *.txt
do
  sort -u $f | grep -v "ab cd" | > $f.sorted.txt
  cut -d' ' -f 2 $f.sorted.txt | cut -d':' -f 1-2  > $f.time.txt
done
