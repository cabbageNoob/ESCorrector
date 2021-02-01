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

sighan_2013 = os.path.join(pwd_path, './data/cn/sighan/sighan_2013_test.txt')
sighan_2014 = os.path.join(pwd_path, './data/cn/sighan/sighan_2014_test.txt')
sighan_2015 = os.path.join(pwd_path, './data/cn/sighan/sighan_2015_test.txt')

# 同音字
same_pinyin_path = os.path.join(pwd_path, 'data/same_pinyin.txt')
# 形似字
same_stroke_path = os.path.join(pwd_path, 'data/same_stroke.txt')

# 通用分词词典文件  format: 词语 词频
word_freq_path = os.path.join(pwd_path, 'data/cn/word_freq.txt')
# 知名人名词典 format: 词语 词频
_person_name_path = os.path.join(pwd_path, 'data/cn/person_name.txt')
# 地名词典 format: 词语 词频
_place_name_path = os.path.join(pwd_path, 'data/cn/place_name.txt')
# 停用词
stopwords_path = os.path.join(pwd_path, 'data/cn/stopwords.txt')
