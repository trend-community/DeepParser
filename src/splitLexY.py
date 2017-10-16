
import logging, re, operator, sys, os, pickle, requests
import string
import shutil

from utils import *
from FeatureOntology import *

def splitTwoWords(para):
    with open(newpara, 'w', encoding="utf8") as file:
        with open(temp, 'w', encoding="utf8") as tempfile:
            with open(para, encoding= "utf8") as dictionary:
                for line in dictionary:
                    if line.startswith("//"):
                        tempfile.write(line)
                    code, comment = SeparateComment(line)
                    blocks = [x.strip() for x in re.split(":", code) if x]
                    if len(blocks) != 2:
                        #logging.warn("line is not in [word]:[features] format:\n\t" + line)
                        continue
                    if "_" in blocks[0]:
                        file.write(line)
                    else:
                        tempfile.write(line)





if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    para = dir_path + '/../../fsa/Y/lexY.txt'
    newpara = dir_path + '/../../fsa/Y/compoundY.txt'
    temp = dir_path + '/../../fsa/Y/lexYcopy.txt'
    splitTwoWords(para)

    shutil.move(temp, para)



