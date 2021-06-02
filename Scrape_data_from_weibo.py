# -*- coding:utf-8 -*-
# By：Tangbin Chen
# Create：2019-12-23
# Update：2021-10-20
# For: Scrape data from weibo and a simple and not so rigours sentiment analysis based on sentiment dictionary


import requests
import re
import os
import time
import random
from lxml import etree
from datetime import datetime, timedelta
import pandas as pd
from urllib.request import quote, unquote
from fp.fp import FreeProxy


class ScrapePosts:
    def __init__(self,kw=None,cookies=None,headers=None,use_prox=True,st=None,et=None,sort="hot",cr_url=True):
        self.cookies = cookies
        self.headers = headers
        if use_prox:
            self.new_proxy()
        else:
            self.proxies = None
        self.keyword = quote(kw, encoding='utf-8') if kw is not None else None
        self.starttime = datetime.strptime(st, '%Y/%m/%d') if st is not None else None
        self.endtime = datetime.strptime(et, '%Y/%m/%d') if et is not None else None
        self.sort = sort
        self.url = self.get_url() if cr_url else None

    def new_proxy(self, rand = True):
        self.proxies = FreeProxy(rand=rand).get()

    def change_endtime(self,date):
        self.endtime = datetime.strptime(date, '%Y/%m/%d')
        self.url = self.get_url()

    def change_starttime(self,date):
        self.starttime = datetime.strptime(date, '%Y/%m/%d')
        self.url = self.get_url()

    def change_kw(self,kw):
        self.keyword = quote(kw, encoding='utf-8')
        self.url = self.get_url()

    def change_sort(self,sort):
        self.sort = sort
        self.url = self.get_url()

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
        delta = self.endtime - self.starttime + timedelta(days=1)
        url = [None] * delta.days
        i = 0
        while i < delta.days:
            url[i] = search_url + "&keyword=" + self.keyword + "&advancedfilter=1" + "&starttime=" + (
                        self.starttime + timedelta(days=i)).strftime('%Y%m%d') + "&endtime=" + (
                                 self.starttime + timedelta(days=i)).strftime('%Y%m%d') + "&sort=" + self.sort
            i += 1
        return url

    # create a tiny function to create name
    def save_html(self, url, html):
        ed = re.findall(r'endtime=(.*?)&', url)[0]
        pg = re.findall(r'page=(.*)', url)[0]
        name = '_'.join([unquote(self.keyword), ed, pg])
        save = open('.//html/%s.txt' % name, "w", encoding="utf-8")
        save.write('%s' % html)
        save.close()

    # note that if you generate the url from geturl function, you will need to add the "&page=" to the url
    def get_html(self, url, save_html=True, use_prox=True):
        # find the headers, you will need the cookies that is freshly baked, you will need the Fiddler to get cookies
        headers = {
            'User-Agent': self.headers,
            'Cookie': self.cookies
        }
        if use_prox:
            proxies = {
                "https": self.proxies.replace("http://",""),
                "http": self.proxies.replace("http://", "")
            }
            response = requests.get(url, headers=headers, proxies=proxies)
        else:
            response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        # to know if we successfully get the response
        if response.status_code != 200:
            print('\nResponse Error!')
        html = response.text
        if save_html:
            self.save_html(url, html)
        html = bytes(html, encoding='utf-8')
        html = etree.HTML(html)
        return html

    def total_page(self, html):
        try:
            page = html.xpath("//div[@class='pa']//div/text()")
            page = str(page)
            page = int(re.findall(r'/(.*?)页', str(page))[0])
            if page > 100:
                page = 100
            return page
        except Exception as e:
            return 0
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
                    # print("Warning: this user can be posting a pic, userID is %s.\r" % poster)
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

    def post_list(self, get_ttp = True,use_prox=True):
        info_list = pd.DataFrame()
        # from the first page, get the total page of each day and also the first html
        timer = 0
        for url in self.url:
            timer = timer + 1
            i = 1
            child_url = []
            child_url.append(url + "&page=1")
            try:
                html = self.get_html(child_url[0],use_prox=use_prox)
                info = self.parse_html(html)
                # save the data just in case
                if not os.path.isfile("%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"],unquote(self.keyword))):
                    info.to_csv("%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"],unquote(self.keyword)), header=True)
                else:  # else it exists so append without writing the header
                    info.to_csv("%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"],unquote(self.keyword)),
                              mode='a', header=False)
                info_list = pd.concat([info_list, info], axis=0, ignore_index=True)
                # print("Great! Make it again!")
                ttp = self.total_page(html) if get_ttp else 100
                # sleep
                time.sleep(random.uniform(1, 4))
                # the second loop is to get html from each page of the day
                print("Try fetch data for day {}".format(re.findall(r'endtime=(.*?)&', url)[0]))
                print('  Get a cup of tea :p  '.center(100 // 2, '='))
                start = time.perf_counter()
                while i < ttp:
                    i = i + 1
                    child_url.append(url + "&page=%s" % i)
                    try:
                        html = self.get_html(child_url[i - 1],use_prox=use_prox)
                        info = self.parse_html(html)
                        # save the data just in case
                        if not os.path.isfile(
                                "%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"], unquote(self.keyword))):
                            info.to_csv(
                                "%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"], unquote(self.keyword)),
                                header=True)
                        else:  # else it exists so append without writing the header
                            info.to_csv(
                                "%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"], unquote(self.keyword)),
                                mode='a', header=False)
                        info_list = pd.concat([info_list, info], axis=0, ignore_index=True)
                        time.sleep(random.uniform(1,2))
                    except Exception as e:
                        print("Error in getting info list, cheack the PostList. Error type: %s" % e)
                        if use_prox:
                            self.new_proxy()
                        time.sleep(5)
                    a = "*" * int(50 * i / ttp)
                    b = '.' * int(50 * (1 - (i / ttp)))
                    c = i / ttp * 100
                    dur = time.perf_counter() - start
                    left = dur / i * (ttp - i) / 60
                    print('\r{:^3.0f}%[{}->{}] Dur: {:.2f}min; Approx {:.2f}min left'.format(c, a, b, dur / 60, left),
                          end='')
                print('\n' + '  Grattis! Everything Works!  '.center(100 // 2, '=') + '\n' + '\n')
            except Exception as e:
                print("Error in getting info list, cheack the PostList. Error type: %s" % e)
                if use_prox:
                    self.new_proxy()
                time.sleep(5)
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
    def divide_post(self,post_list,id_prefix):
        post_list = post_list.drop_duplicates().reset_index(drop=True)
        main_post = pd.DataFrame()
        other_post = pd.DataFrame()
        vip_post = pd.DataFrame()
        print('  Get a cup of tea :p  '.center(100 // 2, '='))
        j = 0
        start = time.perf_counter()
        for i in post_list.index:
            test_str = post_list['post_content'][i]
            # pa is for the post we have scraped
            pa_mpid = "%s%s%06d"%(id_prefix,0,i+1)
            pa_uid = post_list['user_id'][i]
            pa_url = post_list['user_url'][i].replace("https://weibo.cn/","")
            try:
                pa_time = re.findall(r"\d{2}月\d{2}日\s\d{2}:\d{2}", post_list['post_date'][i])[0]
                pa_time = datetime.strptime(pa_time, '%m月%d日 %H:%M')
                pa_time = pa_time.replace(year=2020)
            except:
                pa_time = None
            try:
                pa_dev = re.findall(r"来自(.*)", post_list['post_date'][i])[0]
            except:
                pa_dev = None
            pa_like = int(re.sub("[\D]","",post_list['post_like'][i]))
            pa_repo = int(re.sub("[\D]","",post_list['post_repo'][i]))
            pa_cmt = int(re.sub("[\D]","",post_list['post_comment'][i]))
            # v is for the post that is been reposted, most of which is popular posters
            v_post = post_list['original_post_content'][i]
            try:
                v_uid = post_list['original_poster_id'][i]
                v_url = post_list['original_poster_url'][i].replace("https://weibo.cn/","")
                v_like = int(re.sub("[\D]","",post_list['original_post_like'][i]))
                v_repo = int(re.sub("[\D]","",post_list['original_post_repo'][i]))
                v_cmt = int(re.sub("[\D]","",post_list['original_post_comment'][i]))
                temp_v = {
                    'MP_id': pa_mpid,
                    'OP_id': "%s%s%06d"%(id_prefix,1,i+1),
                    'OP_user_id': v_uid,
                    'OP_user_url': v_url,
                    'OP_content': v_post,
                    'OP_like': v_like,
                    'OP_repo': v_repo,
                    'OP_cmt': v_cmt
                }
                temp_v = pd.DataFrame(temp_v, index=[0])
                vip_post = pd.concat([vip_post, temp_v], ignore_index=True, axis=0)
            except:
                v_url = None
                # print('\rThere is no original post!')
            try:
                pa_post = re.findall(r'转发理由: (.*?)//', test_str)[0]
                pa_post = re.sub(r'[\s]+', '', pa_post)
            except:
                pa_post = None
            temp_main = {
                'MP_id': pa_mpid,
                'MP_user_id': pa_uid,
                'MP_user_url': pa_url,
                'MP_date': pa_time,
                'MP_dev': pa_dev,
                'MP_content': pa_post,
                'MP_like': pa_like,
                'MP_repo': pa_repo,
                'MP_cmt': pa_cmt,
                'OP_uer_url': v_url
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
                            'IP_user_id': ch_uid,
                            'IP_content': ch_post,
                            'MP_user_url': pa_url,
                            'MP_id': pa_mpid,
                            'OP_user_url': v_url,
                            'OP_id': "%s%s%06d"%(id_prefix,1,i+1)
                        }
                        temp = pd.DataFrame(temp)
                        other_post = pd.concat([other_post, temp], ignore_index=True, axis=0)
                    except:
                        # print("\rThis user repo without comment!")
                        pass
            j += 1
            if j%50 == 0:
                c = j / len(post_list.index)
                a = "*" * int(50 * c)
                b = '.' * int(50 * (1 - c))
                dur = time.perf_counter() - start
                left = dur / c * (1 - c) / 60
                print('\r{:^3.0f}%[{}->{}] Dur: {:.2f}min; Approx {:.2f}min left'.format(c*100, a, b, dur / 60, left),
                      end='')
        print('\n' + '  Grattis! Everything Works!  '.center(100 // 2, '=') + '\n' + '\n')
        return main_post, other_post, vip_post

    # give a list of post_lists from ScrapePosts.post_list, this function will return a user list
    # with only user name, user ID, and user url with duplicates being removed
    def merge_data(self,user_list):
        data = pd.concat(user_list, ignore_index=True, axis=0)
        data = data.drop_duplicates()
        d = data[['user_id', 'user_url']]
        c = data[['original_poster_id', 'original_poster_url']]
        c.columns = ['user_id', 'user_url']
        e = pd.concat([d, c], ignore_index=True, axis=0)
        e = e.drop_duplicates().dropna().reset_index(drop=True)
        e = e.rename(columns={"user_id": "user_name"})
        e["user_id"] = pd.DataFrame(re.sub(r"https:\/\/weibo\.cn\/u*\/*", "", x) for x in e["user_url"])
        return e

    # this will give a list
    def parse_user_page(self, html, uid, is_str=False):
        if is_str:
            html = bytes(html, encoding='utf-8')
            html = etree.HTML(html)
        # try to get the user id, just to make sure if we are on the right person
        # and some user id get from post are not proper ids(consist of only numbers)
        # so by doing this we can replace those bad ids
        try:
            user_id = "".join(html.xpath("//div[@class='u']//span[@class='ctt']/a/@href"))
            user_id = re.findall(r"uid=(\d+)&", user_id)[0]
        except:
            user_id = None
        user_info = "".join(html.xpath("//div[@class='u']//span[@class='ctt']/text()"))
        user_name = re.sub(r'\xa0[男女].*', '', user_info)
        user_gender = re.findall(r'\xa0([男女])', user_info)[0]
        try:
            user_city = re.sub(r"\s+", "", re.findall(r'\xa0[男女]\/(.*)\xa0', user_info)[0])
        except:
            user_city = None
        try:
            posts = html.xpath("//div[@class='tip2']/span/text()")[0]
            posts = re.sub("\D+","",posts)
            follows = html.xpath("//div[@class='tip2']/a[@href]/text()")[0]
            follows = re.sub("\D+", "", follows)
            fans = html.xpath("//div[@class='tip2']/a[@href]/text()")[1]
            fans = re.sub("\D+", "", fans)
        except:
            posts, follows, fans = None, None, None
        try:
            # flag if the user is an official account
            off = html.xpath("//div[@class='u']//div[@class='ut']/span[@class='ctt']/img/@src")[0]
            off_lab = html.xpath("//div[@class='u']//span[@class='ctt']/text()")[2].replace("认证：", "")
        except:
            off = None
            off_lab = None
        ff = {
            'user_id_s': uid,  # this id is from the html source, so we use this id to go to the user profile page
            'user_id': user_id,
            'user_name': user_name,
            'user_gender': user_gender,
            'user_city': user_city,
            'user_post': posts,
            'user_follow': follows,
            'user_fan': fans,
            'user_off': off,
            'user_off_lab': off_lab
        }
        ff = pd.DataFrame(ff,index=[0])
        return ff

    def user_info_list(self, user_list,file_name,use_prox=True):
        print('Start Scraping'.center(100 // 2, '='))
        user_info_list = pd.DataFrame()
        start = time.perf_counter()
        for i in user_list.index:
            user_url = user_list['user_url'][i]
            user_id = re.sub(r"https:\/\/weibo\.cn\/","",user_url)
            # this is to get the follower-fans information
            try:
                # self = luvcss
                # user_url = 'https://weibo.cn/mysour'
                # user_id = "mysour"
                html_ff = self.get_html(user_url, save_html=False,use_prox=use_prox)
                ff = self.parse_user_page(html = html_ff, uid=user_id)
                user_info_list = pd.concat([user_info_list,ff],axis=0,ignore_index=True)
                if not os.path.isfile("%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"],file_name)):
                    ff.to_csv("%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"],file_name), header=True)
                else:  # else it exists so append without writing the header
                    ff.to_csv("%s\Desktop\data\%s_append.csv" % (os.environ["HOMEPATH"],file_name),
                              mode='a', header=False)
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                if use_prox:
                    self.new_proxy()
                print("Error happens while getting user info, read details:%s"%e)
            j = i+1
            a = "*" * int(50 * j / len(user_list.index))
            b = '.' * int(50 * (1 - (j / len(user_list.index))))
            c = j / len(user_list.index) * 100
            dur = time.perf_counter() - start
            left = dur / j * (len(user_list.index) - j) / 60
            print('\r{:^3.0f}%[{}->{}] Dur: {:.2f}min; Approx {:.2f}min left'.format(c, a, b, dur / 60, left),
                  end='')
        print('\n' + '  Grattis! Everything Works!  '.center(100 // 2, '=') + '\n' + '\n')
        return user_info_list

    def parse_html2(self, html):
        post_list = html.xpath("//div[@class='c'][@id]")
        info_list = pd.DataFrame()
        for post in post_list:
            poster = post.xpath(".//div/a[@class='nk']/text()")[0]
            poster_url = post.xpath(".//div/a[@class='nk']/@href")[0]
            try:
                poster_v = post.xpath(".//div/img[@alt='V']/@src")[0]
                poster_v = re.sub("https:.*\/|\.gif", "", poster_v)
            except:
                poster_v = None
            div = post.xpath(".//div")
            if len(div) == 1:
                o_poster, o_poster_url,  o_poster_v = None, None, None
            elif len(div) == 2:
                if div[0].xpath(".//span[@class='cmt']/a[@href]/text()"):
                    o_poster = div[0].xpath(".//span[@class='cmt']/a[@href]/text()")[0]
                    o_poster_url = div[0].xpath(".//span[@class='cmt']/a/@href")[0]
                    try:
                        o_poster_v = div[0].xpath(".//span[@class='cmt']/img[@alt='V']/@src")[0]
                        o_poster_v = re.sub("https:.*\/|\.gif", "", o_poster_v)
                    except:
                        o_poster_v = None
                else:
                    o_poster, o_poster_url, o_poster_v = None, None, None
                    # print("Warning: this user can be posting a pic, userID is %s.\r" % poster)
            elif len(div) == 3:
                o_poster = div[0].xpath(".//span[@class='cmt']/a[@href]/text()")[0]
                o_poster_url = div[0].xpath(".//span[@class='cmt']/a/@href")[0]
                try:
                    o_poster_v = div[0].xpath(".//span[@class='cmt']/img[@alt='V']/@src")[0]
                    o_poster_v = re.sub("https:.*\/|\.gif", "", o_poster_v)
                except:
                    o_poster_v = None
            else:
                o_poster, o_poster_url, o_poster_v = None, None, None
                print("Error in implement")
            info = {
                'user_id': poster,
                'user_url': poster_url,
                'user_vtype': poster_v
            }
            info = pd.DataFrame(info,index=[0])
            info_list = pd.concat([info_list,info],axis=0,ignore_index=True)
            info = {
                'user_id': o_poster,
                'user_url': o_poster_url,
                'user_vtype': o_poster_v
            }
            info = pd.DataFrame(info,index=[0])
            info_list = pd.concat([info_list,info],axis=0,ignore_index=True).dropna(subset=["user_vtype"]).drop_duplicates()
        info_list = info_list.drop_duplicates()
        return (info_list)



# below are some independent methods
# manually parse some of the data and give you a data the same structure as the
# ScrapePosts.post_list
def read_html(path,kw,htmls=None,error_report=False):
    sp = ScrapePosts(kw=kw,cr_url=False,use_prox=False)
    htmls = os.listdir(path) if htmls is None else htmls
    raw = pd.DataFrame()
    error = []
    for i in htmls:
        try:
            f = open("%s\\%s"%(path,i), encoding='utf-8', mode = "r")
            html = ''.join(f.readlines())
            f.close()
            try:
                html = bytes(html, encoding='utf-8')
                html = etree.HTML(html)
                info = sp.parse_html2(html)
                raw = pd.concat([raw, info], axis=0, ignore_index=True).drop_duplicates()
            except Exception as e:
                error.append(i)
                print("an error while parsing the file:%s\nError:%s"%(i,e))
        except:
            print("an error while opening the file:%s" % i)
    if error_report:
        return raw, error
    else:
        return raw



# from a folder of htmls of the same topic, this function will read every html
# and return the numbers of relevant posts each day
def get_counts(path):
    htmls = os.listdir(path)
    counts = pd.DataFrame()
    for i in htmls:
        if re.search("_1\.txt",i) is not None:
            kw = re.findall("^(.*)_\d{8}",i)[0]
            date = datetime.strptime(re.findall("\d{8}",i)[0],"%Y%m%d").strftime("%Y/%m/%d")
            f = open("%s\%s"%(path,i), encoding='utf-8', mode = "r")
            html = ''.join(f.readlines())
            f.close()
            html = bytes(html, encoding='utf-8')
            html = etree.HTML(html)
            if re.search(r'抱歉，未找到(.*)相关结果。',
                         str(html.xpath("//div[@class='c']/text()")[0])) is not None:
                count = 0
                temp = {
                    'topic': [kw],
                    'date': [date],
                    'count': [count]
                }
                temp = pd.DataFrame(temp)
                counts = pd.concat([counts, temp], axis=0, ignore_index=True)
            else:
                count = html.xpath("//div[@class='c']/span/text()")[0]
                count = int(re.findall(r'共(.*?)条', str(count))[0])
                temp = {
                    'topic': [kw],
                    'date': [date],
                    'count': [count]
                }
                temp = pd.DataFrame(temp)
                counts = pd.concat([counts,temp],axis=0,ignore_index=True)
    return counts
