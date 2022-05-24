#!/bin/bash
# loop through a folder to do LexicalAnalyze

#usage: ProcessFolder.sh ../evaluate/5/CLIPS_RAW/1-SPEN/*.txt ../../temp/output graphjson


#INPUTFILES="../../temp/input/*.txt"
INPUTFILES=$1
OUTPUTFOLDER=$2
TYPE=$3

current_time=$(date "+%Y.%m.%d-%H.%M.%S")
TEMPFOLDER=$OUTPUTFOLDER/$current_time

mkdir $TEMPFOLDER

for f in $INPUTFILES/*.txt
do
    echo "Processing $f file..."
    filename=$(basename "$f")
    outputfile="$TEMPFOLDER/$filename"
    #echo $outputfile
    #echo $filename
    python3 LexicalAnalyze_Document_RestfulService.py --type $TYPE "$f"  > "$outputfile" 2>> "../log/ProcessFolder_$filename.log"
done

end_time=$(date "+%Y.%m.%d-%H.%M.%S")
