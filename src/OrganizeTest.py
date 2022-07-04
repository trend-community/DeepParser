import os,sys
from Lexicon import LoadLexicon
from Lexicon import OutputLexicon
from FeatureOntology import LoadFeatureOntology
import shutil

def sortTest(testLocation, outputLocation):
    testList = set()
    with open(testLocation, encoding='utf-8') as test:
        for line in test:
            # print(line,end="")
            testList.add(line)
    testList = sorted(testList,key=lambda x: len(x))
    with open(outputLocation, 'w', encoding = 'utf-8') as output:
        for line in testList:
            output.write(line)


def sortLexicon(outputLocation,Englishflag=False):
    with open(outputLocation,'w',encoding="utf-8") as output:
        outputString = OutputLexicon(Englishflag)
        output.write(outputString)


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))

    inputPath = dir_path + '/../../fsa/extra/sort.txt'
    outputPath = dir_path + '/../../fsa/extra/temp.txt'

    if len(sys.argv) == 1:
        sortTest(inputPath, outputPath)
        shutil.move(outputPath, inputPath)
    elif len(sys.argv) == 2:
        command = sys.argv[1]
        if command == "sortLexicon":
            LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
            LoadLexicon(inputPath)
            sortLexicon(outputPath)
            shutil.move(outputPath, inputPath)
        else :
            print("Usage: python OrganizeTest.py sortLexicon")
            exit(0)
    elif len(sys.argv) == 4 :
        command = sys.argv[1]
        inputPath = dir_path + sys.argv[2]
        outputPath = dir_path + sys.argv[3]
        if command == "sortTest":
            sortTest(inputPath, outputPath)
        elif command == "sortLexicon":
            LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
            LoadLexicon(inputPath)
            if "/fsa/X" in inputPath:
                Englishflag = False
                sortLexicon(outputPath)
            else:
                Englishflag = True
                sortLexicon(outputPath, True)


    else:
        print("Usage: python OrganizeTest.py sortLexicon inputFile outputFile")
        exit(0)




