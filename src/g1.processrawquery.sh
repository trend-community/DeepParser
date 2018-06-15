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
#  nohup sh g1.processrawquery.sh /nlpengine/queries/data/g0.raw.txt ../data/g0.P /nlpengine/fsa/X/Q /nlpengine/fsa/X/ &

set -x
mkdir -p $3/temp
mkdir -p $3/lexicon
mkdir -p $3/rule

#perl -pi -e 's/\x01/\t/g' $1

LC_ALL=C grep -Pva "\t[1-9]$" $1  > $3/temp/raw.10plus.txt
#LC_ALL=C grep -Pv "\t1[0-9]$" $3/temp/raw.10plus.txt  > $3/temp/raw.100plus.txt  # that removed some useful words. might be able to add up to more than 100. sample: 格纹
sed -e "s/[[:punct:]]/ /g" $3/temp/raw.10plus.txt > $3/temp/raw.10plus.nopunct.txt    #has to be executed manually to get the Chinese punct correct.
LC_ALL=C sed -e "s/[\x00-\x08\x0b-\x0c\x0e-\x1a]//g"  $3/temp/raw.10plus.nopunct.txt  > $3/temp/raw_wo_ctrl.10plus.nopunct.txt        #only keep \t \r \n

python3 g1.norm.py $3/temp/raw_wo_ctrl.10plus.nopunct.txt ../../fsa/X/LexBlacklist.txt ../../fsa/X/LexBlacklist_TopChars.txt $3/temp/dictoutput.txt $2 2>../temp/g1.norm.error.txt

python3 g1.generatewordlist.py $3/temp $2     2>../temp/g1.generatewordlist.error.txt


cat $4/AllLexicon.txt | awk -F: '{print $1}' > $3/temp/SystemLexicon.txt
cat $4/defLexX.txt | awk -F: '{print $1}' > $3/temp/SystemLexicon_defLex.txt
cat $4/defPlus.txt | awk -F: '{print $1}' >> $3/temp/SystemLexicon_defLex.txt
for f in $3/temp/gram*
do
  echo "processing $f ..."
    filename=$(basename "$f")
    outputfile="$3/temp/Mixed_$filename"
    python3 g1.sent.py  "$f" "$outputfile" $2 $3/temp/SystemLexicon.txt $3/temp/SystemLexicon_defLex.txt

    newlexiconname="$3/lexicon/CleanLexicon_$filename"
    grep -va "<" $outputfile | grep -Fxv -f $3/temp/SystemLexicon.txt | grep -Fxv -f $3/temp/SystemLexicon_defLex.txt> $newlexiconname &

    newrulename="$3/rule/CleanRule_$filename"
    echo "CleanRule_$filename ==  // $filename \n" > $newrulename
    # 1, search for rule; 2, add quotes for english word, 3, add rule name for each 2000 lines. | awk '1;!(NR%2000){print "CleanRule_$filename ==";}'
    grep -a "<" $outputfile | sed  -E  's/([< ])([a-z0-9A-Z][a-z0-9A-Z]*)([ >])/\1\[\x27\2\x27\]\3/g'   >> $newrulename &
done

echo "done. analyzing blacklisted lexicons."

grep  Blacklisted ../temp/g1.norm.error.txt | cut -f 4 -d : > ../temp/QbyLex.notsort.txt
awk '{ print length(), $0 | "sort -n" }'  ../temp/QbyLex.notsort.txt  | cut -f 2  -d\  > ../../fsa/extra/QbyLexBlacklist.txt
grep -Fx -f ../../fsa/extra/lexiconlist.txt ../../fsa/extra/QbyLexBlacklist.txt > ../../fsa/extra/Qlexcommon.txt
grep -Fxv -f ../../fsa/extra/Qlexcommon.txt ../../fsa/extra/QbyLexBlacklist.txt > ../../fsa/extra/Qlexcommon_N.txt


#Create oQcQ file.
rm $3/temp/LexX-oQcQ.all.txt
for f in $3/rule/CleanRule*
do
    sed 's/\/\/.*//' $f  >> $3/temp/LexX-oQcQ.all.txt		#remove comment
done

perl -pi -e 's/\:.*?\]/]/g'     $3/temp/LexX-oQcQ.all.txt
perl -pi -e 's/[<>\/\?]//g'     $3/temp/LexX-oQcQ.all.txt
perl -pi -e 's/\^\.?[A-Za-z]*//g'   $3/temp/LexX-oQcQ.all.txt
perl -pi -e   "s/[\[\]\']//g"   $3/temp/LexX-oQcQ.all.txt
perl -pi -e  's/ /\//g'         $3/temp/LexX-oQcQ.all.txt
#remove openning and trailing slash
perl -pi -e  's/^\/+//g'        $3/temp/LexX-oQcQ.all.txt
perl -pi -e   's/\/+$//'        $3/temp/LexX-oQcQ.all.txt
grep -E  ".{10,}" $3/temp/LexX-oQcQ.all.txt > $3/temp/LexX-oQcQ.10.txt
grep -v -E  ".{10,}" $3/temp/LexX-oQcQ.all.txt > $3/temp/LexX-oQcQ.txt
