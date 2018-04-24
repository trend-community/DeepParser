# usage: sh run.sh [input_file_prefix] 
# e.g.
# sh run.sh testUnit
# sh run.sh testJD

# Notes: 
#
# For better formatting the output filename, don't add the surfix of the input file.

set -e -x

# 测试集前缀
# TODO: 用正则取文件前缀？
testFileNamePrefix=$1

# 获取今天的日期和昨天的日期
date=`date +%Y%m%d`
yesterday=`date -d '1 days ago' +%Y%m%d`
#yesterday=20180408

# 输出文件保存的目录，默认是~/temp
if [ ! -n "$2" ];then
	outputFilePath=~/temp
else
	outputFilePath=$2
fi

# 运行 parser 分析程序
resFileName=${testFileNamePrefix}_regtest_${date}.txt
regressionInput=~/git/fsa/test/input/${testFileNamePrefix}.txt 
regressionOutput=${outputFilePath}/output/${resFileName} 
cd ../..  # go to 'src' dir
python LexicalAnalyze.py ${regressionInput} > ${regressionOutput} --mode simple
echo "regression_test.py is done."

# 运行 diff 比较程序
baseFileName=${testFileNamePrefix}_regtest_${yesterday}.txt
diffInput=${outputFilePath}/output/${baseFileName} 
diffOutput=${outputFilePath}/output/${resFileName} 
cd test/regression_test # from 'src' back to this dir
python diff.py ${diffInput} ${diffOutput} ${regressionInput} > ${outputFilePath}/diff/${testFileNamePrefix}.${date}.diff
echo "diff.py is done."

