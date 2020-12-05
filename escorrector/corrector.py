'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 19:53:51
'''
import os, sys
sys.path.insert(0, os.getcwd())
from escorrector.detector import Detector
from escorrector import config
from escorrector.es_build.search import filter_msg
from escorrector.utils.text_utils import split_2_short_text

class Corrector(Detector):
    def __init__(self, language_model_path=config.language_model_path,):
        super(Corrector, self).__init__(language_model_path=language_model_path)
        self.name = 'corrector'
        self.initialized_corrector = False

    def initialize_corrector(self):
        t1 = time.time()
        self.filter_msg = filter_msg
        self.initialized_corrector = True

    def check_corrector_initialized(self):
        if not self.initialized_corrector:
            self.initialize_corrector()

    def correct(self, text, reverse=True):
        """
        句子改错
        :param sentence: 句子文本
        :return: 改正后的句子, list(wrong, right, begin_idx, end_idx)
        """
        # 长句切分为短句
        blocks = split_2_short_text(text, include_symbol=True)
        for blk, idx in blocks:
            self.correct_short(blk, start_idx=idx)
        # return details

    def correct_short(self, sentence, start_idx=0):
        if self.is_char_error_detect:
            maybe_errors = self.detect(sentence)
            move_windows = 2
            for token, begin_idx, end_idx, err_type in maybe_errors:
                begin_window = begin_idx - move_windows if begin_idx >= move_windows else 0
                end_window = end_idx + move_windows if end_idx + move_windows < len(sentence) else len(sentence)
                seg_window = sentence[begin_window:end_window]
                print(self.filter_msg(seg_window))


if __name__ == '__main__':
    c = Corrector()
    err_sentences = [
        '毛泽东的扮演者贾云在时戏',
        '如果需要在和滩铺水泥建训练基地',
        '需经安庆市水利局睡管科审批'
        '形成以大运河文化为混'
        '联动为本的智慧旅游发展理念'
    ]
    for sent in err_sentences:
        c.correct_short(sent)
        # print("original sentence:{} => detect sentence:{}".format(sent, err))