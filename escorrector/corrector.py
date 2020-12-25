'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 19:53:51
'''
# TODO 1、在语料中，加入成语、习语   2、过大语料中，发掘效果不太理想的原因
import os, sys, re
sys.path.insert(0, os.getcwd())
import time, heapq
import operator, Levenshtein
from typing import List
from escorrector.detector import Detector
from escorrector import config
from escorrector.utils.nlpir_tokenizer import tokenizer4IR
from escorrector.es_build.search import filter_msg, filter_phrase_msg
from escorrector.utils.lcs_utils import LCS
from escorrector.utils.text_utils import(
    split_2_short_text,
    get_correct_text,
    string_generalization,
    find_index_tokens
)


class Corrector(Detector):
    def __init__(self, language_model_path=config.language_model_path,
                    is_char_correct=True,
                    is_word_correct=False,
                    index_name=''):
        super(Corrector, self).__init__(language_model_path=language_model_path)
        self.name = 'corrector'
        self.is_char_correct = is_char_correct
        self.is_word_correct = is_word_correct
        self.index_name = index_name
        self.initialized_corrector = False

    def initialize_corrector(self):
        t1 = time.time()
        self.initialized_corrector = True

    def check_corrector_initialized(self):
        if not self.initialized_corrector:
            self.initialize_corrector()

    def get_candidates(self, msg, index_name=''):
        '''
        Descripttion: 针对可能错字，构建上下文，然后词组索引查询
        param {*}
        return {*}
        '''
        n = 2
        candidates={}
        for i in range(len(msg) - n + 1):
            word = msg[i:i + n]
            if isinstance(word, List):
                word = ''.join(word)
            # print(filter_phrase_msg('云在',index_name='corpus_generalization'))
            one_candidates={item['_source']['sentence']:item['_score'] for item in eval(filter_phrase_msg(word,index_name=self.index_name))}
            candidates = self._add_candidates(candidates=candidates, one_candidates=one_candidates)
        return sorted(candidates.items(), key=lambda item:item[1], reverse=True)

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
        candidates_list = heapq.nsmallest(5,final_candidates,key=lambda k: self.ppl_score(list(before_sent + k + after_sent)))
        corrected_item = min(candidates_list, key=lambda k: Levenshtein.distance(token, k))# LCS(token, k, result=[], istrack=False)
        return corrected_item

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
                token = sentence[begin_idx:end_idx]
                before_sent = sentence[:begin_idx]
                after_sent = sentence[end_idx:]
                # 以词为单位进行滑动窗口
                end_index += 1
                begin_window = begin_index - move_windows if begin_index - move_windows >= 0 else 0
                end_window = end_index + move_windows if end_index + move_windows < len(tokens_list) else len(tokens_list)
                seg_window = tokens_list[begin_window:end_window]
                candidates = self.get_candidates(seg_window,index_name=self.index_name)[:10]
                before_tokens = tokens_list[begin_window:begin_index]
                after_tokens = tokens_list[end_index:end_window]
                final_candidates = self.filter_candidates(candidates, token, before_tokens, after_tokens)
                corrected_item = self.es_correct_item(final_candidates, token, before_sent, after_sent)
                if corrected_item and corrected_item != token:
                    detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, err_type]
                    details.append(detail)
        details = sorted(details, key=operator.itemgetter(2))
        return details

  
if __name__ == '__main__':
    c = Corrector(is_char_correct=False,is_word_correct=True,index_name='corpus')
    err_sentences = [
        # '毛泽东的扮演者贾云在时戏',
        '如果需要在和滩铺水泥建训练基地',
        # '需经安庆市水利局睡管科审批',
        # '形成以大运河文化为混',
        # '联动为本的智慧旅游发展理念',
        # '昨日下午，两江影视城民国街，毛泽东的扮演者贾云在时戏。重庆晨报记者高科摄',
        # '皖水是一条大河，如果需要在和滩铺水泥建训练基地，需经安庆市水利局睡管科审批',
        # '在提升区域旅游产业能寄过程中，运用信息技术，搭建相关产业融合共享的信息平台，形成以大运河文化为混、平台为先、联动为本的智慧旅游发展理念',
        # '一本万李',
        '遇到逆竞时'
    ]
    for sent in err_sentences:
        details = c.correct(sent,details=[])
        correct_sent = get_correct_text(sent,details)
        print("original sentence:{} => correct sentence:{} =>details:{}".format(sent, correct_sent, details))
        