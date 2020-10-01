# SentimentAnalysisofWeibo
I used the sentiment dictionary to predict the sentiment of post scraped from weibo.cn, here we will have the following contents.

## Contents:
### 1. a weibo spider:
It can scrape the posts from weibo.cn. It will give you as many posts as possible that is related to the kwyword during the period(from starttime to end time)
### 2. a slapdash sentiment analysis:
* i. It uses jieba to tokenize each posts, and can draw a very simple word cloud.
* ii. It can do a simple sentiment analysis(but not rigorous) based on the sentiment dictionaries

## About Tokenization:
#### I used the stopwords from Harbin Institute of Technology(HIT) and I also collect some other stopwords lists.

## About sentiment analysis:
* i. I don't have time to build a modle using the data, so I used the sentiment dictionary from BosonNLP sentiment scores, it is generated from weibo and news release, so I think it could be applicable.
* ii. Due to the limited time, and I really wish to end this temporately for my two coming deadlines, I choose to suppose that the negative words and adverbs before a sentiment word is to modify the sentiment word, and the sentiment od the sentence is the summed up scores of each sentimentwords mutiply the modifying negative words and adverbs before them.

###### *Note: this analysis is very slapdash, and I only upload these codes to record my learning process of python. And if this property in any ways invades your rights, please contact me.*
