#!/bin/bash
# loop through a folder to do MultiLevelSegment.py

#exit 0 # comment this line if not to run it.


INPUTFILES="../../fsa/test/input/*.txt"
OUTPUTFOLDER="../../fsa/test/output"
FEATUREFILE="_feature.txt"


current_time=$(date "+%Y.%m.%d-%H.%M.%S")
TEMPFOLDER=$OUTPUTFOLDER/$current_time
mkdir $TEMPFOLDER
echo $current_time >> ../log/ProcessFolder.sh.log

wget http://localhost:8080/Reload > /tmp/reload.html

python SentenceTest.pyc > "$TEMPFOLDER/SentenceTest.txt" 2>> ../log/ProcessFolder.log &

for f in $INPUTFILES
do
    echo "Processing $f file..."
    filename=$(basename "$f")
    outputfile="$TEMPFOLDER/$filename"
    nice -18 python LexicalAnalyze.pyc "$f" NoFeature > "$outputfile" 2>> "../log/ProcessFolder_$filename.log" &
done


for f in $INPUTFILES
do
    echo "Processing $f file..."
    filename=$(basename "$f")
    outputfile="$TEMPFOLDER/$filename"
    nice -19 python LexicalAnalyze_Restfulservice.pyc "$f"  > "$outputfile$FEATUREFILE" 2>> "../log/ProcessFolder_feature_$filename.log" &
done



wait        #wait for all child process to complete.

end_time=$(date "+%Y.%m.%d-%H.%M.%S")
echo "$current_time - end at: $end_time " >> ../log/ProcessFolder.sh.log

#
cp $TEMPFOLDER/* $OUTPUTFOLDER
#rmdir $TEMPFOLDER

#remove folder that is 1 week old
find $OUTPUTFOLDER/* -type d -mtime +7 -exec rm -rf {} \;


end_time=$(date "+%Y.%m.%d-%H.%M.%S")
echo "$current_time - end at: $end_time " >> ../log/ProcessFolder.sh.log
