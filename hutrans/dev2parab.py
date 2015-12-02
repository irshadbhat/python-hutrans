#!/usr/bin/env python 
#!-*- coding: utf-8 -*-

"""
Transliteration Tool:
Devnagri to Persio-Arabic transliterator for hindi-urdu transliteration
"""

import os
import re
import sys
import warnings

import numpy as np
from scipy.sparse import csc_matrix

import viterbi
import one_hot_repr
from converter_indic import wxConvert

warnings.filterwarnings("ignore")

__author__ = "Irshad Ahmad"
__version__ = "1.0"
__email__ = "irshad.bhat@research.iiit.ac.in"

class DP_Transliterator():
    """Transliterates words from Hindi to Urdu"""

    def __init__(self):        

        self.n = 4
	self.tab = chr(1)*2
	self.space = chr(2)*2
	self.esc_char = chr(0)
        self.lookup = dict()
        self.con = wxConvert(order='utf2wx')
        path = os.path.abspath(__file__).rpartition('/')[0]
	sys.path.append(path)
	self.coef_ = np.load('%s/models/hu_coef.npy' %path)[0]
        self.vec = np.load('%s/models/hu_sparse-vec.npy' %path)[0]
	self.classes_ = np.load('%s/models/hu_classes.npy' %path)[0]
	self.intercept_init_ = np.load('%s/models/hu_intercept_init.npy' %path)
	self.intercept_trans_ = np.load('%s/models/hu_intercept_trans.npy' %path)
	self.intercept_final_ = np.load('%s/models/hu_intercept_final.npy' %path)
	self.lrange = set(range(ord('a'), ord('z')+1)) | set(range(ord('A'), ord('Z')+1))
	self.letters = re.compile(r"([^a-zA-Z%s]+)" %(self.esc_char))

        self.punkt_str = str()
        self.punkt_tbl = dict()
        with open('%s/extras/punkt.map' %path) as punkt_fp:
            for line in punkt_fp:
                line = line.decode('utf-8')
                s,t = line.split()
                self.punkt_str += s
                self.punkt_tbl[ord(s)] = t

    def feature_extraction(self, letters):
        out_word = list()
        dummies = ["_"] * self.n
        context = dummies + letters + dummies
        for i in range(self.n, len(context)-self.n):
            current_token = context[i]
            wordContext = context[i-self.n:i] + [current_token] + context[i+1:i+(self.n+1)]
            word_ngram_context = wordContext + ["%s|%s" % (p,q) for p,q in zip(wordContext[:-1], wordContext[1:])] +\
                ["%s|%s|%s" % (r,s,t) for r,s,t in zip(wordContext[:-2], wordContext[1:], wordContext[2:])] +\
                ["%s|%s|%s|%s" % (u,v,w,x) for u,v,w,x in zip(wordContext[:-3],wordContext[1:],wordContext[2:],wordContext[3:])] 
            out_word.append(word_ngram_context)

        return out_word

    def predict(self, word):
        X = self.vec.transform(word)
        scores = X.dot(self.coef_.T).toarray()

        y = viterbi.decode(scores, self.intercept_trans_, self.intercept_init_, self.intercept_final_)

        y =  [self.classes_[pred] for pred in y]

        return re.sub('_','',''.join(y))

    def case_trans(self, word):
        if word in self.lookup:
            return self.lookup[word]
        word_feats = ' '.join(word).replace(' a', 'a').replace(' Z', 'Z')
        word_feats = word_feats.encode('utf-8').split()
        word_feats = self.feature_extraction(word_feats)
        op_word = self.predict(word_feats)
        self.lookup[word] = op_word

        return op_word

    def transliterate(self, text):
        tline = str()
	text = re.sub(r'([a-zA-Z]+)', r'%s\1' %(self.esc_char), text)
	lines = text.split("\n")
	for line in lines:
	    if not line.strip():
                tline += "\n"
		continue
            line = self.con.convert(line).decode('utf-8')  # Convert to wx
            line = line.replace('\t', self.tab)
            line = line.replace(' ', self.space)
            line = self.letters.split(line)
            for word in line:
		if not word:
		    continue
		if word == self.space:
		    tline += " "
		elif word == self.tab:
		    tline += "\t"
		elif word[0] == self.esc_char:
		    tline += word[1:].encode('utf-8')
                elif ord(word[0]) not in self.lrange:
                    tline += word.translate(self.punkt_tbl).encode('utf-8')
		else:
		    op_word = self.case_trans(word)
		    tline += op_word
	    tline += "\n"
       
	tline = tline.replace(self.space, " ")
	tline = tline.replace(self.tab, "\t").strip()
        return tline
