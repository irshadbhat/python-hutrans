#!/usr/bin/python

# Copyright Irshad Ahmad Bhat, Riyaz Ahmad Bhat 2015

import re
from collections import namedtuple, OrderedDict

class SSFReader():
    def __init__ (self, sentence):
        self.tokens = list()
        self.fs_order = list()
        self.nodeList = list()
        self.sentence = sentence
        fs_node = ('af', 'name', 'head', 'chunkId', 'chunkType', 'posn', 'vpos', 'drel', 'coref',
                'stype', 'voicetype', 'poslcat', 'mtype', 'troot', 'etype', 'etype_root', 'emph', 
                'esubtype', 'etype_name', 'agr_num', 'hon', 'agr_cas', 'agr_gen') #NOTE add node
        nodes = ('id', 'wordForm', 'posTag', 'af', 'name', 'head', 'chunkId', 'chunkType', 'posn', 
                'vpos', 'drel', 'coref', 'stype', 'voicetype', 'poslcat', 'mtype', 'troot', 'corel', 
                'parent', 'dmrel', 'etype', 'etype_root', 'emph', 'esubtype', 'etype_name', 'agr_num', 
                'hon', 'agr_cas', 'agr_gen') #NOTE add node

        self.node = namedtuple('node', nodes)
        self.maping = dict(zip(fs_node, range(len(fs_node)))) 
        self.features = namedtuple('features', ('lemma', 'cat', 'gen', 'num', 'per', 'case', 'vib', 'tam'))
    
    def morphFeatures (self, af):
        """LEMMA, CAT, GEN, NUM, PER, CASE, VIB, TAM"""
        af = af[1:-1].split(",")
        assert len(af) == 8 #NOTE no need to process trash!
        return af

    def buildNode(self, id_, form_, tag_, pairs_):
        wordForm_, Tag_, name_, head_, posn_, vpos_, chunkId_, chunkType_, depRel_, = [str()]*9 #NOTE add node
        corel_, coref_, parent_, stype_, voicetype_, features_, poslcat_, mtype_, troot_ = [str()]*9
        etype_, etype_root_, emph_, esubtype_, etype_name_, agr_num_, hon_, agr_cas_, agr_gen_ = [str()]*9 
        wordForm_, Tag_ = form_, tag_
        for key, value in pairs_.items():
            if key == "af":
                lemma_, cat_, gen_, num_, per_, case_, vib_, tam_ = self.morphFeatures(value) 
                features_ = self.features(lemma_, cat_, gen_, num_, per_, case_, vib_, tam_)
            elif key == "name":
                name_ = re.sub("'|\"", '', value) #NOTE word is used as word in deprel
            elif key == "chunkType":
                assert len(value.split(":", 1)) == 2 # no need to process trash! FIXME
                chunkType_, chunkId_ = re.sub("'|\"", '', value).split(":", 1)
            elif key == "head":
                head_ = re.sub("'|\"", '', value)
            elif key == "posn":
                posn_ = re.sub("'|\"", '', value)
            elif key == "vpos":
                vpos_ = re.sub("'|\"", '', value)
            elif key == "poslcat":
                poslcat_ = re.sub("'|\"", '', value)
            elif key == "mtype":
                mtype_ = re.sub("'|\"", '', value)
            elif key == "troot":
                troot_ = re.sub("'|\"", '', value)
            elif key == "drel":
                assert len(value.split(":", 1)) == 2 # no need to process trash! FIXME
                depRel_, parent_ = re.sub("'|\"", '', value).split(":", 1)
                assert depRel_ and parent_ # no need to process trash! FIXME
            elif key == "coref":
                try: corel_, coref_ = re.sub("'|\"", '', value).split(":")
                except ValueError: corel_, coref_ = '', re.sub("'|\"", '', value)
            elif key == "stype":
                stype_ = re.sub("'|\"", '', value)
            elif key == "voicetype":
                voicetype_ = re.sub("'|\"", '', value)
            elif key == "etype":
                etype_ = re.sub("'|\"", '', value)
            elif key == "etype_root":
                etype_root_ = re.sub("'|\"", '', value)
            elif key == "emph":
                emph_ = re.sub("'|\"", '', value)
            elif key == "esubtype":
                esubtype_ = re.sub("'|\"", '', value)
            elif key == "etype_name":
                etype_name_ = re.sub("'|\"", '', value)
            elif key == "agr_num":
                agr_num_ = re.sub("'|\"", '', value)
            elif key == "hon":
                hon_ = re.sub("'|\"", '', value)
            elif key == "agr_cas":
                agr_cas_ = re.sub("'|\"", '', value)
            elif key == "agr_gen":
                agr_gen_ = re.sub("'|\"", '', value) #NOTE add node

        self.fs_order.append([self.maping[x] for x in pairs_.keys() if x in self.maping][::-1])
        self.nodeList.append(self.node(id_, wordForm_, Tag_.decode("ascii", 'ignore').encode("ascii"),
            features_, name_, head_, chunkId_, chunkType_, posn_, vpos_, depRel_, coref_,
            stype_, voicetype_, poslcat_, mtype_, troot_, corel_, parent_, self.dmrel_,
            etype_, etype_root_, emph_, esubtype_, etype_name_, agr_num_, hon_, agr_cas_, agr_gen_)) #NOTE add node

    def FSPairs(self, FS):
        feats = OrderedDict()
        self.dmrel_ = False
        for feat in FS.split():
            if "=" not in feat: continue
            if 'dmrel' in feat:
                self.dmrel_ = True
                feat = feat.replace("dmrel", "drel")
            feat = re.sub("af='+", "af='", feat)
            feat = re.sub("af='+", "af='", feat)
            attribute, value = feat.split("=")
            feats[attribute] = value

        return feats

    def getAnnotations(self):
        for line in self.sentence.split("\n"):
            line = line.split('\t')
            if line[0].isdigit():
                assert len(line) == 4 # no need to process trash! FIXME
                id_, oBraces_, Tag_ = line[:3]
                attributeValue_pairs = self.FSPairs(line[3][4:-1])
                self.buildNode(id_, oBraces_, Tag_, attributeValue_pairs)
            elif line[0].replace(".", '').isdigit():
                id_, wordForm_, Tag_ = line[:3]
                attributeValue_pairs = self.FSPairs(line[3][4:-1])
                assert wordForm_.strip() and Tag_.strip() # no need to process trash! FIXME
                self.buildNode(id_, wordForm_, Tag_, attributeValue_pairs)
            else:
                self.buildNode('', '))', '', {})

        return self
