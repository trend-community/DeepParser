#running in linux, macos, or MING (Git Bash) of Windows

#!/bin/bash
mkdir ../temp
python FeatureOntology.py CreateFeatureList > ../temp/NewFeatureList.txt
echo "New features:"
diff ../temp/NewFeatureList.txt ../../fsa/extra/featurelist.txt | grep --color "<"
echo "Removed features:"
diff ../temp/NewFeatureList.txt ../../fsa/extra/featurelist.txt | grep --color ">"

read -p  "Ctrl-C to stop, or ENTER to accept the modification!"

cp ../temp/NewFeatureList.txt ../../fsa/extra/featurelist.txt
cd ../../fsa
git commit extra/featurelist.txt -m 'new feature list from feature.txt'
git push
