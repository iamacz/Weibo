# -*- coding:utf-8 -*-
# By：Tangbin Chen
# Create：2019-12-25
# Update：2020-10-22
# For: Analyse data from weibo using a simple and not so rigours sentiment analysis based on sentiment dictionary


import jieba
import pandas as pd
from wordcloud import WordCloud


class SegPost:
    def __init__(self, df, get_sent = False, userdict='mydict.txt', stopwords='哈工大停用词表.txt'):
        self.df = self.clean_data(df)
        self.userdict = userdict
        self.stopwords = [line.strip() for line in open(f'.//dict/{stopwords}', 'r', encoding = 'utf-8').readlines()]
        self.words, self.app_seg = self.seg_str()
        self.app_sa, self.post_score = self.sentiment() if get_sent else None, None

    def get_sent(self):
        self.app_sa, self.post_score = self.sentiment()

    def clean_data(self, df):
        # load data and clean data, we will have a data set without duplicated posts or null/nan
        df = df[-pd.isna(df['post'])]
        df = df[df['post'] != '转发微博']
        df = df.drop_duplicates(subset=['post'])
        return(df)
    # we will generate 2 variables from the function
    # a set of all segregated words and a list of every sentence with seg_words

    def seg_str(self):
        rdf = self.df
        # load a local dictionary, here we put every dictionaries in the mydict folder
        jieba.load_userdict(f".//dict/{self.userdict}")
        seg_list = []
        for i in rdf.index:
            seg = jieba.lcut(rdf['post'][i], cut_all=False)
            seg_list.append(seg)
        # calculate the word frequency
        words = []
        new_seg = []
        for seg_t in seg_list:
            seg = []
            for word in seg_t:
                if word not in self.stopwords:
                    seg += [word]
                    words.append(word)
            new_seg.append(seg)
        rdf["seg_post"] = new_seg
        return words, rdf

    def word_freq(self):
        word_freq = pd.DataFrame(self.words, columns=['word'])
        word_freq = word_freq['word'].value_counts()
        return word_freq

    def get_wc(self, name, user_sw, font_path="chinese.simhei.ttf"):
        # words, rdf = self.seg_str()
        # import imageio
        # mk = imageio.imread('We_Can_Do_It.png')
        w = WordCloud(
            background_color='#F3F3F3',
            font_path= font_path,
            width=500,
            height=300,
            margin=2,
            max_font_size=200,
            random_state=42,
            scale=7,
            # add some customized stop words
            stopwords=set(self.stopwords).union(user_sw)
        )
        # w = w.generate_from_frequencies(word_freq)
        # w.to_file('output3.png')
        a = '//'.join(self.words)
        w2 = w.generate(a)
        w2.to_file(f'./wordcloud/{name}.png')
        return (w2)

    def sentiment(self, add_seg = False,use_weight=False):
        import pandas as pd
        import numpy as np
        sent_dict = pd.read_csv('.//dict/BosonNLP_sentiment_score.txt', encoding="utf-8", sep='\s', engine='python')
        neg_dict = [line.strip() for line in open(f'.//dict/Negative_word_list.txt', 'r', encoding='utf-8').readlines()]
        adv_dict = pd.read_csv('.//dict/adverb.csv', encoding="utf-8")
        # iterate in the seg list which contains all the posts
        import time
        post_score = []
        print('    Sentimental Analysis    '.center(100 // 2, '='))
        start = time.perf_counter()
        j = 0
        for i in self.app_seg.index:
            # iterate within one post
            score = []
            for word in self.app_seg['seg_post'][i]:
                s_sent = sent_dict[sent_dict['word'] == word]['score']
                if s_sent.any():
                    if s_sent.mean() > 0:
                        score += [1]
                    elif s_sent.mean() == 0:
                        score += [0]
                    elif s_sent.mean() < 0:
                        score += [-1]
            if score:
                post_score.append(sum(score))
            else:
                post_score.append(0)
            j += 1
            a = "*" * int(50 * j / len(self.app_seg.index))
            b = '.' * int(50 * (1 - (j / len(self.app_seg.index))))
            c = j / len(self.app_seg.index) * 100
            dur = time.perf_counter() - start
            left = dur / j * (len(self.app_seg.index) - j) / 60
            print('\r{:^3.0f}%[{}->{}] Dur: {:.2f}min; Approx {:.2f}min left'.format(c, a, b, dur / 60, left),
                  end='')
            # print('\r{:^3.0f}%[{}->{}]{:.2f}s'.format(c, a, b, dur), end='')
        print('\n' + 'End of the Loop'.center(100 // 2, '=')+'\n'+'\n')
        if add_seg:
            org = self.app_seg
        else:
            org = self.df
        org['post_sentiment'] = post_score
        return org, post_score


'''
I still wanna use this while giving sentimental score, buuuut, it is not so promising
I soublt this, so just stay in here a bit

        for i in self.app_seg.index:
            # iterate within one post
            weight = []
            score = []
            for word in self.app_seg['seg_post'][i]:
                s_sent = sent_dict[sent_dict['word'] == word]['score']
                s_neg = -1 if word in neg_dict else 1
                s_adv = adv_dict[adv_dict['word'] == word]['score'].values[0] if word in set(adv_dict['word']) else 1
                if use_weight:
                    if s_sent.any():
                        w = np.prod(weight) * s_sent.values[0]
                        score += [w]
                        weight = []
                    else:
                        weight += [s_neg, s_adv]
                else:
                    w = s_sent.values[0]
                    score += [w]

'''
