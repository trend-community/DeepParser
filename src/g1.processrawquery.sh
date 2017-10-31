#!/bin/bash
#Usage for query data:
# Step 1, Generate wordlist.txt by removing special characters and the frequency
# : (Ust Ctrl-V-H to input ^H
#sed - e "s/^H\|^F\|^A.*//g" g0.raw.txt > wordlist.txt
# Step 2, Use g1.norm.py to generate pickle dictionary file w1.P
# Step 3.1 Website can utilize the pickle dictionary file w1.P now
# Step 3.2 Feed wordlist.txt into g1.sent.py using the same pickle dictionary file,
#	to generate rule file rule.txt
# Step 4, Generate "lexicon" from rule.txt using g1.generatelexicon.py
# Step 5, Remove "not rule" from rule.txt by:
#	grep -v "<" rule.txt > cleanrule.txt
# Step 6, include lexicon file and cleanrule.txt in parser pipeline.


# new steps, Oct 30.
#Usage:
#bash g1.processrawquery.sh rawfilelocation dictfilelocation rulefilefolder, lexiconfilefolder

sed -e "s/[\x02-\x09\x0b-\x0c\x0e-\x1a]//g" $1 > /tmp/raw_wo_ctrl.txt
python g1.norm.py /tmp/raw_wo_ctrl.txt /tmp/dictoutput.txt $2

mkdir -p $3
python g1.generatewordlist.py $3 $2

mkdir -p $4
for f in $3/*
do
    echo "processing $f ..."
    filename=$(basename "$f")
    outputfile="$4/Mixed_$filename"
    python g1.sent.py  "$f" "$outputfile" $2

    newlexiconname="$4/CleanLexicon_$filename"
    grep -v "<" $outputfile > $newlexiconname &

    newrulename="$3/CleanRule_$filename"
    grep "<" $outputfile > $newrulename &
done

echo "done"
