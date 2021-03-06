'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
Date: 2021-05-10 21:00:47
'''
import logging
import os, re
import jieba
from jieba import posseg
jieba.re_han_default = re.compile("([\u4E00-\u9FD5a-zA-Z0-9+#&\._%\S\s]+)", re.U)

def segment(sentence, cut_type='word', pos=False):
    """
    切词
    :param sentence:
    :param cut_type: 'word' use jieba.lcut; 'char' use list(sentence)
    :param pos: enable POS
    :return: list
    """
    if pos:
        if cut_type == 'word':
            word_pos_seq = posseg.lcut(sentence)
            word_seq, pos_seq = [], []
            for w, p in word_pos_seq:
                word_seq.append(w)
                pos_seq.append(p)
            return word_seq, pos_seq
        elif cut_type == 'char':
            word_seq = list(sentence)
            pos_seq = []
            for w in word_seq:
                w_p = posseg.lcut(w)
                pos_seq.append(w_p[0].flag)
            return word_seq, pos_seq
    else:
        if cut_type == 'word':
            return jieba.lcut(sentence)
        elif cut_type == 'char':
            return list(sentence)


class Tokenizer(object):
    def __init__(self, dict_path='', custom_word_freq_dict=None, custom_confusion_dict=None, custom_list=None):
        self.model = jieba
        self.model.default_logger.setLevel(logging.ERROR)
        # 初始化大词典
        if os.path.exists(dict_path):
            self.model.set_dictionary(dict_path)
        # 加载用户自定义词典
        if custom_word_freq_dict:
            for w, f in custom_word_freq_dict.items():
                self.model.add_word(w, freq=f)
        # 加载混淆集词典
        if custom_confusion_dict:
            for k, word in custom_confusion_dict.items():
                # 添加到分词器的自定义词典中
                self.model.add_word(k)
                self.model.add_word(word)
        # 加载词典列表
        if custom_list:
            for word in custom_list:
                self.model.add_word(word)

    def tokenize(self, sentence):
        """
        切词并返回切词位置
        :param sentence:
        :return: (word, start_index, end_index) model='default'
        """
        return list(self.model.tokenize(sentence))

    def jieba_cut(self, sentence):
        """
        切词
        :param sentence:
        :return: ['','','']
        """
        return list(self.model.cut(sentence))

if __name__ == '__main__':
    jieba.add_word('“蔡佳豪”')
    jieba.add_word('蔡佳豪')
    print(list(jieba.tokenize('我是“蔡佳豪”')))
    tokenizer = Tokenizer()
    print(tokenizer.jieba_cut('我是蔡佳豪本人'))
