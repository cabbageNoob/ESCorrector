'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 20:20:42
'''

import json
import sys, os
sys.path.insert(0,os.getcwd())
pwd_path = os.path.abspath(os.path.dirname(__file__))
 
from ctypes import * #Python的一个外部库，提供和C语言兼容的数据类型，可以很方便地调用C DLL中的函数.访问dll，首先需引入ctypes库
libFile = os.path.join(pwd_path, '../tools/nlpir_tools/NLPIR-ICTCLAS/lib/win64/new/NLPIR.dll')

libSoFile=os.path.join(pwd_path,'../tools/nlpir_tools/NLPIR-ICTCLAS/lib/linux64/libNLPIR.so')
NLPIR_ICTCLAS_path = os.path.join(pwd_path, '../tools/nlpir_tools/NLPIR-ICTCLAS')
# dll =  CDLL(libSoFile)    # 支持linux
dll = CDLL(libFile) #支持windows


def loadFun(exportName, restype, argtypes):
    global dll
    f = getattr(dll,exportName)
    f.restype = restype
    f.argtypes = argtypes
    return f

class ENCODING:
    GBK_CODE        =   0               #默认支持GBK编码
    UTF8_CODE       =   GBK_CODE+1      #UTF8编码
    BIG5_CODE       =   GBK_CODE+2      #BIG5编码
    GBK_FANTI_CODE  =   GBK_CODE+3      #GBK编码，里面包含繁体字
 
 
Init = loadFun('NLPIR_Init',c_int, [c_char_p, c_int, c_char_p])
Tokenizer4IR = loadFun('NLPIR_Tokenizer4IR', c_char_p, [c_char_p, c_bool])
Freqstat=loadFun('NLPIR_WordFreqStat',c_char_p,[c_char_p])

if not Init(NLPIR_ICTCLAS_path.encode('UTF-8'),ENCODING.UTF8_CODE,b''):
    print("Initialization failed!")
    exit(-111111)
 
def tokenizer4IR(sentence):
    result = Tokenizer4IR(sentence.encode('UTF-8'), False)
    # print('result  ',result)
    return json.loads(result)

def Freq(sentence):
    result = Freqstat(sentence.encode('UTF-8'))
    result = str(result, encoding="utf-8")
    print(result)
    
if __name__ == "__main__":
    print('1111111')
    p = '但却也英尺违反了和普茨迈斯特之间的保密协议。最终，普茨迈斯特出于各项商业方面考虑，仍与三一重工达成最终协议。'
    # p = '为期两天的谈判结束后，美国总统军控问题特使比林斯利在周二的新闻发布会上说'
    print(tokenizer4IR(p))



            