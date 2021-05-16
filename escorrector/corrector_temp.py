

import os, sys, re
sys.path.insert(0, os.getcwd())
import heapq, codecs
import operator
import numpy
from numpy import mean, exp, log, log10, sin, tanh,arctan
from escorrector.detector import Detector, ErrorType
from escorrector import config
from utils.ssc_utils import Filter_ssc
from utils.es_utils import filter_msg_regexp
from utils.logger import logger

from utils.text_utils import (
    _check_contain_error,
    split_2_short_text,
    get_correct_text,
    find_index_tokens,
    find_index_tokens_jieba,
    is_chinese_string
)

class CorrectorRegexp(Detector):
    def __init__(self, language_model_path=config.language_model_path,
                    hanzi_ssc_path=config.hanzi_ssc_path,
                    is_word_correct=True,
                    is_char_error_detect=True,
                    is_word_error_detect=True,
                    index_name=''):
        super(CorrectorRegexp, self).__init__(language_model_path=language_model_path,
                                        is_char_error_detect=is_char_error_detect,
                                        is_word_error_detect=is_word_error_detect)
        self.name = 'corrector'
        self.is_word_correct = is_word_correct
        self.index_name = index_name 
        self.hanzi_ssc_path = hanzi_ssc_path
        self.initialized_corrector = False

    @staticmethod
    def load_same_pinyin(path, sep='\t'):
        """
        加载同音字
        :param path:
        :param sep:
        :return:
        """
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists:" + path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(sep)
                if parts and len(parts) > 2:
                    key_char = parts[0]
                    same_pron_same_tone = set(list(parts[1]))
                    same_pron_diff_tone = set(list(parts[2]))
                    value = same_pron_same_tone.union(same_pron_diff_tone)
                    if key_char and value:
                        result[key_char] = value
        return result

    @staticmethod
    def load_same_stroke(path, sep='\t'):
        """
        加载形似字
        :param path:
        :param sep:
        :return:
        """
        result = dict()
        if not os.path.exists(path):
            logger.warn("file not exists:" + path)
            return result
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(sep)
                if parts and len(parts) > 1:
                    for i, c in enumerate(parts):
                        exist = result.get(c, set())
                        current = set(list(parts[:i] + parts[i + 1:]))
                        result[c] = exist.union(current)
        return result

    def initialize_corrector(self):
        # same pinyin
        self.same_pinyin = self.load_same_pinyin(config.same_pinyin_path)
        # same stroke
        self.same_stroke = self.load_same_stroke(config.same_stroke_path)
        self.ssc_util = Filter_ssc(self.hanzi_ssc_path)
        self.initialized_corrector = True

    def check_corrector_initialized(self):
        if not self.initialized_corrector:
            self.initialize_corrector()

    def get_regexp_candidates(self, msg, before_token, after_token):
        '''
        Descripttion: 利用正则查询找到候选集
        param {*}
        return {*}
        '''
        # 候选句子
        candidates_sent = {}
        # 候选词语
        candidates_word = {}

        if not is_chinese_string(before_token):
            before_token = ''
        if not is_chinese_string(after_token):
            after_token = ''
        for i in range(len(msg)):
            one_candidates = {}
            try:
                regexp = before_token + msg[:i] + '.{1,1}' + msg[i + 1:] + after_token + '.*'
                one_candidates = {item['_source']['keyword']: item['_source']['count'] for item in eval(filter_msg_regexp(regexp, index_name=self.index_name))}
            except Exception as e:
                print(e)
            candidates_sent.update(one_candidates)

        for candidate, count in candidates_sent.items():
            word = candidate[len(before_token):len(before_token) + len(msg)]
            if candidates_word.get(word) == None:
                candidates_word[word] = count
            else:
                candidates_word[word] += count
        return dict(sorted(candidates_word.items(), key=lambda item: item[1], reverse=True))

    def get_regexp_candidates_similar(self, token, before_token, after_token, index_name=''):
        '''
        Descripttion: 利用正则查询找到候选集
        param {*}
        return {*}
        '''
        # 候选句子
        candidates_sent = {}
        # 候选词语
        candidates_word = {}
        # 正则查询
        try:
            regexp = before_token + '.{2,2}' + after_token + '.*'
            candidates_sent = {item['_source']['keyword']: item['_source']['count'] for item in eval(filter_msg_regexp(regexp, index_name=self.index_name))}
        except Exception as e:
            pass
        if candidates_sent == {}:
            return {}
        # 从句子中得到候选词
        for candidate, count in candidates_sent.items():
            word = candidate[len(before_token):len(before_token) + 2]
            if candidates_word.get(word) == None:
                candidates_word[word] = count
            else:
                candidates_word[word] += count
        return dict(sorted(candidates_word.items(), key=lambda item: item[1], reverse=True))            

    def get_regexp_candidates_wordchar(self, token, before_token, after_token, index_name=''):
        '''
        Descripttion: 针对可能多字少字，利用上下文，正则查询
        param {*}
        return {*}
        '''
        # 候选句子
        candidates_sent = {}
        # 候选词语
        candidates_word = {}
        # 正则查询
        try:
            regexp = before_token + '.{0,2}' + after_token + '.*'
            candidates_sent = {item['_source']['keyword']: item['_source']['count'] for item in eval(filter_msg_regexp(regexp, index_name=self.index_name))}
        except Exception as e:
            pass
        if candidates_sent == {}:
            return {}
        # 从句子中得到候选词
        re_str = re.compile(before_token + '.{0,2}' + after_token)
        for candidate, score in candidates_sent.items():
            matched_str = re.finditer(re_str, candidate)
            if matched_str:
                for match_item in matched_str:
                    word = match_item.group().replace(before_token,'').replace(after_token,'')
                    if candidates_word.get(word) == None:
                        candidates_word[word] = score
                    else:
                        candidates_word[word] += score
        return dict(sorted(candidates_word.items(), key=lambda item: item[1], reverse=True))

    def filter_items_new(self, word, candidates:dict, n=10):
        '''
        @Descripttion: 根据相似度loss，从候选集中，直接过滤掉不相关的候选，减少误纠情况
        @param {*}
        @return {*}
        '''
        res_candidates = {}
        for candidate_word, count in candidates.items():
            sound_loss_max, shape_loss_max = self.ssc_util.computer_ssc_word_loss(word, candidate_word)
            if res_candidates.get(candidate_word) == None:
                res_candidates[candidate_word] = {}
                res_candidates[candidate_word]['sound_loss'] = sound_loss_max
                res_candidates[candidate_word]['shape_loss'] = shape_loss_max
                res_candidates[candidate_word]['loss'] = min(sound_loss_max, shape_loss_max)

        res_candidates = {candidate_word: loss_dict for candidate_word, loss_dict in res_candidates.items() if loss_dict['sound_loss'] < 0.4 or loss_dict['shape_loss'] <= 0.25}
        return dict(sorted(res_candidates.items(), key=lambda item: item[1]['loss'], reverse=False))

    def filter_item_similar(self, word, final_candidates):
        '''
        Descripttion: 针对similar错误进行精准粗筛
        param {*}
        return {*}
        '''
        candidates_similar = {}
        word_similars = self.word_similar.get(word)
        word_similars = [word for word, freq in word_similars]
        for candidate, score in final_candidates.items():
            if candidate in word_similars:
                candidates_similar[candidate] = {}
                candidates_similar[candidate]['loss'] = 0
        return candidates_similar       

    def filter_items_wordchar(self, char, final_candidates):
        '''
        Descripttion: 针对可能多字少字进行粗筛过滤
        param {*}
        return {*}
        '''  
        candidates = {}
        sound_set = self.same_pinyin.get(char)
        shape_set = self.same_stroke.get(char)
        sound_set = {} if sound_set == None else sound_set
        shape_set = {} if shape_set == None else shape_set
        for candidate_word, freq in final_candidates.items():
            if len(candidate_word) == 1:
                if candidate_word in sound_set or candidate_word in shape_set:
                    candidates[candidate_word] = freq
            else:    
                if candidate_word == '' or char in candidate_word:
                    candidates[candidate_word] = freq
        return dict(sorted(candidates.items(), key=lambda item: item[1], reverse=True))

    def es_correct_item_ppl(self, final_candidates, token, before_sent, after_sent, n=1):
        '''
        Descripttion: 利用ppl来精排
        param {*}
        return {*}
        '''
        final_candidates = list(final_candidates.keys())
        if token not in final_candidates:
            final_candidates.append(token)
        candidates_list = heapq.nsmallest(n, final_candidates, key=lambda k: self.ppl_score(list(before_sent + k + after_sent)))
        # corrected_item = min(final_candidates, key=lambda k: self.ppl_score(list(before_sent + k + after_sent)))
        return candidates_list

    def es_correct_item_score(self, token, candidates_ssc, candidates_search, before_sent, after_sent):
        '''
        @Descripttion: 利用计算得到的分数进行精排
        @param {*}
        @return {*}
        '''
        if not candidates_ssc:
            return token
        # 判断token
        if candidates_ssc.get(token) == None:
            candidates_ssc[token] = {}
            candidates_ssc[token]['loss'] = 0
        if candidates_search.get(token) == None:
            candidates_search[token] = 1

        candidates_keys = list(candidates_ssc.keys())
        counts = [candidates_search[candidate] for candidate in candidates_keys]
        max_count = max(counts)
        ppls = [self.ppl_score(list(before_sent + k + after_sent)) for k in candidates_keys]
        ppl_origin = self.ppl_score(list(before_sent + token + after_sent))
        corrected_item = max(candidates_keys, key=lambda k: self.computer_score(\
            1 - candidates_ssc[k]['loss'], \
            log10(candidates_search[k] + 1) / log10(max_count + 1), \
            ppl_origin - ppls[candidates_keys.index(k)]))
        return corrected_item

    def _normalization(self, lis):
        '''
        对得到的列表中间数据中，四个数字，进行归一化操作,Z-score标准化方法
        :param lis: 列表数据
        :return: 归一化后的结果(列表)
        '''
        arr = numpy.array(lis)
        max_data = max(arr)
        min_data = min(arr)
        arr = list((arr - min_data + 1) / (max_data - min_data + 1))   #向量转换为列表
        return arr

    def computer_score(self,ssc_ratio,count_ratio,ppl_increment):
        '''
        @Descripttion: 
        @param {*}
        @return {*}
        '''
        # TODO 公式修润，返回结果有时候并不理想
        # return (sin(ssc_ratio*2/3.1415928) * tanh(count)) / (log(ppl))
        # return (ssc_ratio * tanh(count)) / (log(ppl))
        # return (ssc_ratio * count_ratio)/ppl_ratio
        # return 0.9 * ssc_ratio + 0.03 * count_ratio + 0.07 * (1 - ppl_ratio)
        # if ppl_increment <= 0:
        #     ppl_increment = 0.001
        return ssc_ratio * ppl_increment + 0.1 * count_ratio

    def similar_word_correct_item(self, token, candidates, before_sent, after_sent):
        '''
        Descripttion: 精排，找出最佳候选
        param {*}
        return {*}
        '''
        if token not in candidates:
            candidates.append(token)
        return min(candidates, key=lambda k: self.ppl_word_score(self.jieba_tokenizer.jieba_cut(before_sent + k + after_sent)))
    
    def correct(self, text, details=[], right_text=''):
        """
        句子改错
        :param text: 句子文本
        :return: 改正后的句子, list(wrong, right, begin_idx, end_idx)
        """
        # 长句切分为短句
        blocks = split_2_short_text(text, include_symbol=True)
        for blk, idx in blocks:
            details = self.correct_short(blk, start_idx=idx, details=details,right_text=right_text)
        return details

    def correct_short(self, sentence, start_idx=0, details=[],right_text=''):
        self.check_corrector_initialized()
        self.check_detector_initialized()
        if self.is_word_correct:
            # 使用语言模型得分
            tokens_jieba = self.jieba_tokenizer.tokenize(sentence)
            if len(sentence) == 1:
                return details
            maybe_errors = self.detect(sentence)
            for token, begin_idx, end_idx, err_type in maybe_errors:
                # 如果错误已经包含
                if _check_contain_error([token, begin_idx + start_idx, end_idx + start_idx], details):
                    continue
                before_sent = sentence[:begin_idx]
                after_sent = sentence[end_idx:]
                if err_type == ErrorType.similar:
                    # 同音同义词校对
                    begin_index, end_index = find_index_tokens_jieba(tokens_jieba, begin_idx, end_idx)
                    if begin_index == 0:
                        before_token = ''
                        after_token = tokens_jieba[end_index + 1][0] + tokens_jieba[end_index + 2][0] if end_index + 2 < len(tokens_jieba) else tokens_jieba[end_index][0]
                    elif end_index + 1 == len(tokens_jieba):
                        after_token = ''
                        before_token = tokens_jieba[begin_index - 2][0] + tokens_jieba[begin_index - 1][0] if begin_index - 2 >=0 else tokens_jieba[begin_index][0]
                    else:
                        before_token = tokens_jieba[begin_index - 1][0] if begin_index != 0 else ''
                        after_token = tokens_jieba[end_index + 1][0] if end_index + 1 != len(tokens_jieba) else ''
                    # 根据该词的前后各一个词来检索该词
                    candidates_search = self.get_regexp_candidates_similar(token, before_token,after_token)
                    # 粗筛
                    candidates_similar = self.filter_item_similar(token, candidates_search)
                    candidates = self.filter_items_new(token, candidates_search)
                    candidates.update(candidates_similar)
                   
                    # score 精排
                    corrected_item = self.es_correct_item_score(token, candidates, candidates_search, before_sent, after_sent)
                    if corrected_item and corrected_item != token and is_chinese_string(corrected_item):
                        detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'regex']
                        details.append(detail)
                elif err_type == ErrorType.word_char:
                    # 可能多字少字
                    begin_index, end_index = find_index_tokens_jieba(tokens_jieba, begin_idx, end_idx)
                    if begin_index == 0:
                        before_token = ''
                        after_token = tokens_jieba[end_index + 1][0] + tokens_jieba[end_index + 2][0] if end_index + 2 < len(tokens_jieba) else tokens_jieba[end_index][0]
                    elif end_index + 1 == len(tokens_jieba):
                        after_token = ''
                        before_token = tokens_jieba[begin_index - 2][0] + tokens_jieba[begin_index - 1][0] if begin_index - 2 >=0 else tokens_jieba[begin_index][0]
                    else:
                        before_token = tokens_jieba[begin_index - 1][0] if begin_index != 0 else ''
                        after_token = tokens_jieba[end_index + 1][0] if end_index + 1 != len(tokens_jieba) else ''
                    # 根据该词的前后各一个词来检索该词
                    candidates_search = self.get_regexp_candidates_wordchar(token, before_token,after_token)
                    # 粗筛
                    candidates = self.filter_items_wordchar(token, candidates_search)
                    # # ppl精排
                    corrected_item = self.es_correct_item_ppl(candidates, token, before_sent, after_sent)[0]
                
                    if corrected_item != token and is_chinese_string(corrected_item):
                        if len(corrected_item) > len(token):
                            detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'lack']
                        elif len(corrected_item) < len(token):
                            detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'redundancy']
                        else:
                            detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'regex']
                        details.append(detail)
                elif err_type == ErrorType.redundancy:
                    # 可能多字
                    candidates = {'': 1}
                    # # ppl精排
                    corrected_item = self.es_correct_item_ppl(candidates, token, before_sent, after_sent)[0]
                    if corrected_item != token and is_chinese_string(corrected_item):
                        if corrected_item=='':
                            detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'redundancy']
                        else:
                            detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'regex']
                        details.append(detail)
                else:
                    before_token = ''
                    after_token = ''
                    # 找到token对应分词后的begin_index, end_index
                    begin_index, end_index = find_index_tokens_jieba(tokens_jieba, begin_idx, end_idx)
                    # 对begin_idx, end_idx, token重赋值
                    if begin_index == 0:
                        before_token = ''
                        after_token = tokens_jieba[end_index + 1][0] + tokens_jieba[end_index + 2][0] if end_index + 2 < len(tokens_jieba) else tokens_jieba[end_index][0]
                    elif end_index + 1 == len(tokens_jieba):
                        after_token = ''
                        before_token = tokens_jieba[begin_index - 2][0] + tokens_jieba[begin_index - 1][0] if begin_index - 2 >=0 else tokens_jieba[begin_index][0]
                    else:
                        before_token = tokens_jieba[begin_index - 1][0] if begin_index != 0 else ''
                        after_token = tokens_jieba[end_index + 1][0] if end_index + 1 != len(tokens_jieba) else ''
                   
                    if not is_chinese_string(before_token + token + after_token):
                        continue
                    before_sent = sentence[:begin_idx]
                    after_sent = sentence[end_idx:]
                    
                    # 基于检索，找到可能候选集
                    candidates_search = self.get_regexp_candidates(token, before_token=before_token, after_token=after_token)
                    # 基于音码、形码粗筛
                    candidates = self.filter_items_new(token, candidates_search)

                    corrected_item = self.es_correct_item_score(token, candidates, candidates_search, before_sent, after_sent)
                    if corrected_item and corrected_item != token and is_chinese_string(corrected_item):
                        detail = [token, corrected_item, begin_idx + start_idx, end_idx + start_idx, 'regex']
                        details.append(detail)
        details = sorted(details, key=operator.itemgetter(2))
        return details

