'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
@Date: Do not edit
'''
import os, sys, re
sys.path.insert(0, os.getcwd())
import time, heapq
import operator, Levenshtein
from typing import List
from escorrector.detector import Detector
from escorrector import config
from escorrector.utils.nlpir_tokenizer import tokenizer4IR
from escorrector.es_build.search import filter_msg, filter_phrase_msg, filter_msg_regexp
from escorrector.utils.lcs_utils import LCS
from escorrector.utils.ssc_utils import compute_equal_rate
from escorrector.utils.text_utils import(
    split_2_short_text,
    get_correct_text,
    string_generalization,
    find_index_tokens
)

class Corrector(Detector):
    def __init__(self, language_model_path=config.language_model_path,
                    hanzi_ssc_path=config.hanzi_ssc_path,
                    is_char_correct=True,
                    is_word_correct=False,
                    index_name=''):
        super(Corrector, self).__init__(language_model_path=language_model_path)
        self.name = 'corrector'
        self.is_char_correct = is_char_correct
        self.is_word_correct = is_word_correct
        self.index_name = index_name
        self.hanziSSCDict = self._getHanziSSCDict(hanzi_ssc_path)
        self.initialized_corrector = False

    def initialize_corrector(self):
        t1 = time.time()
        self.initialized_corrector = True

    def check_corrector_initialized(self):
        if not self.initialized_corrector:
            self.initialize_corrector()

    def _getHanziSSCDict(self, hanzi_ssc_path):
        hanziSSCDict = {}#汉子：SSC码
        with open(hanzi_ssc_path, 'r', encoding='UTF-8') as f:#文件特征：U+4EFF\t仿\t音形码\n
            for line in f:
                line = line.split()
                hanziSSCDict[line[1]] = line[2]
        return hanziSSCDict
        
    def get_regexp_candidates(self, msg, index_name=''):
        '''
        Descripttion: 利用正则查询找到候选集
        param {*}
        return {*}
        '''
        # 候选句子
        candidates = {}
        # 候选词语
        final_candidates = {}
        for i in range(len(msg)):
            regexp = '.*' + msg[:i] + '.{1,1}' + msg[i + 1:] + '.*'
            one_candidates = {item['_source']['sentence']: item['_score'] for item in eval(filter_msg_regexp(regexp, index_name=self.index_name))}
            # 从句子中得到候选词
            re_str = re.compile(msg[:i] + '.{1,1}' + msg[i + 1:])
            for candidate, score in one_candidates.items():
                matched_str = re.finditer(re_str, candidate)
                if matched_str:
                    for match_item in matched_str:
                        final_candidate = match_item.group()
                        if abs(len(final_candidate) - len(msg) <= 2):
                            if final_candidates.get(final_candidate) == None:
                                final_candidates[final_candidate] = score
                            else:
                                final_candidates[final_candidate] += score
            # candidates = self._add_candidates(candidates=candidates, one_candidates=one_candidates)
        return sorted(final_candidates.items(), key=lambda item: item[1], reverse=True)            

    def _add_candidates(self, candidates={}, one_candidates={}):
        '''
        Descripttion: 对索引出的结果进行聚合
        param {*}
        return {*}
        '''
        for sent, score in one_candidates.items():
            if candidates.get(sent) == None:
                candidates[sent] = score
            else:
                candidates[sent] += score
        return candidates

    def filter_candidates(self, candidates_score, token, before_tokens, after_tokens):
        '''
        Descripttion: 针对错误字词可能上下文进行过滤
        param {*}
        return {*}
        '''
        final_candidates = []
        if isinstance(before_tokens, List):
            before_tokens = ''.join(before_tokens)
        if isinstance(after_tokens, List):
            after_tokens = ''.join(after_tokens)
        re_str = re.compile('(%s)[\u4E00-\u9FD5]+(%s)' % (before_tokens, after_tokens))
        for candidate, score in candidates_score:
            matched_str = re.finditer(re_str, candidate)
            if matched_str:
                for match_item in matched_str:
                    final_candidate = match_item.group().replace(before_tokens, '').replace(after_tokens, '')
                    # print(final_candidate)
                    if abs(len(final_candidate) - len(token) <= 2):
                        final_candidates.append(final_candidate)
        return final_candidates

    # TODO 考虑损失，即（编辑距离、音形相似度）
    # Done 编辑距离
    def es_correct_item(self, final_candidates, token, before_sent, after_sent):
        '''
        Descripttion: 候选集选择
        param {*}
        return {*}
        '''
        candidated_item = None
        if not final_candidates:
            return None
        candidates_list = heapq.nsmallest(5,final_candidates,key=lambda k: self.ppl_score(list(before_sent + k[0] + after_sent)))
        # corrected_item = min(candidates_list, key=lambda k: Levenshtein.distance(token, k[0]))# LCS(token, k, result=[], istrack=False)
        corrected_item = max(candidates_list, key=lambda k: compute_equal_rate(self.get_word_ssc(token),self.get_word_ssc(k[0])))
        return corrected_item

    def get_word_ssc(self, word):
        '''
        Descripttion: 返回字符串的音形码
        param {*}
        return {*}
        '''
        ssc=''
        for char in word:
            if self.hanziSSCDict.get(char) == None:
                ssc += '0' * 11
            else:
                ssc += self.hanziSSCDict.get(char)
        return ssc

    def correct(self, text, details=[]):
        """
        句子改错
        :param sentence: 句子文本
        :return: 改正后的句子, list(wrong, right, begin_idx, end_idx)
        """
        # 长句切分为短句
        blocks = split_2_short_text(text, include_symbol=True)
        for blk, idx in blocks:
            details = self.correct_short(blk, start_idx=idx, details=details)
        return details

    def correct_short(self, sentence, start_idx=0, details=[]):
        self.check_corrector_initialized()
        if self.is_char_correct:
            maybe_errors = self.detect(sentence)
            move_windows = 2
            for token, begin_idx, end_idx, err_type in maybe_errors:
                before_sent = sentence[:begin_idx]
                after_sent = sentence[end_idx:]
                begin_window = begin_idx - move_windows if begin_idx >= move_windows else 0
                end_window = end_idx + move_windows if end_idx + move_windows < len(sentence) else len(sentence)
                seg_window = sentence[begin_window:end_window]
                candidates = self.get_candidates(seg_window, index_name=self.index_name)[:10]
                before_tokens = sentence[begin_window:begin_idx]
                after_tokens = sentence[end_idx:end_window]
                final_candidates = self.filter_candidates(candidates, token, before_tokens, after_tokens)
                corrected_item = self.es_correct_item(final_candidates, token, before_sent, after_sent)
                if corrected_item and corrected_item != token:
                    detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, err_type]
                    details.append(detail)
        elif self.is_word_correct:
            tokens_nlpir = tokenizer4IR(sentence)
            if tokens_nlpir == None:
                    return []
            # tokens_list = string_generalization(sentence)
            tokens_list = [item['text'] for item in tokens_nlpir]
            maybe_errors = self.detect(sentence)
            move_windows = 2
            for token, begin_idx, end_idx, err_type in maybe_errors:
                # 找到token对应分词后的begin_index, end_index
                begin_index, end_index = find_index_tokens(tokens_nlpir, begin_idx, end_idx)
                # 对begin_idx, end_idx, token重赋值
                begin_idx = tokens_nlpir[begin_index]['begin']
                end_idx = tokens_nlpir[end_index]['end']
                # 如果token长度太小，向前后各移一位
                if end_idx - begin_idx <= 2:
                    begin_idx = begin_idx - 1 if begin_idx - 1 >= 0 else 0
                    end_idx = end_idx + 1 if end_idx + 1 < len(sentence) else len(sentence)
                token = sentence[begin_idx:end_idx]
                before_sent = sentence[:begin_idx]
                after_sent = sentence[end_idx:]
                
                candidates = self.get_regexp_candidates(token,index_name=self.index_name)
                corrected_item = self.es_correct_item(candidates, token, before_sent, after_sent)
                if corrected_item and corrected_item[0] != token:
                    detail = [token, corrected_item[0], begin_idx + start_idx, end_idx + start_idx, err_type]
                    details.append(detail)
        details = sorted(details, key=operator.itemgetter(2))
        return details

if __name__ == '__main__':
    c = Corrector(is_char_correct=False,is_word_correct=True,index_name='no_genera_people14_sighan_test')
    err_sentences = [
        # '毛泽东的扮演者贾云在时戏',
        # '如果需要在和滩铺水泥建训练基地',
        # '需经安庆市水利局睡管科审批',
        # '形成以大运河文化为混',
        # '联动为本的智慧旅游发展理念',
        # '昨日下午，两江影视城民国街，毛泽东的扮演者贾云在时戏。重庆晨报记者高科摄',
        # '皖水是一条大河，如果需要在和滩铺水泥建训练基地，需经安庆市水利局睡管科审批',
        # '在提升区域旅游产业能寄过程中，运用信息技术，搭建相关产业融合共享的信息平台，形成以大运河文化为混、平台为先、联动为本的智慧旅游发展理念',
        # '一本万李',
        # '遇到逆竞时',
        # '坐路差不多十分钟，我们到了。',
        # '没了声音他能怎么辨',
        # '从小，我父母的工作就很忙录。',
        # '当你一但经历和刻服了这些关卡时，就是你张开双手迎接成功的时候。',
        # '但是发生了想不道的事，也有可能一生都很辛苦，可是有一天他却过着福有的生活。',
        # '经过了一场风雨澈底的改变了他的命运，也使他的耳朵渐渐的听不到了。',
        '但是努力的人种比不努力的人还要有成就吧！',
        '事后它依然安然无样得坐在那儿。',
        '反正，都己发生了，只是个糟遇罢了。'
    ]
    for sent in err_sentences:
        details = c.correct(sent,details=[])
        correct_sent = get_correct_text(sent,details)
        print("original sentence:{} => correct sentence:{} =>details:{}".format(sent, correct_sent, details))
    candidates = c.get_regexp_candidates(msg='很忙录', index_name='no_genera_people14_sighan_test')
    # print(candidates)

  