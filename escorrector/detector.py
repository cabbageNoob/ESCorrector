
import os, sys
sys.path.insert(0, os.getcwd())

from corrector_dict.detector_dict import DetectorDict
from utils.logger import logger
from utils.text_utils import is_alphabet_string, is_chinese_string, uniform, readjson
import time, codecs
from escorrector import config
import numpy as np
np.seterr(invalid='ignore')
PUNCTUATION_LIST = ".。,，,、?？:：;；{}[]【】“‘’”《》/!！%……（）<>@#$~^￥%&*\"\'=+-_——「」"

class ErrorType(object):
    word = 'word'
    char = 'char'
    word_char = 'word_char'
    redundancy = 'redundancy'
    similar = 'similar'
    regex='regex'

class Detector(object):
    def __init__(self, language_model_path=config.language_model_path,
                language_word_model_path=config.language_word_model_path,
                is_word_error_detect=True,
                is_char_error_detect=True):
        self.name = 'detector'
        self.language_model_path = language_model_path
        self.language_word_model_path = language_word_model_path
        self.is_word_error_detect = is_word_error_detect
        self.is_char_error_detect = is_char_error_detect
        self.initialized_detector = False

    def initialize_detector(self):
        t1 = time.time()
        try:
            import kenlm
            self.lm = kenlm.Model(self.language_model_path)
            logger.debug('Loaded language model: %s, spend: %s s' %
                        (self.language_model_path, str(time.time() - t1)))
            t1 = time.time()
            self.lm_word = kenlm.Model(self.language_word_model_path)
            logger.debug('Loaded language model: %s, spend: %s s' %
                        (self.language_word_model_path, str(time.time() - t1)))
        except Exception:
            raise ImportError('mypycorrector dependencies are not fully installed, '
                              'they are required for statistical language model.'
                              'Please use "pip install kenlm" to install it.'
                              'if you are Win, Please install kenlm in cgwin.')
        t1 = time.time()
        # # 同音词
        self.word_similar = readjson(config.word_similar_path)
        # 词、频数dict
        self.char_freq = self.load_word_freq_dict(config.char_freq_path)
        self.custom_word_freq = {}

        detector_dict = DetectorDict()
        detector_dict.check_detector_dict_initialized()
        self.jieba_tokenizer = detector_dict.tokenizer
        self.word_freq = detector_dict.word_freq
        logger.debug('Loaded file: %s, spend: %s s' %
                        (config.word_freq_path, str(time.time() - t1)))
        self.initialized_detector = True

    def check_detector_initialized(self):
        if not self.initialized_detector:
            self.initialize_detector()

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

    def ngram_word_score(self, words):
        """
        取n元文法得分
        :param words: list, 以词切分
        :return:
        """
        self.check_detector_initialized()
        return self.lm_word.score(' '.join(words), bos=False, eos=False)# bos=False, eos=False

    def ppl_word_score(self, words):
        """
        取语言模型困惑度得分，越小句子越通顺
        :param words: list, 以词或字切分
        :return:
        """
        self.check_detector_initialized()
        return self.lm_word.perplexity(' '.join(words))

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
            if (maybe_err[begin_idx] >= err[begin_idx] and maybe_err[begin_idx] < err[end_idx]) or\
                (maybe_err[end_idx] > err[begin_idx] and maybe_err[end_idx] <= err[end_idx]):
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
    
    @staticmethod
    def is_filter_token(token):
        """
        是否为需过滤字词
        :param token: 字词
        :return: bool
        """
        result = False
        # pass blank
        if not token.strip():
            result = True
        # pass num
        if token.isdigit():
            result = True
        # pass alpha
        if is_alphabet_string(token.lower()):
            result = True
        # pass not chinese
        if not is_chinese_string(token):
            result = True
        return result

    def detect_word(self, sentence, maybe_errors):
        '''
        Descripttion: 使用词模型检测句子中的疑似错词信息，包括[词、位置、错误类型]
        param {*}
        return {*}
        '''
        if not sentence.strip() or sentence in PUNCTUATION_LIST:
            return maybe_errors
        # 初始化
        self.check_detector_initialized()
        try:
            tokens = self.jieba_tokenizer.tokenize(sentence)
            words = [token for token, begin_idx, end_idx in tokens]
            n = 3
            if len(words) < n:
                return maybe_errors
            scores = []
            for i in range(len(words) - n + 1):
                word = words[i:i + n]
                score = self.ngram_word_score(list(word))
                scores.append(score)
            # 移动窗口补全得分
            scores.insert(0, scores[0])
            scores.append(scores[-1])
            
            # 取疑似错字信息
            for i in self._get_maybe_error_index(scores,threshold=1.1):
                token = words[i]
                # pass filter word
                if self.is_filter_token(token):
                    continue
                if self.word_similar.get(token) != None:
                    # token, begin_idx, end_idx, error_type
                    maybe_err = [token, tokens[i][1], tokens[i][2], ErrorType.similar]
                    self._add_maybe_error_item(maybe_err, maybe_errors)
        except IndexError as ie:
            logger.warn("index error, sentence:" + sentence + str(ie))
        except Exception as e:
            logger.warn("detect error, sentence:" + sentence + str(e))
        return maybe_errors

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
        # # 文本归一化
        sentence = uniform(sentence)
        if sentence in PUNCTUATION_LIST:
            return []
        if self.is_word_error_detect:
            # 使用jieba分词，判断可能错词
            # 切词
            tokens = self.jieba_tokenizer.tokenize(sentence)
            # 未登录词加入疑似错误词典
            for token, begin_idx, end_idx in tokens:
                # pass filter word
                if self.is_filter_token(token):
                    continue
                # pass in dict
                if token not in self.word_freq:
                    maybe_err = [token, begin_idx, end_idx, ErrorType.word]
                    self._add_maybe_error_item(maybe_err, maybe_errors)

                else:
                    # 多字词或词频小于10000的单字，可能出现多字少字
                    if len(token) == 1 and token in self.char_freq and self.char_freq.get(token) < 10000:                                  
                        maybe_err = [token, begin_idx, end_idx, ErrorType.word_char]
                        self._add_maybe_error_item(maybe_err, maybe_errors)
                        continue
                    # 出现叠字，考虑是否多字
                    if len(token) == 1 and sentence[begin_idx - 1] == token:
                        maybe_err = [token, begin_idx, end_idx, ErrorType.redundancy]
                        self._add_maybe_error_item(maybe_err, maybe_errors)
            
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
                for i in self._get_maybe_error_index(sent_scores,threshold=1.9):
                    token = sentence[i]
                    # pass filter word
                    if self.is_filter_token(token):
                        continue
                    # token, begin_idx, end_idx, error_type
                    maybe_err = [token, i, i + 1, ErrorType.char]
                    self._add_maybe_error_item(maybe_err, maybe_errors)
            except IndexError as ie:
                logger.warn("index error, sentence:" + sentence + str(ie))
            except Exception as e:
                logger.warn("detect error, sentence:" + sentence + str(e))
            # 最后再使用词模型进行错误检测
            self.detect_word(sentence=sentence, maybe_errors=maybe_errors)
            maybe_errors = self._merge_detect(maybe_errors)
        return sorted(maybe_errors, key=lambda k: k[1], reverse=False)

    def _merge_detect(self, maybe_errors):
        maybe_errors = sorted(maybe_errors, key=lambda k: k[1], reverse=False)
        if maybe_errors == []:
            return []
        else:
            merge_maybe_errors = [maybe_errors[0]]
        for token, begin_idx, end_idx, err_type in maybe_errors[1:]:
            if err_type not in (ErrorType.similar, ErrorType.word_char, ErrorType.redundancy) and begin_idx == merge_maybe_errors[-1][2]:
                merge_maybe_errors[-1][0] += token
                merge_maybe_errors[-1][2] += len(token)
                merge_maybe_errors[-1][3] = 'merge'
            else:
                merge_maybe_errors.append([token, begin_idx, end_idx, err_type])
        return merge_maybe_errors



if __name__ == '__main__':
    d = Detector()
    err_sentences = [
        # '昨日下午，两江影视城民国街，毛泽东的扮演者贾云在时戏。重庆晨报记者高科摄',
        '《研学旅行服务规范》（LB/T 054-2016）、《红色旅游经典景区服务规范》（LB/T 055-2016）、《旅游电子商务企业基本信息规范》（LB/T 056-2016）、《旅游电子商务旅游产品和服务基本规范》（LB/T 057-2016）、《旅游电子商务电子合同基本信息规范》（LB/T 058-2016）、《会议服务机构经营与服务规范》（LB/T 059-2016）等6项行业标准已经国家旅游局批准，现予以公布，2017年5月1日起实施。',
        '崔永元早年为转基因视频问题论战',
        '皖水是一条大河，如果需要在和滩铺水泥建训练基地，需经安庆市水利局睡管科审批',
        '在提升区域旅游产业能寄过程中，运用信息技术，搭建相关产业融合共享的信息平台，形成以大运河文化为混、平台为先、联动为本的智慧旅游发展理念',
        '，'
    ]
    for sent in err_sentences:
        err = d.detect(sent)
        print("original sentence:{} => detect sentence:{}".format(sent, err))
