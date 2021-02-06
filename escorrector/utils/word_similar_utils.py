'''
@Descripttion: 计算出分词词典中相似词
@Author: cjh (492795090@qq.com)
Date: 2021-02-05 15:22:04
'''

import sys, os
sys.path.insert(0, os.getcwd())

import Levenshtein

from escorrector.detector import Detector
from escorrector.utils.ssc_utils import compute_equal_rate
from escorrector.utils.file_utils import writejson2file, readjson
from escorrector.utils.text_utils import is_chinese_string

pwd_path = os.path.abspath(os.path.dirname(__file__))
word_freq_path = os.path.join(pwd_path, '../data/cn/word_freq.txt')
word_similar_path = os.path.join(pwd_path, '../data/cn/word_similar.json')
hanzi_ssc_path = os.path.join(pwd_path, '../data/ssc_data/hanzi_ssc_res.txt')

def _getHanziSSCDict(hanzi_ssc_path):
    hanziSSCDict = {}#汉字：SSC码
    with open(hanzi_ssc_path, 'r', encoding='UTF-8') as f:#文件特征：U+4EFF\t仿\t音形码\n
        for line in f:
            line = line.split()
            hanziSSCDict[line[1]] = line[2]
    return hanziSSCDict

def get_word_sound_code(word, hanziSSCDict):
    '''
    Descripttion: 返回字符串的音码
    param {*}
    return {*}
    '''
    sound_code=''
    for char in word:
        if hanziSSCDict.get(char) == None:
            sound_code += '0' * 3
        else:
            sound_code += hanziSSCDict.get(char)[:3]
    return sound_code

def get_similar(word_freq_path, word_similar_path,threshold=0.75):
    hanziSSCDict = _getHanziSSCDict(hanzi_ssc_path)
    word_freq = Detector.load_word_freq_dict(word_freq_path)
    word_similar = {}
    for word_one, freq_one in word_freq.items():
        if len(word_one) == 2 and is_chinese_string(word_one):
            print(word_one)
            word_similar[word_one] = []
            for word_two, freq_two in word_freq.items():
                if len(word_two) == 2 and is_chinese_string(word_two) and word_one != word_two:
                    # if compute_equal_rate(get_word_sound_code(word_one,hanziSSCDict), get_word_sound_code(word_two,hanziSSCDict)) >= threshold:
                    if Levenshtein.distance(get_word_sound_code(word_one, hanziSSCDict), get_word_sound_code(word_two, hanziSSCDict)) <= 1:
                        word_similar[word_one].append((word_two, freq_two))
    writejson2file(word_similar, word_similar_path)

if __name__ == "__main__":
    get_similar(word_freq_path, word_similar_path)
    hanziSSCDict = _getHanziSSCDict(hanzi_ssc_path)
    print(Levenshtein.distance(get_word_sound_code('争取', hanziSSCDict), get_word_sound_code('正确', hanziSSCDict)))
    print(get_word_sound_code('一一', hanziSSCDict))
    print(get_word_sound_code('一生', hanziSSCDict))