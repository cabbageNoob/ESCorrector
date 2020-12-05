'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 19:53:31
'''
import os, sys
sys.path.insert(0, os.getcwd())
from escorrector import config
from escorrector.utils.logger import logger
import time, kenlm
import numpy as np


class ErrorType(object):
    confusion = 'confusion'
    word = 'word'
    char = 'char'
    redundancy = 'redundancy'   #冗余
    miss = 'miss'               #缺失
    word_char='word_char'       #分词后的碎片单字错误

class Detector(object):
    def __init__(self, language_model_path=config.language_model_path):
        self.name = 'detector'
        self.language_model_path = language_model_path
        self.is_char_error_detect = True
        self.initialized_detector = False

    def initialize_detector(self):
        t1 = time.time()
        try:
            import kenlm
        except ImportError:
            raise ImportError('mypycorrector dependencies are not fully installed, '
                              'they are required for statistical language model.'
                              'Please use "pip install kenlm" to install it.'
                              'if you are Win, Please install kenlm in cgwin.')

        self.lm = kenlm.Model(self.language_model_path)
        logger.debug('Loaded language model: %s, spend: %s s' %
                        (self.language_model_path, str(time.time() - t1)))
        self.initialized_detector = True

    def check_detector_initialized(self):
        if not self.initialized_detector:
            self.initialize_detector()

    def ngram_score(self, chars):
        """
        取n元文法得分
        :param chars: list, 以词或字切分
        :return:
        """
        self.check_detector_initialized()
        return self.lm.score(' '.join(chars), bos=False, eos=False)

    def ppl_score(self, words):
        """
        取语言模型困惑度得分，越小句子越通顺
        :param words: list, 以词或字切分
        :return:
        """
        self.check_detector_initialized()
        return self.lm.perplexity(' '.join(words))

    def score(self, words):
        """
        Return the log10 probability of a string.
        :param words: list, 以词或字切分
        :return:
        """
        self.check_detector_initialized()
        return self.lm.score(' '.join(words))

    @staticmethod
    def _check_contain_error(maybe_err, maybe_errors):
        """
        检测错误集合(maybe_errors)是否已经包含该错误位置（maybe_err)
        :param maybe_err: [error_word, begin_pos, end_pos, error_type]
        :param maybe_errors:
        :return:
        """
        error_word_idx = 0
        begin_idx = 1
        end_idx = 2
        for err in maybe_errors:
            if maybe_err[error_word_idx] in err[error_word_idx] and maybe_err[begin_idx] >= err[begin_idx] and \
                    maybe_err[end_idx] <= err[end_idx]:
                return True
        return False

    def _add_maybe_error_item(self, maybe_err, maybe_errors):
        """
        新增错误
        :param maybe_err:
        :param maybe_errors:
        :return:
        """
        if maybe_err not in maybe_errors and not self._check_contain_error(maybe_err, maybe_errors):
            maybe_errors.append(maybe_err)

    @staticmethod
    def _get_maybe_error_index(scores, ratio=0.6745, threshold=1.4):
        """
        取疑似错字的位置，通过平均绝对离差（MAD）
        :param scores: np.array
        :param threshold: 阈值越小，得到疑似错别字越多
        :return: 全部疑似错误字的index: list
        """
        result = []
        scores = np.array(scores)
        if len(scores.shape) == 1:
            scores = scores[:, None]
        median = np.median(scores, axis=0)  # get median of all scores
        # deviation from the median
        margin_median = np.abs(scores - median).flatten()
        # 平均绝对离差值
        med_abs_deviation = np.median(margin_median)
        if med_abs_deviation == 0:
            return result
        y_score = ratio * margin_median / med_abs_deviation
        # 打平
        scores = scores.flatten()
        maybe_error_indices = np.where(
            (y_score > threshold) & (scores < median))
        # 取全部疑似错误字的index
        result = list(maybe_error_indices[0])
        return result

    def detect(self, sentence):
        """
        检测句子中的疑似错误信息，包括[词、位置、错误类型]
        :param sentence:
        :return: list[list], [error_word, begin_pos, end_pos, error_type]
        """
        maybe_errors = []
        if not sentence.strip():
            return maybe_errors
        # 初始化
        self.check_detector_initialized()
       
        if self.is_char_error_detect:
            # 语言模型检测疑似错误字
            try:
                ngram_avg_scores = []
                for n in [2, 3]:
                    scores = []
                    for i in range(len(sentence) - n + 1):
                        word = sentence[i:i + n]
                        score = self.ngram_score(list(word))
                        scores.append(score)
                    if not scores:
                        continue
                    # 移动窗口补全得分
                    for _ in range(n - 1):
                        scores.insert(0, scores[0])
                        scores.append(scores[-1])
                    avg_scores = [sum(scores[i:i + n]) / len(scores[i:i + n])
                                    for i in range(len(sentence))]
                    ngram_avg_scores.append(avg_scores)

                # 取拼接后的n-gram平均得分
                sent_scores = list(np.average(
                    np.array(ngram_avg_scores), axis=0))
                # 取疑似错字信息
                for i in self._get_maybe_error_index(sent_scores):
                    token = sentence[i]
                    # # pass filter word
                    # if self.is_filter_token(token):
                    #     continue
                    # token, begin_idx, end_idx, error_type
                    maybe_err = [token, i, i + 1, ErrorType.char]
                    self._add_maybe_error_item(maybe_err, maybe_errors)
            except IndexError as ie:
                logger.warn("index error, sentence:" + sentence + str(ie))
            except Exception as e:
                logger.warn("detect error, sentence:" + sentence + str(e))
        return sorted(maybe_errors, key=lambda k: k[1], reverse=False)


if __name__ == '__main__':
    d = Detector()
    err_sentences = [
        '昨日下午，两江影视城民国街，毛泽东的扮演者贾云在时戏。重庆晨报记者高科摄',
        '皖水是一条大河，如果需要在和滩铺水泥建训练基地，需经安庆市水利局睡管科审批',
        '在提升区域旅游产业能寄过程中，运用信息技术，搭建相关产业融合共享的信息平台，形成以大运河文化为混、平台为先、联动为本的智慧旅游发展理念'
    ]
    for sent in err_sentences:
        err = d.detect(sent)
        print("original sentence:{} => detect sentence:{}".format(sent, err))
