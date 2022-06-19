import os
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver import EdgeOptions
from lxml import etree
import time
import re
import logging
import logging.config
from Send_Email import Send_QQ_Email
import datetime
import subprocess

from time import sleep
from PIL import Image
from chaojiying import Chaojiying_Client
from dpi_get import WindowsCommon
from selenium.webdriver import ActionChains

# 配置无头浏览器参数以及规避检测
edge_options = Options()
edge_options.use_chromium = True
# edge_options.add_argument('--headless')
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--disable-blink-features=AutomationControlled')

s = Service('./msedgedriver.exe')

# 配置文件实现日志
# 设置两个日志文件，app.log用于记录程序正常运行日志 error.log用于记录异常日志
logging.config.fileConfig('./logging.conf')
logger = logging.getLogger('applog')
root_logger = logging.getLogger()


class Subprice:
    def __init__(self, account, password):
        self.brow = webdriver.Edge(service=s, options=edge_options)
        self.brow.get('https://passport.ctrip.com/user/login')  # 用户的登录界面网址
        self.login(account, password)

    def login(self, account, password):

        logger.info(f'开始登陆账户 {account}')

        user_name = self.brow.find_element(by=By.XPATH, value='//*[@id="nloginname"]')  # 用户名标签的定位
        user_passowrd = self.brow.find_element(by=By.XPATH, value='//*[@id="npwd"]')  # 用户密码的登录
        user_name.click()
        user_name.send_keys(account)  # 填入账号

        user_passowrd.click()
        user_passowrd.send_keys(password)  # 填入密码
        login_aggree_b2 = self.brow.find_element(by=By.XPATH, value='//*[@id="normalview"]/form/p/input')  # 同意登录的定位
        login_aggree_b2.click()
        login_b2 = self.brow.find_element(by=By.XPATH, value='//*[@id="nsubmit"]')  # 账号登录的登录按钮定位
        login_b2.click()
        flag = True
        try:

            self.ver_slidecode()

            self.click_code()
        except:
            flag = False
            ret = subprocess.run("ping www.baidu.com -n 1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 在登录成功后
        sleep(2)
        logger.info(f'账户 {account} 已成功登录')
        try:
            first_option = self.brow.find_element(by=By.XPATH,
                                                  value='//*[@id="hp_nfes_homepage"]/span')  # 在登陆界面之后是需要点击首页的选项
            first_option.click()
            flag = True
        except Exception:
            pass

        # 飞机票的选项

        sleep(3)
        first_option_tk = self.brow.find_element(by=By.XPATH,
                                                 value='//*[@id="leftSideNavLayer"]/div/div/div[2]/div/div[1]/div/div[2]/button')
        first_option_tk.click()
        airplane_tk_option = self.brow.find_element(by=By.XPATH,
                                                    value='//*[@id="leftSideNavLayer"]/div/div/div[2]/div/div[1]/div/div[2]/button')
        airplane_tk_option.click()
        sleep(0.4)

    # 滚轮验证码的点击因为不需要滚轮的点击

    # 滑块验证码的验证

    def ver_slidecode(self):  # 在验证码登录的时可以利用循环来进行点击
        logger.info('正在破解第一重验证码')
        while True:
            try:
                ver_scroll = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div/div[4]/div[3]')
                sleep(1)
                ver_scroll.click()
                flag = 1
                if flag:
                    break
            except:
                # num +=1
                pass
        # 顺序点击的验证码

    def click_code(self):
        logger.info('正在破解第二重验证码')
        # 首先截图
        sleep(3)
        self.brow.save_screenshot('aa.png')  # 对当前页面保存
        code_img_ele = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
        location = code_img_ele.location  # x,y
        print(location)
        size = code_img_ele.size  # size返回的是验证码标签返回的长和宽
        print(size)
        # 对应左上角和右下角的坐标
        # 获取当前的电脑的分辨率
        windows_common = WindowsCommon()
        dpi_num = windows_common.getScreenScaleRate()
        x = int(location['x']) * dpi_num
        y = int(location['y']) * dpi_num
        rangle = (
            int(location['x']) * dpi_num, int(location['y']) * dpi_num, int(location['x'] + size['width']) * dpi_num,
            int(location['y'] + size['height']) * dpi_num)
        # 验证码图片确定下来了
        print(rangle)
        i = Image.open('./aa.png')
        code_img_name = 'code.png'
        frame = i.crop(rangle)
        frame.save(code_img_name)
        chaojiying = Chaojiying_Client("frants", "123456", "934829")
        im = open('code.png', 'rb').read()
        dic = chaojiying.PostPic(im, 9004)['pic_str']
        print('dic:', dic)
        # 对获取到的坐标进行分割按'|'
        if '|' in dic:
            groups = dic.split('|')
            locations = [[int(number) for number in group.split(',')] for group in groups]  # 将坐标
        else:
            one_local = dic.split(',')
            locations = [[one_local[0], one_local[1]]]

        element = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
        for location_1 in locations:
            x = location_1[0] / dpi_num
            y = location_1[1] / dpi_num
            ActionChains(self.brow).move_to_element_with_offset(element, x, y).click().perform()
        login_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="hp_nfes_accountbar"]/li[1]/div/button')
        login_bt.click()

    def search_info(self, from_, to_, date, depart_option, class_option, passenger_info):
        # 需传入 起始地点 目的地 日期 选择的起飞时间段 舱位等级
        # depart_option 1：代表6点到12点 2：代表12点到18点 3：代表18点到24点
        # class_option 1:经济舱 2:商务舱/头等舱
        date = '-'.join(date)  # date 形如['2022','06','18']
        depart_option_dic = {1: '6点到12点', 2: '12点到18点', 3: '18点到24点'}
        class_option_dic = {1: '经济舱', 2: '商务舱/头等舱'}
        logger.info(
            f'开始查找 在 {date} {depart_option_dic[depart_option]} 时间段，由 {from_} 去往 {to_} {class_option_dic[class_option]}的机票')

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

        # 指定日期
        # date = '-'.join(date)  # date 形如['2022','06','18']
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

        # 爬取航班信息前的处理

        # 直飞选项
        zhifei_button = self.brow.find_element(by=By.XPATH,
                                               value='//*[@id="hp_container"]/div[2]/div/div[3]/div[2]/div/ul[1]/li[1]/div/span')
        zhifei_button.click()
        # 起飞时间段/抵达时间段
        depart_arrival = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_time"]/div')
        depart_arrival.click()
        time.sleep(0.8)
        # depart_option = 1  # 1：代表6点到12点 2：代表12点到18点 3：代表18点到24点
        arrival_option = 1  #
        # 选择起飞时间段
        depart_ul = self.brow.find_element(by=By.XPATH,
                                           value=f'.//ul[@id="filter_group_time__depart"]/li[{depart_option}]/span/i')
        depart_ul.click()

        arrival_ul = self.brow.find_element(by=By.XPATH,
                                            value=f'.//ul[@id="filter_group_time__arrive"]/li[{arrival_option}]/span/i')

        depart_arrival.click()

        # 选择舱位 经济舱 or 商务舱/头等舱
        # class_option = 1  # 1：经济舱 2：商务舱/头等舱 默认为1

        class_grade = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_class_grade"]/div')
        class_grade.click()
        class_ul = self.brow.find_element(by=By.XPATH,
                                          value=f'.//ul[@id="filter_group_class_grade__default"]/li[{class_option}]')

        class_ul.click()
        class_grade.click()

        # js脚本循环几次向下滑动,便于获取动态加载数据 需注意一次不能滑动太多，否则数据加载不全
        for i in range(8):
            time.sleep(0.5)
            self.brow.execute_script('window.scrollBy(0,500)')
        time.sleep(2)
        page_text = self.brow.page_source

        logger.info('正在获取航班信息...')
        # 利用xpath解析数据
        tree = etree.HTML(page_text)
        self.flight_info_dict = {}
        # 航班divs
        divs = tree.xpath('//div[@class="flight-item domestic"]')

        # 航班信息形如 ['河北航空', 'NS8456\xa0', '波音737(中)', '共享 '] ‘共享’项不一定均存在
        flight_airline = divs[1].xpath('.//div[@class="flight-airline"]//text()')

        # 航班详细信息 flight_detail

        # 出发地 ['17:05', '江北国际机场', 'T3'] 可能出现没有 航站楼Terminal信息
        depart = divs[1].xpath('.//div[@class="depart-box"]//text()')

        # 目的地信息 ['00:40', ' +1天', '大兴国际机场', 'T2']  第二个信息为 附加信息，可能为空 第四个信息为航站楼信息，可能不会出现该信息
        arrival = divs[1].xpath('.//div[@class="arrive-box"]//text()')

        # # 航班准点率信息
        # arrival_rate = divs[1].xpath('.//div[@class="flight-arrival-punctuality-list"]//text()')
        #
        # # 航班价格信息
        # flight_price = divs[1].xpath('.//div[@class="flight-price domestic-flight-price"]//text()')
        # 获取航班信息

        # 获取航空公司及飞机编号
        info = ' '.join(flight_airline) + ' '.join(depart) + ' '.join(arrival)
        # info = ' '.join(flight_airline) + ' '.join(depart) + ' '.join(arrival) + ' '.join(arrival_rate) + ' '.join(
        #     flight_price)
        logger.info(info)

        # for div in divs:
        #     # 航班信息形如 ['河北航空', 'NS8456\xa0', '波音737(中)', '共享 '] ‘共享’项不一定均存在
        #     flight_airline = div.xpath('.//div[@class="flight-airline"]//text()')
        #
        #     # 航班详细信息 flight_detail
        #
        #     # 出发地 ['17:05', '江北国际机场', 'T3'] 可能出现没有 航站楼Terminal信息
        #     depart = div.xpath('.//div[@class="depart-box"]//text()')
        #
        #     # 目的地信息 ['00:40', ' +1天', '大兴国际机场', 'T2']  第二个信息为 附加信息，可能为空 第四个信息为航站楼信息，可能不会出现该信息
        #     arrival = div.xpath('.//div[@class="arrive-box"]//text()')
        #
        #     # 航班准点率信息
        #     arrival_rate = div.xpath('.//div[@class="flight-arrival-punctuality-list"]//text()')
        #
        #     # 航班价格信息
        #     flight_price = div.xpath('.//div[@class="flight-price domestic-flight-price"]//text()')
        #     # 获取航班信息
        #
        #     # 获取航空公司及飞机编号
        #     info = ' '.join(flight_airline) + ' '.join(depart) + ' '.join(arrival) + ' '.join(arrival_rate) + ' '.join(
        #         flight_price)
        #     logger.debug(info)
        self.brow.execute_script('window.scrollTo(0,0)')
        logger.info('开始生成订单')
        # # 生成订单
        expend_all_price = self.brow.find_element(by=By.XPATH,
                                                  value='.//*[@id="hp_container"]/div[2]/div/div[3]/div[3]/div[2]/span/div[1]/div/div/div/div/div[2]/div[2]/button')
        # expend_all_price.click()
        self.brow.execute_script("arguments[0].click();", expend_all_price)

        order_ = self.brow.find_element(by=By.XPATH,
                                        value='//*[@id="hp_container"]/div[2]/div/div[3]/div[3]/div[2]/span/div[1]/div/div/div/div[2]/div[1]/div[5]/div/div[2]')
        order_.click()
        # 填写乘机人信息

        passenger_num = len(passenger_info)  # 乘客人数
        # 根据乘客人数点击 新增乘机人 按钮
        add_passenger_bt = self.brow.find_element(by=By.XPATH, value='.//span[@class="psg-passenger__add-text"]')
        # for i in range(passage_num - 1):
        #     add_passage_bt.click()
        #     time.sleep(0.5)
        # 填写乘机人信息
        for i in range(passenger_num):
            # 姓名
            p_name = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_name_{i}"]')
            p_name.send_keys(passenger_info[i][0])

            # 身份证
            p_id = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_card_no_{i}"]')
            p_id.send_keys(passenger_info[i][1])

            # 电话号码 (可不填)
            p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_cellphone_{i}"]')
            p_cellphone.send_keys(passenger_info[i][2])
            if i < passenger_num - 1:
                add_passenger_bt.click()
                time.sleep(0.5)

        save_order = self.brow.find_element(by=By.XPATH, value='.//a[@id="J_saveOrder"]')
        save_order.click()

        flight_info = self.brow.find_element(by=By.XPATH, value='.//div[@id="J_flightInfo"]').get_attribute(
            "textContent")

        logger.info(flight_info)
        total_price = self.brow.find_element(by=By.XPATH, value='.//span[@id="J_totalPrice"]').get_attribute(
            "textContent")

        logger.debug(total_price)
        logger.info('成功生成订单，向指定邮箱发送通知')
        self.handle(from_, to_, date, flight_airline, depart, arrival)
        time.sleep(5)
        # self.brow.quit()

    def handle(self, from_, to_, date, flight_airline, depart, arrival):
        content = f'用户您好，系统已为您抢到在 {date} {depart[0]} 出发，由 {from_}{depart[1]} 去往 {to_}{arrival[2]} 的航班票\n 详细航班信息以及乘机人信息请访问 https://passport.ctrip.com/user/login  进行查看'
        se = Send_QQ_Email('1784800289@qq.com', content)
        se.send()
        logger.info('邮件发送成功')


if __name__ == '__main__':
    # date = ['2022', '06', '21']
    # passenger_info = [['李欢', '500221200208274316', '15723114723'],
    #                   ['许茂森', '500222199908184320', '15310829546']]
    # account = '15730168247'
    # password = '11903990112ys.'
    # class_option = 1
    # depart_option = 1
    # lg = Subprice(account, password)
    # lg.search_info('重庆', '北京', date, depart_option, class_option, passenger_info)

    # current_datetime = datetime.datetime.now().strftime('%Y-%m-%d')
    # ret = os.system("ping baidu.com -n 1")
    # print(ret)
    ret = subprocess.run("ping www.baidu.com -n 1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    a = ret.returncode
    if a == 200:
        print(1)
    else:
        print(2)
