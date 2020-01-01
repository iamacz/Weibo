# -*- coding:utf-8 -*-
# By：Tangbin Chen
# Create：2019-12-23
# Update：2020-01-01
# For: Scrape data from weibo and a simple and not so rigours sentiment analysis based on sentiment dictionary


import requests
import re
import time
import random
from lxml import etree
from datetime import datetime, timedelta
import pandas as pd
from urllib.request import quote

class ScrapePosts:
    def __init__(self):
        self.keyword = None
        self.starttime = None
        self.endtime = None
        self.sort = 'time'

    def get_filter(self):
        self.keyword = input("Please input keyword:")
        self.endtime = input("Please input end time(yyyy/mm/dd):")
        self.starttime = input("Please input start time(yyyy/mm/dd):")
        self.sort = input("Please choose sorting method(time/hot):")
        # Sometimes it's ok to just put Chinese words into the url, but it will be better to encode with URL encoding
        self.keyword = quote(self.keyword, encoding='utf-8')
        self.starttime = datetime.strptime(self.starttime, '%Y/%m/%d')
        self.endtime = datetime.strptime(self.endtime, '%Y/%m/%d')

    # get the url, note that we need to paste the page= to the url
    # and the function returns a list of urls, each of which searches for the posts within one day
    def get_url(self):
        # default start time is Jan-01, 2010, default sort method is by time(could be by 'hot')
        search_url = 'https://weibo.cn/search/mblog?hideSearchFrame='
        delta = self.endtime - self.starttime
        url = [None] * delta.days
        i = 0
        while i < delta.days:
            url[i] = search_url + "&keyword=" + self.keyword + "&advancedfilter=1" + "&starttime=" + (
                        self.starttime + timedelta(days=i)).strftime('%Y%m%d') + "&endtime=" + (
                                 self.starttime + timedelta(days=i + 1)).strftime('%Y%m%d') + "&sort=" + self.sort
            i += 1
        return url

    # create a tiny function to create name
    def save_html(self, url, html):
        ed = re.findall(r'endtime=(.*?)&', url)[0]
        pg = re.findall(r'page=(.*)', url)[0]
        name = '_'.join([ed, pg])
        save = open('.//html/%s.txt' % name, "w", encoding="utf-8")
        save.write('%s' % html)
        save.close()

    # note that if you generate the url from geturl function, you will need to add the "&page=" to the url
    def get_html(self, url):
        # find the headers, you will need the cookies that is freshly baked, you will need the Fiddler to get cookies
        headers = {
            'User-Agent': 'ua',
            'Cookie': 'cookie'
        }
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        # to know if we successfully get the response
        if response.status_code == 200:
            print('Congrats, successfully get the HTML!')
        else:
            print('Response Error!')
        html = response.text
        self.save_html(url, html)
        html = bytes(html, encoding='utf-8')
        html = etree.HTML(html)
        return html

    def total_page(self, html):
        try:
            page = html.xpath("//div[@class='c']/span/text()")[0]
            page = str(page)
            page = int(re.findall(r'共(.*?)条', str(page))[0])
            page = int(round(page/10))
            if page > 2:
                page = 2
            return page
        except Exception as e:
            print(f'Error while getting the total page,{e}')

    def parse_html(self, html):
        post_list = html.xpath("//div[@class='c'][@id]")
        info_list = []
        for post in post_list:
            poster = post.xpath(".//div/a[@class='nk']/text()")[0]
            poster_url = post.xpath(".//div/a[@class='nk']/@href")[0]
            post_date = post.xpath(".//div/span[@class='ct']/text()")[0]
            post_like = post.xpath(".//div/a[@href]/text()")[-4]
            post_repo = post.xpath(".//div/a[@href]/text()")[-3]
            post_cmt = post.xpath(".//div/a[@href]/text()")[-2]
            div = post.xpath(".//div")
            if len(div) == 1:
                post_txt = etree.tostring(post.xpath(".//div/span[@class='ctt']")[0], encoding="unicode")
                post_txt = post_txt.replace('<span class="ctt">:', '')
                post_txt = post_txt.replace(f'<span class="kt">{self.keyword}</span>', self.keyword)
                post_txt = post_txt.replace('</span>\xa0', '')
                # Here, as above, the data we get may contain nothing or only what the last user who repoed had written
                # let's just tackle it later
                o_poster, o_poster_url, o_post_txt, o_post_like, o_post_repo, o_post_cmt = None, None, None, None, None, None
            elif len(div) == 2:
                try:
                    temp_post = div[1].xpath(".//text()")
                    post_txt = " ".join(temp_post[:len(temp_post) - 9])
                except Exception as e1:
                    post_txt, post_like, post_repo, post_cmt = None, None, None, None
                    print("Error in getting repo information, error type:%s" % e1)
                if div[0].xpath(".//span[@class='cmt']/a[@href]/text()"):
                    o_poster = div[0].xpath(".//span[@class='cmt']/a[@href]/text()")[0]
                    o_poster_url = div[0].xpath(".//span[@class='cmt']/a/@href")[0]
                    o_post_txt = etree.tostring(div[0].xpath(".//span[@class='ctt']")[0], encoding="unicode")
                    o_post_txt = re.sub(r'<[\w+/](.*?)[\"/\w]>', '', o_post_txt)
                    o_post_txt = re.sub(r'[\s]+', '', o_post_txt)
                    o_post_like = div[0].xpath(".//span[@class='cmt']/text()")[2]
                    o_post_repo = div[0].xpath(".//span[@class='cmt']/text()")[3]
                    o_post_cmt = div[0].xpath(".//a[@class='cc']/text()")[0]
                else:
                    o_poster, o_poster_url, o_post_txt, o_post_like, o_post_repo, o_post_cmt = None, None, None, None, None, None
                    print("Warning: this user can be posting a pic, userID is %s." % poster)
            elif len(div) == 3:
                try:
                    temp_post = div[2].xpath(".//text()")
                    post_txt = " ".join(temp_post[:len(temp_post) - 9])
                except Exception as e3:
                    post_txt, post_like, post_repo, post_cmt = None, None, None, None
                    print("Error in getting repo information, error type:%s" % e3)
                o_poster = div[0].xpath(".//span[@class='cmt']/a[@href]/text()")[0]
                o_poster_url = div[0].xpath(".//span[@class='cmt']/a/@href")[0]
                # here we can not just choose the text, because people might have @others and posts some hashtags which
                # will be eliminated if we only return the text
                o_post_txt = etree.tostring(div[0].xpath(".//span[@class='ctt']")[0], encoding="unicode")
                o_post_txt = re.sub(r'<[\w+/](.*?)[\"/\w]>', '', o_post_txt)
                o_post_txt = re.sub(r'[\s]+', '', o_post_txt)
                o_post_like = div[1].xpath(".//span[@class='cmt']/text()")[0]
                o_post_repo = div[1].xpath(".//span[@class='cmt']/text()")[1]
                o_post_cmt = div[1].xpath(".//a[@class='cc']/text()")[0]
            else:
                post_txt, post_like, post_repo, post_cmt = None, None, None, None
                o_poster, o_poster_url, o_post_txt, o_post_like, o_post_repo, o_post_cmt = None, None, None, None, None, None
                print("Error in implement")
            info = {
                'user_id': poster,
                'user_url': poster_url,
                'post_date': post_date,
                'post_content': post_txt,
                'post_like': post_like,
                'post_repo': post_repo,
                'post_comment': post_cmt,
                'original_poster_id': o_poster,
                'original_poster_url': o_poster_url,
                'original_post_content': o_post_txt,
                'original_post_like': o_post_like,
                'original_post_repo': o_post_repo,
                'original_post_comment': o_post_cmt
            }
            info_list.append(info)
        info_list = pd.DataFrame(info_list)
        return (info_list)

    def post_list(self):
        info_list = pd.DataFrame()
        # from the first page, get the total page of each day and also the first html
        timer = 0
        url_list = self.get_url()
        for url in url_list:
            timer = timer + 1
            i = 1
            child_url = []
            child_url.append(url + "&page=1")
            html = self.get_html(child_url[0])
            try:
                info = self.parse_html(html)
                info_list = pd.concat([info_list, info], axis=0, ignore_index=True)
                print("Great! Make it again!")
            except Exception as e:
                print("Error in getting info list, cheack the PostList. Error type: %s" % e)
            ttp = self.total_page(html)
            # sleep
            if timer % 5:
                time.sleep(random.uniform(5, 15))
            else:
                time.sleep(random.uniform(20, 40))
            # the second loop is to get html from each page of the day
            while i <= ttp:
                i = i + 1
                child_url.append(url + "&page=%s" % i)
                html = self.get_html(child_url[i - 1])
                try:
                    info = self.parse_html(html)
                    info_list = pd.concat([info_list, info], axis=0, ignore_index=True)
                except Exception as e:
                    print("Error in getting info list, cheack the PostList. Error type: %s" % e)
                # sleep
                if i % 5:
                    time.sleep(random.uniform(5, 15))
                else:
                    time.sleep(random.uniform(20, 40))
        return info_list

    '''
        This function is write for the data scrapped and stored by the 'execute' with the object extract
        Since the data scrapped are not perfect for the text analysis task so we do a little modification
        to the data as well, after the process, new data frame will be stored in //analyse data/data
        Note:
            the function will return the data frame as well in the order of norm_user(who post/repo the
            post), norm_user2(who are repoed, but we don't have their url,likes,ect), V_user(who are repoed,
            and who are mostly popular weiboers)
    '''
    def get_divided(self):
        post_list = self.post_list()
        main_post = pd.DataFrame()
        other_post = pd.DataFrame()
        vip_post = pd.DataFrame()
        for i in post_list.index:
            test_str = post_list['post_content'][i]
            # pa is for the post we have scraped
            pa_uid = post_list['user_id'][i]
            pa_like = post_list['post_like'][i]
            pa_repo = post_list['post_repo'][i]
            pa_cmt = post_list['post_comment'][i]
            # v is for the post that is been reposted, most of which is popular posters
            v_post = post_list['original_post_content'][i]
            try:
                v_uid = post_list['original_poster_id'][i]
                v_like = post_list['original_post_like'][i]
                v_repo = post_list['original_post_repo'][i]
                v_cmt = post_list['original_post_comment'][i]
                temp_v = {
                    'v_user_id': v_uid,
                    'v_post_content': v_post,
                    'v_post_like': v_like,
                    'v_post_repo': v_repo,
                    'v_post_cmt': v_cmt
                }
                temp_v = pd.DataFrame(temp_v, index=[0])
                vip_post = pd.concat([vip_post, temp_v], ignore_index=True, axis=0)
            except:
                v_uid = None
                print('\rThere is no original post!')
            try:
                pa_post = re.findall(r'转发理由: (.*?)//', test_str)[0]
                pa_post = re.sub(r'[\s]+', '', pa_post)
            except:
                pa_post = None
            temp_main = {
                'user_id': pa_uid,
                'post_content': pa_post,
                'post_like': pa_like,
                'post_repo': pa_repo,
                'post_cmt': pa_cmt,
                'interact': v_uid
            }
            temp_main = pd.DataFrame(temp_main, index=[0])
            main_post = pd.concat([main_post, temp_main], ignore_index=True, axis=0)
            ch_posts = re.split(r'[//|\xa0]', test_str)
            for t_post in ch_posts:
                if re.search('@', t_post) != None:
                    try:
                        ch_uid = re.findall('@(.*?)\s{0,3}:', t_post)[0],
                        ch_post = re.findall(':(.*)', t_post)[0]
                        ch_post = re.sub(r'[\s]+', '', ch_post)
                        temp = {
                            'user_id': ch_uid,
                            'post': ch_post,
                            'interact': pa_uid,
                            'v_uid': v_uid
                        }
                        temp = pd.DataFrame(temp)
                        other_post = pd.concat([other_post, temp], ignore_index=True, axis=0)
                    except:
                        print("\rThis user repo without comment!")
        return main_post, other_post, vip_post