'''
Descripttion: 
version: 
Author: nlpir team
Date: 2020-08-08 10:20:49
LastEditors: cjh
LastEditTime: 2020-09-13 15:39:31
'''
import sys, os
import time
from threading import Thread
sys.path.insert(0, os.getcwd())

from nlpir047.corrector_dict.corrector_dict import CorrectorDict
from nlpir047.utils.corrector_utils.get_corrector_text_utils import get_correct_text
correctorDict = CorrectorDict()
correctorDict.check_detector_dict_initialized()

class MyThread(Thread):
    def __init__(self, sentence, start_idx):
        Thread.__init__(self)
        self.sentence = sentence
        self.start_idx = start_idx

    def run(self):
        self.pred_details = correctorDict.correct_dict_short(self.sentence, self.start_idx)
        
    def get_result(self):
        return self.pred_details

def correct_dict_multi_thread(text, thread_max_count=10):
    text_new = ''
    details = []
    blocks = correctorDict.split_2_short_text(text, include_symbol=True)
    blocks_list = list()
    for i in range(0, len(blocks), thread_max_count):
        blocks_list.append(blocks[i:i + thread_max_count])
    for block in blocks_list:
        pred_details = block_correct_dict_multi_thread(block, thread_max_count)
        details.extend(pred_details)
    text_new = get_correct_text(text, details)
    return text_new, details
    
def block_correct_dict_multi_thread(block, thread_max_count):
    threads_list = []
    details = []
    for blk, start_idx in block:
        threads_list.append(MyThread(blk, start_idx))

    for thread in threads_list:
        thread.start()

    for thread in threads_list:
        thread.join()
        pred_details = thread.get_result()
        details.extend(pred_details)
    return details

if __name__ == '__main__':
    text = '（香港综合讯）香港大学校务委员会昨天（7月28日）在一项会议上以大比数通过解雇“占中三子”之一、法律系副教授戴耀廷。戴耀廷事后指该决定“是由大学以外的势力透过它的代理人作出”，香港中联办则大赞有关决定是“惩恶扬善、顺应民心的正义之举”。\
            据香港01报道，校委会是18比2通过即时解雇戴耀廷的决定。校委会本科生代表成员李梓成昨天受访时基于保密理由表示不便透露投票情况，但直言对会议结果感到失望及愤怒，并说成员当中有不同观点，例如要求等候戴的上诉结果再作决定，他也赞成相关建议，但校委会最终决定就戴耀廷去留的议案付诸表决。\
            戴耀廷担任香港大学法律系副教授多年，曾在2000年至2008年出任法律学院副院长。因倡导2014年的占中运动争取香港真普选，他去年以“串谋犯公众妨扰罪”“煽惑他人犯公众妨扰罪”被判监16个月，其后获准保释等候上诉。\
            港大去年6月成立“探讨充分解雇理由委员会”，处理戴耀廷的教席问题。校方早前启动调查程序，并于昨天的校务委员会例会上，决定戴耀廷的去留。\
            戴耀廷昨晚在面簿发表声明，指“辞退我的决定，并不是由香港大学，而是由大学以外的势力透过它的代理人作出”。\
            他认为，此事标志着香港学术自由的终结，“香港学术机构的教研人员，再难自由地对公众，就一些政治或社会争议事情，发表具争议的言论。香港的学术机构再不能保护其成员免受内部及外在的干预”。\
            他说，若仍有疑问“一国一制”是否已降临香港，“我的个案应足以释疑”。他也说：“当目睹所爱的大学沉沦，我感到心痛。不过，我会以另外的身份继续法治的研究及教学工作，也不会停止为香港的法治而战。”\
            除了是占中运动发起人之一，戴耀廷倡导的公民抗命、违法达义等理念都不见容于北京。他针对去年区议会选举提出的风云计划，针对今年立法会选举提出的雷动计划，均被中国官媒斥为港版“颜色革命”、夺权阴谋等。\
            香港中联办昨晚就在官网发文称港大的决定是“惩恶扬善、顺应民心的正义之举”，净化大学正常教学秩序和教学环境，坚定捍卫大学之道，对香港社会整体利益高度负责，维护社会公义。\
            香港昨天（7月27日）新增145起冠病确诊病例，再破单日新高。香港特区政府宣布四项抗疫紧缩措施，包括餐馆全天禁止堂食、“限聚令”由四人收紧至两人，以及室内室外公共场所都强制戴口罩等。\
            “禁堂食令”“限聚令”“戴口罩令”及体育场所及泳池暂时关闭等措施，自明天凌晨起生效，为期7天至8月4日。港府同时呼吁雇主容许雇员在家工作，市民减少聚会和去市场买菜。\
            据《明报》报道，香港卫生防护中心传染病处主任张竹君昨天在记者会公布，在昨天新增确诊病例中，142起属于本土病例，其余为输入病例。在本土确诊病例中，59起源头不明。这也是香港连续第六天确诊病例数量破百起，目前累计确诊病例达到2778起。\
            政务司长张建宗坦言，第三波疫情严峻，在社区大规模暴发的风险非常高。他说，“过去14天香港新增逾千宗病例，是之前的总和。”不少源头不明，而不同群组、行业都出现病例，范围广泛，难以消除隐形传播链，所以港府一定要严阵以待。\
            对于建制派要求9月的立法会选举推迟一年，张建宗表示，能否如期举行要视乎疫情，底线是安全有序、公平公正地进行。由于投票人数众多，聚集风险非常高。\
            他又称，中国中央政府高度关注香港疫情，提出全力援助。他形容香港有中国这个强大的后盾，特首林郑月娥也已向中央政府请求，包括加大力度检测，及协助在位于大屿山的亚洲国际博览馆建立“方舱医院”等。\
            香港餐饮联业协会会长黄家和表示，目前已有约1200家食店停业，3000多家选择不做晚市提早关门，生意减少三成以上。若港府再禁午市堂食，预料生意将录得六成以上跌幅，整个7月会有50亿港元（8.9亿新元）亏损。\
            他说，部分食店难以转做外卖，例如专门举办婚宴及宴会的酒楼等。而且，业界也难以单靠外卖就可应付人力及其他成本开支，他形容饮食业如风烛残年，希望港府再提供及时援助。\
            香港医学会传染病顾问委员会主席梁子超认为，港府最好是同时要求更多港人居家工作，并确保有稳定的外卖供应，让市民不用抢购物资。\
            香港理工大学医疗科技及信息学系副教授萧杰恒表示，其研究团队近日为香港出现的确诊病例进行基因排序，发现当地病例与欧洲输入病例的基因突变特征相似，相信新一波疫情源头，很大机会是由外地输入。港府对船员提供免检疫安排，近日惹来舆论狠批。\
            （记者是《联合早报》香港特派员）一位的维权人士，疆独,六四\
            '
    t1 = time.time()
    pred_text, pred_detail = correct_dict_multi_thread(text)
    print(pred_text, pred_detail)
    print(time.time() - t1)
    
