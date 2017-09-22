import os,sys

def sortTest(testLocation):
    testList =  []
    with open(testLocation, encoding='utf-8') as test:
        for line in test:
            # print(line,end="")
            testList.append(line)
    testList = sorted(testList,key=lambda x: len(x))
    for line in testList:
        print(line,end="")

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if len(sys.argv) != 1:
        print("Usage: python OrganizeTest.py  > outputfile.txt")
        exit(0)
    para = dir_path + '/../../fsa/X/testSocial.txt'
    sortTest(para)


