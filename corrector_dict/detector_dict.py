'''
Descripttion: 
version: 
Author: nlpir team
Date: 2020-08-07 20:46:45
LastEditors: Please set LastEditors
LastEditTime: 2021-05-15 13:50:17
'''
import sys, os
import codecs, time

sys.path.insert(0, os.getcwd())
from corrector_dict import config
from utils.tokenizer import Tokenizer
from utils.text_utils import split_2_short_text
from utils.logger import logger


class DetectorDict(object):
    def __init__(self,custom_word_freq_path='',
                word_freq_path=config.word_freq_path,
                person_name_path=config.person_name_path,
                place_name_path=config.place_name_path,
                stopwords_path=config.stopwords_path,
                
                spec_nouns_path=config.spec_nouns_path,
                gangtai_path=config.gangtai_path,
                common_confusion_path=config.common_confusion_path):
        self.name = 'detector_dict'
        self.word_freq_path = word_freq_path
        self.person_name_path = person_name_path
        self.place_name_path = place_name_path
        self.stopwords_path = stopwords_path
        
        self.custom_word_freq_path = custom_word_freq_path
        self.spec_nouns_path = spec_nouns_path
        self.gangtai_path = gangtai_path
        self.common_confusion_path = common_confusion_path
        self.initialized_detector_dict = False   

    def initialize_detector_dict(self):
        t1 = time.time()
        self.confusions = dict()
        self.spec_nouns = self.load_dict(self.spec_nouns_path)
        self.gangtai = self.load_dict(self.gangtai_path)
        self.common_confusion = self.load_dict(self.common_confusion_path)
        
        self.confusions.update(self.spec_nouns)
        self.confusions.update(self.gangtai)
        self.confusions.update(self.common_confusion)
        self.confusions_words = list(self.confusions.keys())
        confusions_values = list(self.confusions.values())
        self.confusions_words.extend(confusions_values)

        # 词、频数dict
        self.word_freq = self.load_word_freq_dict(self.word_freq_path)
        # 自定义切词词典
        self.custom_word_freq = self.load_word_freq_dict(self.custom_word_freq_path)
        self.person_names = self.load_word_freq_dict(self.person_name_path)
        self.place_names = self.load_word_freq_dict(self.place_name_path)
        self.stopwords = self.load_word_freq_dict(self.stopwords_path)
        # 合并切词词典及自定义词典
        self.custom_word_freq.update(self.person_names)
        self.custom_word_freq.update(self.place_names)
        self.custom_word_freq.update(self.stopwords)
        self.word_freq.update(self.custom_word_freq)
        self.tokenizer = Tokenizer(dict_path=self.word_freq_path, custom_confusion_dict=self.confusions, custom_word_freq_dict=self.custom_word_freq)
        logger.debug('Loaded file: %s, size: %d, spend: %s s' %
                        (self.spec_nouns_path, len(self.confusions), str(time.time() - t1)))
        self.initialized_detector_dict = True

    def check_detector_dict_initialized(self):
        if not self.initialized_detector_dict:
            self.initialize_detector_dict()

    @staticmethod
    def load_word_freq_dict(path):
        """
        加载切词词典
        :param path:
        :return:
        """
        word_freq = {}
        if path:
            if not os.path.exists(path):
                logger.warning('file not found.%s' % path)
                return word_freq
            else:
                with codecs.open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('#'):
                            continue
                        info = line.split()
                        if len(info) < 1:
                            continue
                        word = info[0]
                        # 取词频，默认1
                        freq = int(info[1]) if len(info) > 1 else 1
                        word_freq[word] = freq
        return word_freq

    @staticmethod
    def load_dict(path):
        '''
        Descripttion: 加载切词词典
        param path 
        return word_truth
        '''
        word_truth = dict()
        with codecs.open(path, 'r', encoding='utf8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                info = line.split()
                if len(info) <= 1:
                    continue
                word = info[0]
                truth = info[1]
                word_truth[word] = truth
        return word_truth

    def max_backward_cut(self, sentence):
        #1.从右向左取待切分汉语句的m个字符作为匹配字段，m为大机器词典中最长词条个数。
        #2.查找大机器词典并进行匹配。若匹配成功，则将这个匹配字段作为一个词切分出来。
        cutlist = []
        index = len(sentence)
        maxword = 7 if len(sentence) >= 7 else len(sentence)
        while index > 0 :
            matched = False
            for i in range(maxword, 0, -1):
                tmp = i
                cand_word = sentence[index - tmp : index]
                #如果匹配上，则将字典中的字符加入到切分字符中
                if cand_word in self.confusions_words:
                    cutlist.append([cand_word, index - tmp, index])
                    matched = True
                    break
            #如果没有匹配上，则按字符切分
            if not matched:
                tmp = 1

            index -= tmp

        return cutlist[::-1]

    def detect_dict(self, text):
        '''
        Descripttion: 检测句子中的疑似错误信息，包括[词、位置、错误类型]
        param text
        return list[list]
        '''
        detector_words = []
        if not text.strip():
            return detector_words
        self.check_detector_dict_initialized()
        blocks = split_2_short_text(text, include_symbol=True)
        for blk, idx in blocks:
            detector_words += self.detect_dict_short(blk, idx)
        return detector_words

    def detect_dict_short(self, sentence, start_idx=0):
        """
        检测句子中的疑似错误信息，包括[词、位置、错误类型]
        :param sentence:
        :param start_idx:
        :return: list[list], [error_word, begin_pos, end_pos, error_type]
        """
        detector_words = []
        self.check_detector_dict_initialized()
        detector_words = self.max_backward_cut(sentence)

        return detector_words



if __name__ == '__main__':
    d = DetectorDict()
    p = '您真是一位好心的维权人士，疆独,装逼，“六四”'
    p = '中国民主党一位的维权人士，疆独'
    p = '身分不明确'
    p = '于网路上传播'
    print(d.detect_dict(p))
        