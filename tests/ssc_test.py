'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
Date: 2021-02-05 15:13:39
'''
import sys, os
sys.path.insert(0, os.getcwd())
from escorrector.utils.ssc_utils import compute_equal_rate
from escorrector.corrector_regexp import Corrector

c = Corrector(is_char_correct=False,is_word_correct=True,index_name='no_genera_people14_sighan_test')

rate1 = compute_equal_rate(c.get_word_ssc('正确')[:4], c.get_word_ssc('争取')[:4])
print(c.get_word_ssc('正确'))
print(c.get_word_ssc('争取'))
print(rate1)
rate1 = compute_equal_rate(c.get_word_ssc('一一')[:4], c.get_word_ssc('事发')[:4])
print(c.get_word_ssc('一一'))
print(c.get_word_ssc('事发'))