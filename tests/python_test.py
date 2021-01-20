'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-12 10:14:29
'''
import sys, os
sys.path.insert(0, os.getcwd())
from escorrector.utils.nlpir_tokenizer import tokenizer4IR
from escorrector.utils.lcs_utils import LCS

# print(tokenizer4IR('遇到逆竞时'))
# print(LCS('混', '核心', [], istrack = False))
# print(LCS('混', '主', [], istrack = False))

print(len('很忙'.encode()))
