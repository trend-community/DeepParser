

def fib_recursivive(n):
    if n <= 2:
        return 1
    else:
        return fib_recursivive(n-1) + fib_recursivive(n-2)

def fib_list(n):
    flist = [0, 1]
    for i in range(2, n+1):
        flist.append(flist[i-1]+flist[i-2])
    return flist[n]

def fib_recur_tail(n):
    return fib_recur_tail_helper(0, 1, n)

def fib_recur_tail_helper(a, b, n):
    if  n <= 0:
        return a
    return fib_recur_tail_helper(b, a+b, n-1)



def coinChange(centsNeeded, coinValues):
   minCoins = [[0 for j in range(centsNeeded + 1)]
               for i in range(len(coinValues))]
   minCoins[0] = list(range(centsNeeded + 1))

   for i in range(1,len(coinValues)):
      for j in range(0, centsNeeded + 1):
         if j < coinValues[i]:
            minCoins[i][j] = minCoins[i-1][j]
         else:
            minCoins[i][j] = min(minCoins[i-1][j],
             1 + minCoins[i][j-coinValues[i]])

   return minCoins[-1][-1]

def stringmatch(str1, str2):
    space = [[0 for j in range(len(str2)+1)]
             for i in range(len(str1)+1)
             ]

    for i in range(1, len(str1)+1):
        for j in range(1, len(str2)+1 ):
            if str1[i-1] == str2[j-1]:
                space[i][j] = 1+space[i-1][j-1]

    for j in range(1, len(str2)+1):
        if space[i][j] == len(str1):
            return  j
    return -1

if __name__ == "__main__":
    #print fib_recursivive(50)
    print(fib_list(500))
    print(fib_recur_tail(500))
    # for i in range(1, 12):
    #     print fib_list(i)
    # for i in range(1, 12):
    #     print fib_recur_tail(i)

    print(coinChange(36, [1,10,25]))

    str_1 = 'efk'
    str_2 = 'sefssefks'
    location = stringmatch(str_1, str_2)
    print("location:%s" % location)
    print(" found string: " + str_2[location-len(str_1): location])