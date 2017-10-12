#!/bin/bash
# loop through a folder to do MultiLevelSegment.py
INPUTFILES=../../fsa/test/input/*
OUTPUTFOLDER=../../fsa/test/output

current_time=$(date "+%Y.%m.%d-%H.%M.%S")
OUTPUTFOLDER=$OUTPUTFOLDER/$current_time
mkdir $OUTPUTFOLDER
echo $current_time >> ../log/ProcessFolder.log

for f in $INPUTFILES
do
    echo "Processing $f file..."
    filename=$(basename "$f")
    outputfile="$OUTPUTFOLDER/$filename"
    python MultiLevelSegment.pyc "$f" NoFeature > "$outputfile" 2>> ../log/ProcessFolder.log &
done

for f in $INPUTFILES
do
    echo "Processing $f file..."
    filename=$(basename "$f")
    outputfile="$OUTPUTFOLDER/$filename"
    python MultiLevelSegment.pyc "$f" Debug > "$outputfile_feature.txt" 2>> ../log/ProcessFolder_feature.log &
done

wait        #wait for all child process to complete.

end_time=$(date "+%Y.%m.%d-%H.%M.%S")
echo "$current_time - end at: $end_time " >> ../log/ProcessFolder.log
