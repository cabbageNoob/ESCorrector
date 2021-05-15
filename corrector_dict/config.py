'''
Descripttion: 
version: 
Author: nlpir team
Date: 2020-08-07 20:46:33
LastEditors: Please set LastEditors
LastEditTime: 2021-05-15 13:47:39
'''
import os

pwd_path = os.path.abspath(os.path.dirname(__file__))

# 特殊名词
spec_nouns_path = os.path.join(pwd_path, '../data/dict/spec_nouns.txt')
# common 混淆集
common_confusion_path = os.path.join(pwd_path, '../data/dict/common_confusion.txt')
# 港台说法混淆集
gangtai_path = os.path.join(pwd_path,'../data/dict/gangtai.txt')


# 通用分词词典文件  format: 词语 词频
word_freq_path = os.path.join(pwd_path, '../data/word_freq.txt')
char_freq_path = os.path.join(pwd_path, '../data/char_freq.txt')
# 知名人名词典 format: 词语 词频
person_name_path = os.path.join(pwd_path, '../data/person_name.txt')
# 地名词典 format: 词语 词频
place_name_path = os.path.join(pwd_path, '../data/place_name.txt')
# 停用词
stopwords_path = os.path.join(pwd_path, '../data/stopwords.txt')