if __name__ == '__main__':
    c = CorrectorRegexp(index_name='4-ngram-count')
    err_sentences = [
        # '云南省无新曾本土确镇病例和无症状感染者',
        '现做现发货',
        '记者从全国总工会今天召开的2021年“五一”新闻发布会上获悉',
        '更加组重打出政策“组合拳”为企业减轻税负',
        '推动中波全面战略伙伴关系向更高水平发展。',
        '制定一部保护黄河的良法',
        # '勒令其在4月20日前离境',
        # '（互联网信息）俄罗斯宣布驱逐20名捷克外交人员',
        # '以汉字为书写在体的中文是中华文明的智慧结晶',
        '人数与大使馆的当地雇员人员相等',
        # '黄河保护立法要贯彻习近平生态文明思想',
        '毗邻区两地城管将针对乱张贴',
        '旨在情祝多种语言以及文化多样性',
        '可是就在我读到孙中山的转记时',
        '如令他还活得好好的',
        '音发网络安全问题',
        '令天突然冷了起来',
        '无法天天都是晴天',
        '当你一但经历和刻服了这些关卡时',
        '有的人一辈子都很好命',
        '于网路上疯传',
        '在网路上疯传',
        '毛泽东的扮演者贾云在时戏',
        '如果需要在和滩铺水泥建训练基地',
        # '需经安庆市水利局睡管科审批',
        # '形成以大运河文化为混',
        # '联动为本的智慧旅游发展理念',
        # '昨日下午，两江影视城民国街，毛泽东的扮演者贾云在时戏。重庆晨报记者高科摄',
        # '皖水是一条大河，如果需要在和滩铺水泥建训练基地，需经安庆市水利局睡管科审批',
        # '在提升区域旅游产业能寄过程中，运用信息技术，搭建相关产业融合共享的信息平台，形成以大运河文化为混、平台为先、联动为本的智慧旅游发展理念',
        # '我们出去抓蝴',
        # '寻衅滋亊罪和敲诈勒索罪已成为腐败官员利用公权力打击访民的专利。',
        # "郭台铭也是完胜国、民两党及无党藉所有台面上的人物",
        # '依旧是指标不治本',
        '我们出去抓蝴蝴蝶',
        # '还想了解他曾做过什么以及当时正在做其么',
        # '切尔诺贝利核电站在1986年发上爆炸事故',
        # '工人与商业正确自由与公平的贸易环境',
        # '崔永元早年为转基因视频问题论战',
        # '风雨过后，改变了许多景象，狂风造成的树木倒塔等，但面对阳光时又是一番新的气象。遇到无法必免的挫败，是否可以把它变成转捩点，只能靠你自己。',
        # '何只是有国才有家',
        # '部分台湾学生抗议马英九政府与大陆签订《海峡两岸服务贸易协议》',
        # '依旧是指标不治本',
        # '从网民提供的图照上观察',
        # '令天突然冷了起来，妈妈丛相子里番出一件旧棉衣让我穿上。我不原意。她在妈妈得说服叫育下，我中于穿上哪件棉衣哼着哥儿上学去了。',
        # '在次',
        # '能让企业门转移注目',
        # '以前战争时代没什么医料设备像现在那么普遍，但一口家庭生孩子的比率增多，相反地死亡的数量也更多。',
        # '一本万李',
        # '遇到逆竞时',
        # '坐路差不多十分钟，我们到了。',
        # '没了声音他能怎么辨',
        # '从小，我父母的工作就很忙录。',
        # '当你一但经历和刻服了这些关卡时，就是你张开双手迎接成功的时候。',
        # '但是发生了想不道的事，也有可能一生都很辛苦，可是有一天他却过着福有的生活。',
        # '经过了一场风雨澈底的改变了他的命运，也使他的耳朵渐渐的听不到了。',
        # '更明确规定“一带一路倡议”的内容',
        # '有钱又权有背景有关系',
        # '我曾去过云南文山洲',
        # '最后获得的才是胜力的强者。',
        # '防护系统不段的升级',
        # '统一采购、统一分配很容易产生污腐。',
        # '但是努力的人种比不努力的人还要有成就吧！',
        # '事后它依然安然无样得坐在那儿。',
        # '反正，都己发生了，只是个糟遇罢了。',
    ]
    for sent in err_sentences:
        details = c.correct(sent,details=[])
        correct_sent = get_correct_text(sent,details)
        print("original sentence:{} => correct sentence:{} =>details:{}".format(sent, correct_sent, details))
    s = '俄罗斯宣布驱逐20名捷克外交人员'
