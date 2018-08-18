set -e -x

outputPath=$1
date=`date +%Y%m%d`

cd ../..  # go to 'src' dir

#  get data
dbPath=~/git/fsa/test/input/badcase/badcase.db
sqlite3 ${dbPath} "SELECT query FROM badcase WHERE is_fixed=0" >  badcase.all.${date}

# run
python LexicalAnalyze.py badcase.all.${date} > ${outputPath}/badcase.all.${date}.txt --type simple --keeporigin yes
rm badcase.all.${date}
