#running in linux, macos, or MING (Git Bash) of Windows

#!/bin/bash
python3 FeatureOntology.py CreateLexicon > ~/tempLexicon/perX.txt
cp ~/tempLexicon/perX.txt ~/fsa/X/perX.txt
rm ~/tempLexicon/perX.txt
