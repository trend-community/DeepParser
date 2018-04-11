# usage: sh run.sh [input_file_prefix] 
# e.g.
# sh run.sh testUnit
# sh run.sh testJD

# Notes: 
#
# For better formatting the output filename, don't add the surfix of the input file.

set -e -x

testFileNamePrefix=$1
date=`date +%Y%m%d`
#yesterday=`date -v-1d +%Y%m%d`
yesterday=20180408

# 输出文件保存的目录，自行修改
outputFilePath=~/temp

resFileName=${testFileNamePrefix}_regtest_${date}.txt
regressionInput=~/git/fsa/test/input/${testFileNamePrefix}.txt 
regressionOutput=${outputFilePath}/${resFileName} 
cd ../..  # go to 'src' dir
python LexicalAnalyze.py ${regressionInput} > ${regressionOutput} --mode simple
echo "regression_test.py is done."

baseFileName=${testFileNamePrefix}_regtest_${yesterday}.txt
diffInput=${outputFilePath}/${baseFileName} 
diffOutput=${outputFilePath}/${resFileName} 
cd test/regression_test # from 'src' back to this dir
python diff.py ${diffInput} ${diffOutput} ${regressionInput} > ${testFileNamePrefix}.diff
echo "diff.py is done."
