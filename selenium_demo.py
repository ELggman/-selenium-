import os
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver import EdgeOptions
from lxml import etree
import time
from threading import Thread
import re

# 配置无头浏览器参数以及规避检测
edge_options = Options()
edge_options.use_chromium = True
# edge_options.add_argument('--headless')
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--disable-blink-features=AutomationControlled')

s = Service('./msedgedriver.exe')


class login:
    def __init__(self):
        self.brow = webdriver.Edge(service=s, options=edge_options)
        self.brow.get('https://flights.ctrip.com/online/channel/domestic')

    def getTC(self):
        while True:
            try:
                tc = self.brow.find_element(by=By.XPATH, value='//div[@id="outerContainer"]//a[@class=“btn”]')
                tc.click()
                self.get_info()
            except:
                pass

    def login(self, account, password):
        login_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="hp_nfes_accountbar"]/li[1]/div/button')
        login_bt.click()

    def search_info(self, from_, to_, date):
        # 出发地点输入框
        from_lable = self.brow.find_element(by=By.XPATH,
                                            value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[1]/div/div/div[1]/input')
        from_lable.click()
        from_lable.send_keys(from_)

        to_lable = self.brow.find_element(by=By.XPATH,
                                          value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[3]/div/div/div[1]/input')
        to_lable.click()
        to_lable.send_keys(to_)
        to_lable.send_keys(Keys.ENTER)

        time.sleep(1)
        dc_button = self.brow.find_element(by=By.XPATH, value='//*[@id="searchForm"]/div/div/div/div[1]/ul/li[1]/span')
        dc_button.click()

        time.sleep(1)
        search_button = self.brow.find_element(by=By.XPATH, value='//*[@id="searchForm"]/div/button')
        search_button.click()

        self.get_info(date)

    def get_info(self, date):  # date 形如['2022','06','18']
        # 指定日期
        date = '-'.join(date)
        url = self.brow.current_url
        pattern = re.compile('(?<=depdate=).*?(?=&cabin)')
        url = re.sub(pattern, date, url)
        self.brow.get(url)
        # self.brow.refresh()
        
        # 疫情弹窗处理
        try:
            self.brow.implicitly_wait(2)
            yiqing_button = self.brow.find_element(by=By.XPATH, value='//*[@id="outerContainer"]/div/div[3]/div')
            yiqing_button.click()
        except:
            pass

        # 爬取航班信息

        # 直飞选项
        zhifei_button = self.brow.find_element(by=By.XPATH,
                                               value='//*[@id="hp_container"]/div[2]/div/div[3]/div[2]/div/ul[1]/li[1]/div/span')
        zhifei_button.click()

        # js脚本循环几次向下滑动,便于获取动态加载数据 需注意一次不能滑动太多，否则数据加载不全
        for i in range(8):
            time.sleep(0.5)
            self.brow.execute_script('window.scrollBy(0,500)')
        time.sleep(2)
        page_text = self.brow.page_source

        # 利用xpath解析数据
        tree = etree.HTML(page_text)
        self.flight_info_dict = {}
        # 航班divs
        divs = tree.xpath('//div[@class="flight-item domestic"]')

        print('div len', len(divs))
        for div in divs:
            # 航班信息形如 ['河北航空', 'NS8456\xa0', '波音737(中)', '共享 '] ‘共享’项不一定均存在
            flight_airline = div.xpath('.//div[@class="flight-airline"]//text()')

            # 航班详细信息 flight_detail

            # 出发地 ['17:05', '江北国际机场', 'T3'] 可能出现没有 航站楼Terminal信息
            depart = div.xpath('.//div[@class="depart-box"]//text()')

            # 目的地信息 ['00:40', ' +1天', '大兴国际机场', 'T2']  第二个信息为 附加信息，可能为空 第四个信息为航站楼信息，可能不会出现该信息
            arrival = div.xpath('.//div[@class="arrive-box"]//text()')

            # 航班准点率信息
            arrival_rate = div.xpath('.//div[@class="flight-arrival-punctuality-list"]//text()')

            # 航班价格信息
            flight_price = div.xpath('.//div[@class="flight-price domestic-flight-price"]//text()')
            # 获取航班信息
            info = []
            # 获取航空公司及飞机编号
            # name = flight_row_div.xpath('./div[1]//text()')
            # info.append(name)
            print(flight_airline, depart, arrival, arrival_rate, flight_price)

        time.sleep(5)
        # self.brow.quit()


if __name__ == '__main__':
    date = ['2022', '06', '18']
    lg = login()

    lg.search_info('重庆', '北京', date)

    # url = 'https://flights.ctrip.com/online/list/oneway-ckg-bjs?_=1&depdate=2022-06-15&cabin=Y_S_C_F'
    # pattern = re.compile('(?<=depdate=).*?(?=&cabin)')
    # print(re.sub(pattern, date, url))
