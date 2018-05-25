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
#bash g1.processrawquery.sh rawfilelocation dictfilelocation rulefilefolder lexiconfilefolder tempfolder systemlexiconfilelocation
#  nohup sh g1.processrawquery.sh /nlpengine.dev/queries/data/g0.raw.txt ../data/g0.P /nlpengine.dev/fsa/X/Q /nlpengine.dev/fsa/X/ &

set -x

#Create oQcQ file.
rm $3/temp/RulesoQcQ.txt
for f in $3/rule/CleanRule*
do
    sed 's/\/\/.*//' $f  >> $3/temp/RulesoQcQ.txt		#remove comment
done

perl -pi -e 's/\:.*?\]/]/g'     $3/temp/RulesoQcQ.txt
perl -pi -e 's/[<>\/\?]//g'     $3/temp/RulesoQcQ.txt
perl -pi -e 's/\^\.?[A-Za-z]*//g'   $3/temp/RulesoQcQ.txt
perl -pi -e   "s/[\[\]\']//g"   $3/temp/RulesoQcQ.txt
perl -pi -e  's/ /\//g'         $3/temp/RulesoQcQ.txt
#remove openning and trailing slash
perl -pi -e  's/^\/+//g'        $3/temp/RulesoQcQ.txt
perl -pi -e   's/\/+$//'        $3/temp/RulesoQcQ.txt

