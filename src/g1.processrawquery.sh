#!/bin/sh
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

#Usage:
#bash g1.processrawquery.sh rawfilelocation dictfilelocation rulefilelocation, lexiconfilelocation

sed -e "s/\|\|.*//g" $1 > /tmp/wordlist.txt
python g1.norm.py $1 /tmp/dictoutput.txt $2
python g1.sent.py /tmp/wordlist.txt /tmp/notcleanrule.txt $2
python g1.generatelexicon.py /tmp/notcleanrule.txt $4
echo -e "QueryRule ==  \\ $1 \n"   > $3
grep -v "<" /tmp/notcleanrule.txt >> $3
