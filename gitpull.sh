#!/usr/bin/env bash  
#echo "$(dirname "$0")"
cd "$(dirname "$0")/.."

cd fsa
git checkout X/summaryLex.txt
rm X/AllLexicon_Extra.txt
#git checkout X/AllLexicon_Extra.txt   #removed from repository.
git checkout X/SegmentSlash.txt
git checkout X/defPlus.txt
git fetch
git pull
 git log --pretty=format:'%h' -n 1 > ../parser/revision.txt 
cd X
bash SegmentSlash.sh
cd ..

cd ../parser
#git checkout .
git stash
git pull
git stash apply

python3 -m compileall -b src
#find . -name "*.py" -delete
# echo -n " " >> revision.txt
echo " \c" >> revision.txt
 git log --pretty=format:'%h' -n 1 >> revision.txt
 echo "" >> revision.txt
 date >> revision.txt


# Check if file older
if test `find "../parser/data/parser.empty.db" -mmin +1440`
	then
   exit
fi
echo "File parser.empty.db is recently modified in last day"

cd ../parser/data

rm parser.db*
cp parser.empty.db parser.db

