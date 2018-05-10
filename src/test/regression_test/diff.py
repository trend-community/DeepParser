#coding=utf8
import sys, logging
import hashlib

def load(filename):
    ret_dict = {}
    fr = open(filename, 'r')
    for line in fr.readlines():
        f = line.strip().split('\t')

        if len(f) == 1:
            f.append('NULL')

        try:
            ret_dict[f[1]] = f[0]
        except:
            print('Error field:' + line)
    fr.close()
    return ret_dict


def diff(listA, listB):
    #求交集的两种方式
    retA = [i for i in listA if i in listB]

    #求差集，在 A 中但不在 B 中
    retB = [i for i in listA if i not in listB]

    #求差集，在 B 中但不在 A 中
    retC = list(set(listB).difference(set(listA)))

    return retA, retB, retC


def check_baseline(baseline_file, result_file):
    diff_count = 0
    total = 0

    baseline_dict = load(baseline_file)
    result_dict = load(result_file)
    common_list, baseline_new_list, result_new_list = diff(baseline_dict.keys(), result_dict.keys()) 

    for k in common_list:
        if baseline_dict[k] != result_dict[k]:
            diff_count += 1
            print(k + '\t' + result_dict[k])
    print('total count is %d, total diffs is %d, diff rate is %.3f' % 
                (len(common_list), diff_count, diff_count * 1.000/len(common_list)))


check_baseline(sys.argv[1], sys.argv[2])
