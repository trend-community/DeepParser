# usage: sh run_diff.sh [baseline file] [regression output file]


# 运行 diff 比较程序
baseline=$1
regressionOut=$2
output=diff.out
python diff.py ${baseline} ${regressionOut} > diff.out
echo "diff.py is done."
echo "output is ${output}"

