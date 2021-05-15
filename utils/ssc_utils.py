'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
Date: 2021-05-11 21:57:28
'''
import sys, os
sys.path.insert(0, os.getcwd())

import time
from utils.logger import logger
from escorrector.config import hanzi_ssc_path

strokesDictReverse = {'1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'A':10,
               'B':11, 'C':12, 'D':13, 'E':14, 'F':15, 'G':16, 'H':17, 'I':18, 'J':19, 'K':20,
               'L':21, 'M':22, 'N':23, 'O':24, 'P':25, 'Q':26, 'R':27, 'S':28, 'T':29, 'U':30,
               'V':31, 'W':32, 'X':33, 'Y':34, 'Z':35, '0':0}

soundWeight=0.5
shapeWeight=0.5
def computeSoundCodeSimilarity(soundCode1, soundCode2):#soundCode=['2', '8', '5', '2']
    featureSize=len(soundCode1)
    wights = [0.4, 0.4, 0.1, 0.1]
    multiplier=[]
    for i in range(featureSize):
        if soundCode1[i]==soundCode2[i]:
            multiplier.append(1)
        else:
            multiplier.append(0)
    soundSimilarity=0
    for i in range(featureSize):
        soundSimilarity += wights[i]*multiplier[i]
    return soundSimilarity

def computeShapeCodeSimilarity(shapeCode1, shapeCode2):#shapeCode=['5', '6', '0', '1', '0', '3', '8']
    featureSize=len(shapeCode1)
    wights = [0.25, 0.1, 0.1, 0.1, 0.1, 0.1, 0.25]
    # wights = [0.3, 0.1, 0.1, 0.1, 0.1, 0.3]
    multiplier=[]
    for i in range(featureSize-1):
        if shapeCode1[i]==shapeCode2[i]:
            multiplier.append(1)
        else:
            multiplier.append(0)
    multiplier.append(1- abs(strokesDictReverse[shapeCode1[-1]]-strokesDictReverse[shapeCode2[-1]])*1.0 / max(strokesDictReverse[shapeCode1[-1]],strokesDictReverse[shapeCode2[-1]]) )
    shapeSimilarity=0
    for i in range(featureSize):
        shapeSimilarity += wights[i]*multiplier[i]
    return shapeSimilarity

def computeSSCSimilarity(ssc1, ssc2, ssc_encode_way='ALL'):
    '''
    @Descripttion: 
    @param ssc_encode_way 1、ALL    2、SOUND    3、SHAPE 
    @return: 
    '''
    #return 0.5*computeSoundCodeSimilarity(ssc1[:4], ssc2[:4])+0.5*computeShapeCodeSimilarity(ssc1[4:], ssc2[4:])
    if ssc_encode_way=="SOUND":
        return computeSoundCodeSimilarity(ssc1, ssc2)
    elif ssc_encode_way=="SHAPE":
        return computeShapeCodeSimilarity(ssc1, ssc2)
    else:
        soundSimi=computeSoundCodeSimilarity(ssc1[:4], ssc2[:4])
        shapeSimi=computeShapeCodeSimilarity(ssc1[4:], ssc2[4:])
        return soundWeight * soundSimi + shapeWeight * shapeSimi


class Filter_ssc():
    def __init__(self, hanzi_ssc_path):
        t1 = time.time()
        self.hanziSSCDict = self._getHanziSSCDict(hanzi_ssc_path)
        logger.debug('load ssc file, spend: %.3f s.' % (time.time() - t1))

    def _getHanziSSCDict(self, hanzi_ssc_path):
        hanziSSCDict = {}#汉字：SSC码
        with open(hanzi_ssc_path, 'r', encoding='UTF-8') as f:#文件特征：U+4EFF\t仿\t音形码\n
            for line in f:
                line = line.split()
                hanziSSCDict[line[1]] = line[2]
        return hanziSSCDict

    def get_word_ssc(self, word):
        '''
        Descripttion: 返回字符串的音形码
        param {*}
        return {*}
        '''
        ssc = ''
        for char in word:
            if self.hanziSSCDict.get(char) == None:
                ssc += '#' * 11
            else:
                ssc += self.hanziSSCDict.get(char)
        return ssc

    def get_word_sound_code(self, word):
        sound_code=''
        for char in word:
            sound_code += self.get_word_ssc(char)[:4]
        return sound_code

    def get_word_shape_code(self, word):
        shape_code=''
        for char in word:
            shape_code += self.get_word_ssc(char)[4:]
        return shape_code

    def computer_ssc_char_loss(self, char1, char2):
        '''
        @Descripttion: 计算两个字符间的音形码损失
        @param {*}
        @return {sound_loss, shape_loss}
        '''    
        char1_sound_code = self.get_word_sound_code(char1)
        char2_sound_code = self.get_word_sound_code(char2)

        char1_shape_code = self.get_word_shape_code(char1)
        char2_shape_code = self.get_word_shape_code(char2)

        sound_code_size = len(char1_sound_code)
        shape_code_size = len(char1_shape_code)

        sound_code_weight = [0.4, 0.4, 0.1, 0.1] # 音码各位权重
        shape_code_weight = [0.25, 0.1, 0.1, 0.1, 0.1, 0.1, 0.25] # 形码各位权重

        sound_multiplier= []
        shape_multiplier= []

        # 音码损失
        for i in range(sound_code_size):
            if char1_sound_code[i] != char2_sound_code[i]:
                sound_multiplier.append(1)
            else:
                sound_multiplier.append(0)
        sound_loss=0
        for i in range(sound_code_size):
            sound_loss += sound_code_weight[i] * sound_multiplier[i]

        # 形码损失
        for i in range(shape_code_size):
            if char1_shape_code[i] != char2_shape_code[i]:
                shape_multiplier.append(1)
            else:
                shape_multiplier.append(0)
        shape_loss=0
        for i in range(shape_code_size):
            shape_loss += shape_code_weight[i] * shape_multiplier[i]

        return sound_loss, shape_loss

    def computer_ssc_word_loss(self, word1, word2):
        '''
        @Descripttion: 计算两个字符串间的音形码损失
        @param {*}
        @return {sound_loss, shape_loss }
        '''
        word_sound_loss = []
        word_shape_loss = []
        length = len(word1)
        for i in range(length):
            if word1[i] != word2[i]:
                sound_loss, shape_loss = self.computer_ssc_char_loss(word1[i], word2[i])
                word_sound_loss.append(sound_loss)
                word_shape_loss.append(shape_loss)
        # 计算音码损失值
        if word_sound_loss == []:
            sound_loss_max = 0
        else:
            sound_loss_max = max(word_sound_loss)
        # 计算形码损失平均值
        if word_shape_loss == []:
            shape_loss_max = 0
        else:
            shape_loss_max = max(word_shape_loss)

        return sound_loss_max, shape_loss_max


if __name__ == '__main__':
    filter_ssc = Filter_ssc(hanzi_ssc_path)
    # computeSSCSimilaruty()
    filter_ssc.computer_ssc_word_loss('萝卜素成','萝卜上坟')