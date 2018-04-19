set -e -x

outputPath=$1
date=`date +%Y%m%d`

#  get data
cat ../../../../fsa/test/input/badcase/*badcase.txt > badcase.all.${date}

# run
cd ../..  # go to 'src' dir
python LexicalAnalyze.py badcase.all.${date} > ${outputPath}/badcase.all.${date}.out --mode simple
