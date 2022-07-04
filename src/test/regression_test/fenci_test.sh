set -e -x

input=~/git/fsa/test/input/badcase/testFenci.txt
cd ../../ && python test/regression_test/offline_fenci_test.py ${input} 
