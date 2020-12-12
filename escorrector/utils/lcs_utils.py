'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-10 11:50:19
'''
from typing import List

class compunit:
    def __init__(self, i, j, op):
        self.newi = i
        self.oldi = j
        self.operation = op


def LCS(a: str, b: str, result: List, istrack=True):
    lena = len(a)
    lenb = len(b)
    lcs = []

    for i in range(0, lena + 1):
        lcs.append([0] * (lenb + 1))
        lcs[i][0] = 0
    for i in range(0, lenb + 1):
        lcs[0][i] = 0

    for i in range(1, lena + 1):
        for j in range(1, lenb + 1):
            if a[i - 1] == b[j - 1]:
                lcs[i][j] = lcs[i - 1][j - 1] + 1
            elif lcs[i - 1][j] > lcs[i][j - 1]:
                lcs[i][j] = lcs[i - 1][j]
            else:
                lcs[i][j] = lcs[i][j - 1]

    if not istrack:
        res = lcs[lena][lenb]
        return res
    i = lena
    j = lenb
    res = lcs[i][j]
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            result.append(compunit(i, j, 0))
            i -= 1
            j -= 1
        elif lcs[j][j - 1] > lcs[i - 1][j]:
            result.append(compunit(i, j, 1))
            j -= 1
        else:
            result.append(compunit(i, j, 2))
            i -= 1
    return res


if __name__ == '__main__':
    s1 = "intention"
    s2 = "execution"
    rst = []
    print(LCS(s1, s2, rst, True))