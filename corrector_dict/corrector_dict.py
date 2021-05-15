'''
Descripttion: 
version: 
Author: nlpir team
Date: 2020-08-07 20:46:23
LastEditors: Please set LastEditors
LastEditTime: 2021-05-14 14:35:59
'''
import sys, os
sys.path.insert(0, os.getcwd())
from corrector_dict.detector_dict import DetectorDict
from utils.text_utils import get_correct_text
from utils.text_utils import split_2_short_text, traditional2simplified, _check_contain_error
from collections import Iterable

class CorrectorDict(DetectorDict):
    def __init__(self):
        super(CorrectorDict, self).__init__()
        self.name = 'corrector_dict'

    def add_dict(self, words, separators='-'):
        """增加混淆集对

        传入的参数可以是：一个词语、一个列表、一个元组、甚至是一个文件地址，文件地址里面是包含一行一个词语

        格式1： 只增加一个词

        格式2：增加一个列表

        :param words: 可以传列表、文件地址、或者字符串，如果字符串包含separators，则默认为传入混淆集对，
                      比如：度假-渡假

        :param separators: 地址分割符，比如：度假-渡假、分割符是：-
        """
        if isinstance(words, str):
            words = words.strip()  # 去除空格
            if os.path.exists(words):  # 判断是否存在该文件
                with open(words, encoding='UTF-8')as fp:
                    for word in fp:
                        self.add_dict(word, separators)
            elif separators in words:  # 判断是否带有分割符
                self.common_confusion.update({words.split(separators)[0]:words.split(separators)[1]})
            else:  # 纯字符串
                raise Exception('未指定混淆集的分隔符')
        elif isinstance(words, Iterable):  # 迭代器
            for word in words:
                self.add_dict(word, separators)
    
    def correct_dict(self, text, include_symbol=True):
        '''
        Descripttion: 句子改错
        param text
        return 改正后的句子
        '''
        details = []
        blocks = split_2_short_text(text, include_symbol=include_symbol)
        for blk, idx in blocks:
            details = self.correct_dict_short(blk, start_idx=idx, details=details)
        return details

    def correct_dict_short(self, sentence, start_idx=0, details=[]):
        detector_words = self.detect_dict_short(sentence)
        for item, begin_idx, end_idx in detector_words:
            if item in self.confusions:
                detail_word = [item, self.confusions[item], begin_idx + start_idx, end_idx + start_idx,'dict']
                details.append(detail_word)

        tokens = self.tokenizer.tokenize(sentence)
        for word, begin_idx, end_idx in tokens:
            if _check_contain_error([word, begin_idx + start_idx, end_idx + start_idx], details):
                continue
            word_simplified = traditional2simplified(word)
            if word_simplified != word:
                # 繁化简错误
                detail_word = [word, word_simplified, begin_idx + start_idx, end_idx + start_idx, 'traditional']
                details.append(detail_word)
                
        return details

    
if __name__ == '__main__':
    correct = CorrectorDict()
    err_sentences = [
    # '记者从全国总工会今天召开的2021年“五一”新闻发布会上获悉,憂郁的臺灣烏龜',
    '一带一路於网路',
    '您真是一位好心的维权人士，疆独,六四,装逼,国家粮食局',
    '中国民主党一位的维权人士，疆独',
    '中国民主党',
    '根据中国互联网络信息中心(China Internet Network Information Center，简称CNNIC)于2015年2月发布的第35次',
    '于网路上传播'
    ]
    for err_sent in err_sentences:
        pred_detail = correct.correct_dict(err_sent)
        pred_sent = get_correct_text(err_sent, pred_detail)
        print(pred_sent, pred_detail)
