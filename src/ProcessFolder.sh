#!/bin/bash
# loop through a folder to do MultiLevelSegment.py
INPUTFILES=../../fsa/test/input/*
OUTPUTFOLDER=../../fsa/test/output

for f in $INPUTFILES
do
    echo "Processing $f file..."
    filename=$(basename "$f")
    outputfile="$OUTPUTFOLDER/$filename"
    python MultiLevelSegment.py "$f" NoFeature > "$outputfile" 2>> ../log/ProcessFolder.log &
    #python MultiLevelSegment.pyc "$f" Debug > "$outputfile_feature.txt" 2>> ../log/ProcessFolder_feature.log &
    #python MultiLevelSegment_RestfulService.pyc "$f" NoFeature > "$outputfile" 2>> ../log/ProcessFolder.log &
done

