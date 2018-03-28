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
#  nohup sh g1.processrawquery.sh /nlpengine.dev/queries/data/g0.raw.txt ../data/g0.P /nlpengine.dev/fsa/X/Q/rule /nlpengine.dev/fsa/X/Q/lexicon /nlpengine.dev/fsa/X/Q/temp /nlpengine.dev/fsa/X/AllLexicon.txt &

mkdir -p $5
perl -pi -e 's/\x01/\t/g' $1

LC_ALL=C sed -e "s/[\x00-\x09\x0b-\x0c\x0e-\x1a]//g" $1 > $5/raw_wo_ctrl2.txt
LC_ALL=C sed -e "s/[[:punct:]]/ /g" $5/raw_wo_ctrl2.txt > $5/raw_wo_ctrl.txt
LC_ALL=C grep -Pv "\t[1-9]$" $5/raw_wo_ctrl.txt  > $5/raw_wo_ctrl.10plus.txt
LC_ALL=C grep -Pv "\t[1-9][0-0]$" $5/raw_wo_ctrl.10plus.txt  > $5/raw_wo_ctrl.100plus.txt
python3 g1.norm.py $5/raw_wo_ctrl.100plus.txt ../../fsa/X/LexBlacklist.txt ../../fsa/X/LexBlacklist_TopChars.txt $5/dictoutput.txt $2 2>../temp/g1.norm.error.txt

python3 g1.generatewordlist.py $5 $2     2>../temp/g1.generatewordlist.error.txt

mkdir -p $3
mkdir -p $4
cat $6 | awk -F: '{print $1}' > $5/SystemLexicon.txt
for f in $5/gram*
do
    echo "processing $f ..."
    filename=$(basename "$f")
    outputfile="$5/Mixed_$filename"
    python3 g1.sent.py  "$f" "$outputfile" $2 $5/SystemLexicon.txt

    newlexiconname="$4/CleanLexicon_$filename"
    grep -va "<" $outputfile | grep -Fxv -f $5/SystemLexicon.txt > $newlexiconname &

    newrulename="$3/CleanRule_$filename"
    echo "$filename QRule ==  // $filename \n" > $newrulename
    grep -a "<" $outputfile | awk '1;!(NR%2000){print "QRule ==";}' >> $newrulename &
done

echo "done. analyzing blacklisted lexicons."

grep  Blacklisted ../temp/g1.norm.error.txt | cut -f 4 -d : > ../temp/QbyLex.notsort.txt
awk '{ print length(), $0 | "sort -n" }'  ../temp/QbyLex.notsort.txt  | cut -f 2  -d\  > ../../fsa/extra/QbyLexBlacklist.txt
grep -Fx -f ../../fsa/extra/lexiconlist.txt ../../fsa/extra/QbyLexBlacklist.txt > ../../fsa/extra/Qlexcommon.txt
grep -Fxv -f ../../fsa/extra/Qlexcommon.txt ../../fsa/extra/QbyLexBlacklist.txt > ../../fsa/extra/Qlexcommon_N.txt

