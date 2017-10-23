import os,sys
from Lexicon import LoadLexicon
from Lexicon import OutputLexicon
from FeatureOntology import LoadFeatureOntology


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


def sortLexicon(outputLocation):
    with open(outputLocation,'w',encoding="utf-8") as output:
        outputString = OutputLexicon(Englishflag)
        output.write(outputString)


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))


    if len(sys.argv) != 4:
        print("Usage: python OrganizeTest.py sortTest/sortLexicon inputFile outputFile")
        exit(0)

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
        else:
            Englishflag = True
        sortLexicon(outputPath)

    else:
        print("Usage: python OrganizeTest.py sortTest/sortLexicon inputFile outputFile")
        exit(0)




