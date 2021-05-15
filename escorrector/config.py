'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 19:53:58
'''
import os

pwd_path = os.path.abspath(os.path.dirname(__file__))

# ngram模型
language_model_path = '/data/caijiahao/corrector_data/kenlm/zh_giga.no_cna_cmn.prune01244.klm' #zh_giga.no_cna_cmn.prune01244.klm   people2014corpus_chars.klm
# word ngram 模型
language_word_model_path = '/data/caijiahao/corrector_data/kenlm/people2014_word.klm'
# 音形码文件
hanzi_ssc_path = '/data/caijiahao/corrector_data/ssc_data/hanzi_ssc_res.txt'

# 同音字
same_pinyin_path = os.path.join(pwd_path, '../data/same_pinyin.txt')
# 形似字
same_stroke_path = os.path.join(pwd_path, '../data/same_stroke.txt')

# 同音词
word_similar_path = '/data/caijiahao/corrector_data/word_pinyin_similar_new.json'
# 通用分词词典文件  format: 词语 词频
word_freq_path = os.path.join(pwd_path, '../data/word_freq.txt')
char_freq_path = os.path.join(pwd_path, '../data/char_freq.txt')

# 建立索引的语料文件
index_data_dir = os.path.join(pwd_path, '../data/index_data/')
