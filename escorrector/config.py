'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 19:53:58
'''
import os

pwd_path = os.path.abspath(os.path.dirname(__file__))
# 人民日报2014ngram模型
language_model_path = os.path.join(pwd_path, './data/kenlm/people2014corpus_chars.klm')

# 校对测试文件
test_path = os.path.join(pwd_path, './data/cn/test_set/test.json')
# 音形码文件
hanzi_ssc_path = os.path.join(pwd_path, './data/ssc_data/hanzi_ssc_res.txt')
