#!/usr/bin/python

#Create 2-gram from top 500 characters
#   and 3-gram from top 100 characters
# from ..\..\fsa\extra\ChineseTopCharacters.txt
# to ..\..\fsa\X\LexBlacklist_TopChars.txt

import os, zipfile
import utils

TopCharacterFile = "../../fsa/extra/ChineseTopCharacters.txt"
OutputFile = "../../fsa/X/LexBlacklist_TopChars.txt"

def LoadTopCharacters(FileLocation):
    Top500 = ""
    with open(FileLocation, encoding="utf-8") as dictionary:
        for lined in dictionary:
            characters, _ = utils.SeparateComment(lined)
            if not characters:
                continue
            Top500 += characters
    return Top500[:100], Top500

if __name__ == "__main__":

    T100, T500 = LoadTopCharacters(TopCharacterFile)
    if OutputFile.startswith("."):
        OutputFile = os.path.join(os.path.dirname(os.path.realpath(__file__)),  OutputFile)

    with open(OutputFile, "w", encoding="utf-8") as fout:
        for c1 in T500:
            for c2 in T500:
                fout.write(c1 + c2 + "\n")
        for c1 in T100:
            for c2 in T100:
                for c3 in T100:
                    fout.write(c1 + c2 + c3 + "\n")

    z = zipfile.ZipFile(OutputFile + ".zip", "w", zipfile.ZIP_DEFLATED)
    z.write(OutputFile, os.path.basename(OutputFile))
    z.close()