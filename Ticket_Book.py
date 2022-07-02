import logging.config
import re
import subprocess
import time
from time import sleep

from PIL import Image
from lxml import etree
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from PyQt5.QtCore import QThread, pyqtSignal

from Send_Email import Send_QQ_Email
from chaojiying import Chaojiying_Client
from dpi_get import WindowsCommon

# 配置无头浏览器参数以及规避检测
edge_options = Options()
edge_options.use_chromium = True
edge_options.add_argument('--headless')
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--disable-blink-features=AutomationControlled')
edge_options.add_argument(
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36 Edg/103.0.1264.37')

# s = Service('./msedgedriver.exe')

s = Service('../msedgedriver.exe')
# 配置文件实现日志
# 设置一个日志文件，app.log用于记录程序正常运行日志
logging.config.fileConfig('./logging.conf')
logger = logging.getLogger('applog')
root_logger = logging.getLogger()


class Subprice(QThread):
    mySignal = pyqtSignal(str)

    def __init__(self, account, password, second, from_, to_, depart_date, back_date, depart_time_limit,
                 back_time_limit,
                 class_option,
                 ticket_type,
                 passenger_info, email_add):
        super(Subprice, self).__init__()
        self.url = ''
        self.second = second  # 每隔多少秒进行轮询
        self.from_ = from_  # 出发地点
        self.to_ = to_  # 目的地
        self.depart_date = depart_date  # 出发日期 ['2022','07','03']
        self.back_date = back_date  # 返程日期
        self.depart_time_limit = depart_time_limit  # 出发时间段限制 ['12','14']
        self.back_time_limit = back_time_limit  # 返程时间段限制
        self.class_option = class_option  # 机票类型 1：经济舱 2：商务舱
        self.ticket_type = ticket_type  # 0：单程票 1:往返票
        self.passenger_info = passenger_info  # 乘客信息
        self.email_add = email_add
        self.account = account
        self.password = password

    def login(self):

        logger.info(f'开始登陆账户 {self.account}')
        self.mySignal.emit(f'开始登陆账户 {self.account}')

        user_name = self.brow.find_element(by=By.XPATH, value='//*[@id="nloginname"]')  # 用户名标签的定位
        user_passowrd = self.brow.find_element(by=By.XPATH, value='//*[@id="npwd"]')  # 用户密码的登录
        user_name.click()
        user_name.send_keys(self.account)  # 填入账号

        user_passowrd.click()
        user_passowrd.send_keys(self.password)  # 填入密码
        login_aggree_b2 = self.brow.find_element(by=By.XPATH, value='//*[@id="normalview"]/form/p/input')  # 同意登录的定位
        login_aggree_b2.click()
        login_b2 = self.brow.find_element(by=By.XPATH, value='//*[@id="nsubmit"]')  # 账号登录的登录按钮定位
        login_b2.click()
        flag = True

        # # 判断登录验证码类型 或没有验证码
        while flag:
            # 捕获滑块验证
            start_time = time.time()
            try:
                self.brow.switch_to.default_content()
                time.sleep(2)
                ver_scroll = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div/div[4]/div[3]')
                flag = True
                dialog_info = self.brow.find_element(by=By.XPATH,
                                                     value='//*[@id="sliderddnormal"]/div/div[4]/div[5]/span').get_attribute(
                    "textContent")
                if dialog_info.strip() == '拖动滑块填充拼图':
                    logger.info('正在破解滑块验证码')
                    self.mySignal.emit('正在破解滑块验证码')
                    time.sleep(1)
                    ver_scroll.click()
                else:
                    raise Exception
            except:
                try:
                    icon_ = self.brow.find_element(by=By.XPATH,
                                                   value='//*[@id="sliderddnormal"]/div/div[4]/div[2]/div/span/span/span[1]')
                    flag = True
                    # time.sleep(6)
                    # self.click_code_old()
                    code_img_ele = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
                    element = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
                    login_bt = self.brow.find_element(by=By.XPATH,
                                                      value='//*[@id="hp_nfes_accountbar"]/li[1]/div/button')
                    self.click_code(code_img_ele, element, login_bt, 9004)
                except:
                    flag = False
            if not flag:
                end_time = time.time()
                if end_time - start_time >= 2:  # 如果超过 几秒 未捕获到弹窗 判断当前网络状态
                    ret = subprocess.run("ping www.taobao.com -n 1", shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    if ret.returncode == 0:  # 当前网络良好,则代表已成功登录，无验证码弹窗
                        break
                    else:  # 网络状态不好，应该抛出异常，这里暂时不写
                        logger.info('当前网络状态较差，请检查网络状态，重新登录。')
                        self.mySignal.emit('当前网络状态较差，请检查网络状态，重新登录。')
                        return False
                else:
                    flag = True

        try:
            self.brow.switch_to.default_content()
            time.sleep(1)
            personErr_info = self.brow.find_element(by=By.XPATH, value='//*[@id="nerr"]').get_attribute(
                "textContent")
            if '密码不正确' in personErr_info:
                logger.info('用户名或密码错误，请检查之后重新登录')
                self.mySignal.emit('用户名或密码错误，请检查之后重新登录')
                return False
            else:
                pass
        except:
            pass

        logger.info(f'账户 {self.account} 已成功登录')
        self.mySignal.emit(f'账户 {self.account} 已成功登录')
        sleep(0.5)

        self.brow.get('https://flights.ctrip.com/online/channel/domestic')
        return True

    # 滚轮验证码的点击因为不需要滚轮的点击

    # 滑块验证码的验证

    # 顺序点击的验证码

    def click_code(self, code_img_ele, element, login_bt, code_type):
        logger.info('正在破解图标验证码')
        self.mySignal.emit('正在破解图标验证码')
        # 首先截图
        sleep(3)
        self.brow.save_screenshot('aa.png')  # 对当前页面保存
        # code_img_ele = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
        location = code_img_ele.location  # x,y
        # print(location)
        logger.debug(f'验证码图片坐标{location}')
        size = code_img_ele.size  # size返回的是验证码标签返回的长和宽
        logger.debug(f'验证码标签的长和宽{size}')
        # print(size)
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
        # logger.info()
        # print(rangle)
        logger.debug(f'验证码图片的坐标{rangle}')
        i = Image.open('./aa.png')
        code_img_name = 'code.png'
        frame = i.crop(rangle)
        frame.save(code_img_name)
        chaojiying = Chaojiying_Client("frants", "123456", "934829")
        im = open('code.png', 'rb').read()
        dic = chaojiying.PostPic(im, code_type)['pic_str']
        logger.debug(f'验证码点击坐标 {dic}')
        # print('dic:', dic)
        # 对获取到的坐标进行分割按'|'
        if '|' in dic:
            groups = dic.split('|')
            locations = [[int(number) for number in group.split(',')] for group in groups]  # 将坐标
        else:
            one_local = dic.split(',')
            locations = [[one_local[0], one_local[1]]]

        # element = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
        for location_1 in locations:
            x = location_1[0] / dpi_num
            y = location_1[1] / dpi_num
            ActionChains(self.brow).move_to_element_with_offset(element, x, y).click().perform()
        # login_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="hp_nfes_accountbar"]/li[1]/div/button')
        login_bt.click()

    def click_code_old(self):
        logger.info('正在破解图标验证码')
        self.mySignal.emit('正在破解图标验证码')
        # 首先截图
        sleep(3)
        self.brow.save_screenshot('aa.png')  # 对当前页面保存
        code_img_ele = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div')
        location = code_img_ele.location  # x,y
        # print(location)
        logger.debug(f'验证码图片坐标{location}')
        size = code_img_ele.size  # size返回的是验证码标签返回的长和宽
        logger.debug(f'验证码标签的长和宽{size}')
        # print(size)
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
        # logger.info()
        # print(rangle)
        logger.debug(f'验证码图片的坐标{rangle}')
        i = Image.open('./aa.png')
        code_img_name = 'code.png'
        frame = i.crop(rangle)
        frame.save(code_img_name)
        chaojiying = Chaojiying_Client("frants", "123456", "934829")
        im = open('code.png', 'rb').read()
        dic = chaojiying.PostPic(im, 9004)['pic_str']
        logger.debug(f'验证码点击坐标 {dic}')
        # print('dic:', dic)
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

    def generate_order(self):
        status = False
        if self.ticket_type == 0:  # 表示单程票
            status = self.generate_one_way_order()
        else:
            status = self.generate_round_order()
        if status:
            return True
        else:
            return False

    # 单程机票
    def generate_one_way_order(self):
        # 需传入 起始地点 目的地 日期 选择的起飞时间段 舱位等级
        # depart_option 1：代表6点到12点 2：代表12点到18点 3：代表18点到24点
        # self.class_option 1:经济舱 2:商务舱/头等舱
        # self.depart_date = '-'.join(self.depart_date)  # self.depart_date 形如['2022','06','18']
        # 时间限制
        st_t = int(self.depart_time_limit[0])
        end_t = int(self.depart_time_limit[1])

        self.class_option_dic = {1: '经济舱', 2: '商务舱/头等舱'}
        logger.info(
            f'开始查找 在 {self.depart_date} {st_t}点 到 {end_t}点 时间段，由 {self.from_} 去往 {self.to_} {self.class_option_dic[self.class_option]}的 单程机票')
        self.mySignal.emit(
            f'开始查找 在 {self.depart_date} {st_t}点 到 {end_t}点 时间段，由 {self.from_} 去往 {self.to_} {self.class_option_dic[self.class_option]}的 单程机票')
        time.sleep(0.5)
        # 出发地点输入框
        start = time.time()
        while True:
            try:
                self.from_lable = self.brow.find_element(by=By.XPATH,
                                                         value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[1]/div/div/div[1]/input')
                break
            except Exception as e:
                end = time.time()
                if end - start > 15:
                    ret = subprocess.run("ping www.taobao.com -n 1", shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    if ret.returncode != 0:
                        logger.info('网络错误，请检查网络重试')
                        self.mySignal.emit('网络错误，请检查网络重试')
                        return False

        self.from_lable.click()
        self.from_lable.send_keys(self.from_)

        self.to_lable = self.brow.find_element(by=By.XPATH,
                                               value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[3]/div/div/div[1]/input')
        self.to_lable.click()
        self.to_lable.send_keys(self.to_)
        self.to_lable.send_keys(Keys.ENTER)

        time.sleep(1)
        dc_button = self.brow.find_element(by=By.XPATH, value='//*[@id="searchForm"]/div/div/div/div[1]/ul/li[1]/span')
        dc_button.click()

        time.sleep(1)
        search_button = self.brow.find_element(by=By.XPATH, value='//*[@id="searchForm"]/div/button')
        search_button.click()

        # 指定日期
        time.sleep(1)
        # self.depart_date = '-'.join(self.depart_date)  # self.depart_date 形如['2022','06','18']
        url = self.brow.current_url
        pattern = re.compile('(?<=depdate=).*?(?=&cabin)')
        url = re.sub(pattern, self.depart_date, url)
        self.url = url
        self.brow.get(url)
        # self.brow.refresh()
        # 疫情弹窗处理
        try:
            self.brow.implicitly_wait(2)
            yiqing_button = self.brow.find_element(by=By.XPATH, value='//*[@id="outerContainer"]/div/div[3]/div')
            yiqing_button.click()
        except:
            pass
        # 判断输入城市与搜索城市是否匹配，以此判断用户地点是否输入错误

        dep_info = self.brow.find_element(by=By.XPATH,
                                          value='//div[@class="form-item-v3 flt-depart      "]//input[@class="form-input-v3"]').get_attribute(
            'value')

        arr_info = self.brow.find_element(by=By.XPATH,
                                          value='//div[@class="form-item-v3 flt-arrival     "]//input[@class="form-input-v3"]').get_attribute(
            'value')
        if self.from_ in dep_info and self.to_ in arr_info:
            pass
        else:
            logger.info('出发地点或目的地点有误，请检查重新输入')
            self.mySignal.emit('出发地点或目的地点有误，请检查重新输入')
            return False

        # 爬取航班信息前的处理

        time.sleep(2)
        # 直飞选项
        while True:
            try:
                zhifei_button = self.brow.find_element(by=By.XPATH,
                                                       value='//*[@id="hp_container"]/div[2]/div/div[3]/div[2]/div/ul[1]/li[1]/div/span')
                break
            except:
                pass
        zhifei_button.click()

        # 选择舱位 经济舱 or 商务舱/头等舱
        # self.class_option = 1  # 1：经济舱 2：商务舱/头等舱 默认为1

        class_grade = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_class_grade"]/div')
        class_grade.click()
        class_ul = self.brow.find_element(by=By.XPATH,
                                          value=f'.//ul[@id="filter_group_class_grade__default"]/li[{self.class_option}]')

        class_ul.click()
        class_grade.click()

        logger.info('正在获取航班信息...,筛选符合条件的航班')
        self.mySignal.emit('正在获取航班信息...,筛选符合条件的航班')
        # js脚本循环几次向下滑动,便于获取动态加载数据 需注意一次不能滑动太多，否则数据加载不全
        for i in range(8):
            time.sleep(0.5)
            self.brow.execute_script('window.scrollBy(0,500)')
        time.sleep(2)
        # 回到顶部
        self.brow.execute_script('window.scrollTo(0,0)')
        flight_index = 0

        # 符合条件标志位
        sat_flag = False
        while True:
            try:
                # 起飞时间
                depart_time = self.brow.find_element(by=By.XPATH,
                                                     value=f'//div[@index="{flight_index}"]//div[@class="depart-box'
                                                           f'"]/div[@class="time"]').get_attribute(
                    'textContent')

                f_t = int(depart_time.split(':')[0])
                if st_t <= f_t < end_t:
                    # 满足时间条件，获取当前航班的其他信息
                    f'//div[@index="{flight_index}"]//div[@class="depart-box"]'
                    # 航空公司名称
                    airline_company = self.brow.find_element(by=By.XPATH,
                                                             value=f'//div[@index="{flight_index}"]//div['
                                                                   f'@class="airline-name"]/span').get_attribute(
                        'textContent')
                    # 航班号
                    plane_no = self.brow.find_element(by=By.XPATH,
                                                      value=f'//div[@index="{flight_index}"]//span['
                                                            f'@class="plane-No"]').get_attribute(
                        'textContent')
                    # 飞机类型
                    plane_type = self.brow.find_element(by=By.XPATH,
                                                        value=f'//div[@index="{flight_index}"]//span['
                                                              f'@class="plane-No"]/span').get_attribute(
                        'textContent')
                    # 预计到达时间
                    arrive_time = self.brow.find_element(by=By.XPATH,
                                                         value=f'//div[@index="{flight_index}"]//div[@class="arrive-box'
                                                               f'"]/div[@class="time"]').get_attribute(
                        'textContent')
                    # 出发机场
                    depart_airport = self.brow.find_element(by=By.XPATH,
                                                            value=f'//div[@index="{flight_index}"]//div['
                                                                  f'@class="depart-box"]/div['
                                                                  f'@class="airport"]/span').get_attribute(
                        'textContent')
                    # 到达机场
                    arrive_airport = self.brow.find_element(by=By.XPATH,
                                                            value=f'//div[@index="{flight_index}"]//div['
                                                                  f'@class="arrive-box"]/div['
                                                                  f'@class="airport"]/span').get_attribute(
                        'textContent')
                    sat_flag = True
                    info = f'匹配到符合条件航班 {airline_company} {plane_no} {plane_type} 出发时间 {depart_time} 预计到达时间 {arrive_time}'
                    logger.info(info)
                    self.mySignal.emit(info)
                    break
                else:
                    flight_index += 1
            except:
                break
        if not sat_flag:
            info = f'未寻找到合适的航班，请更改条件重新查找'
            logger.info(info)
            self.mySignal.emit(info)
            return False

        logger.info('开始生成订单')
        self.mySignal.emit('开始生成订单')
        # # 生成订单
        expend_all_price = self.brow.find_element(by=By.XPATH,
                                                  value=f'//div[@index="{flight_index}"]//button[@class="btn btn-book"]')

        # expend_all_price.click()
        self.brow.execute_script("arguments[0].click();", expend_all_price)

        # 判断当前航班是否有购票限制
        i = 0
        while True:
            try:
                tag_limit = self.brow.find_element(by=By.XPATH, value=f'//span[@id="tagLimit_0_{i}"]')
                tag_content = tag_limit.get_attribute('textContent')
                logger.info(tag_content)
                self.mySignal.emit(tag_content)
                i += 1
            except:
                break

        order_ = self.brow.find_element(by=By.XPATH,
                                        value=f'//*[@id="{flight_index}_{i}"]')
        order_text = order_.get_attribute("textContent")
        print(i)
        if order_text == '选购':
            # order_.click()
            self.brow.execute_script('arguments[0].click();', order_)
            time.sleep(1)

            order_expend = self.brow.find_element(by=By.XPATH,
                                                  value=f'//*[@id="hp_container"]//div[@index="{flight_index}"]//div[@class="seat-row seat-row-v3 has-related-price"]/div/div[2]/button')


            order_expend.click()
        # order_.click()

        '//*[@id="hp_container"]/div[2]/div/div[3]/div[3]/div[2]/span/div[3]/div/div/div/div[2]/span[1]/div/div[1]/div[2]/button'
        '//*[@id="hp_container"]/div[2]/div/div[3]/div[3]/div[2]/span/div[3]/div/div/div[2]/span[1]/div/div[1]/div[2]/button'
        self.brow.execute_script('arguments[0].click();', order_)

        # 捕获机票售完弹窗信息
        try:
            sold_out_info = self.brow.find_element(by=By.XPATH, value='//div[@div="popup-info"]')
            # '您预订的航班机票已售完，请重新查询预订。'
            if '已售完' in sold_out_info.get_attribute('textContent').strip():
                # re_search_bt.click()
                logger.info('当前航班没有余票')
                self.mySignal.emit('当前航班没有余票')

        except:
            logger.info('当前航班有余票')
            self.mySignal.emit('当前航班有余票')

        try:
            # 预防登录没有成功，这里再次捕捉登录弹窗
            self.brow.switch_to.default_content()
            time.sleep(1)
            # 账户名称
            nloginame = self.brow.find_element(by=By.XPATH, value='//*[@id="nloginname"]')
            # 账户密码
            npwd = self.brow.find_element(by=By.XPATH, value='//*[@id="npwd"]')

            nloginame.send_keys(self.account)
            npwd.send_keys(self.password)

            # 登录按钮
            nsubmit = self.brow.find_element(by=By.XPATH, value='//*[@id="nsubmit"]')
            nsubmit.click()
            time.sleep(3)
            # 判断用户密码是否正确
            try:
                self.brow.switch_to.default_content()
                time.sleep(1)
                personErr_info = self.brow.find_element(by=By.XPATH, value='//*[@id="nerr"]').get_attribute(
                    "textContent")
                if '密码不正确' in personErr_info:
                    logger.info('用户名或密码错误，请检查之后重新登录')
                    self.mySignal.emit('用户名或密码错误，请检查之后重新登录')
                    return False
                else:
                    pass
            except:
                pass
        except:
            pass

        # 填写乘机人信息
        passenger_num = len(self.passenger_info)  # 乘客人数
        # 根据乘客人数点击 新增乘机人 按钮
        add_passenger_bt = self.brow.find_element(by=By.XPATH, value='.//span[@class="psg-passenger__add-text"]')
        # 填写乘机人信息
        succ_count = 0
        for i in range(passenger_num):

            p_name = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_name_{succ_count}"]')
            p_id = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_card_no_{succ_count}"]')
            try:
                p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_cellphone_{succ_count}"]')
            except:
                p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_contact_{succ_count}"]')
            # 姓名
            p_name.click()
            p_name.clear()
            p_name.send_keys(self.passenger_info[i][0])
            # 身份证
            time.sleep(0.2)
            p_id.click()
            p_id.clear()
            p_id.send_keys(self.passenger_info[i][1])
            # 电话号码 (可不填)
            time.sleep(0.2)
            p_cellphone.click()
            p_cellphone.clear()
            p_cellphone.send_keys(self.passenger_info[i][2])
            p_cellphone.send_keys(Keys.ENTER)

            # # 判断 当前乘车人信息是否正确
            # time.sleep(1)
            error_flag = False
            try:
                p_id_error_info = self.brow.find_element(by=By.XPATH,
                                                         value=f'//*[@id="passengerMain"]/div[{succ_count + 1}]/div[2]/div/div[3]/div[2]/div[4]/span').get_attribute(
                    'textContent')
                if '正确' in p_id_error_info:
                    logger.info(f'乘客 {self.passenger_info[i][0]} 身份证信息有误，系统将不为该乘客进行购票')
                    self.mySignal.emit(f'乘客 {self.passenger_info[i][0]} 身份证信息有误，系统将不为该乘客进行购票')
                    error_flag = True
            except:
                pass

            if not error_flag:
                try:
                    p_cell_info = self.brow.find_element(by=By.XPATH,
                                                         value=f'//*[@id="passengerMain"]/div[{succ_count + 1}]/div[2]/div/div[6]/div[2]/div/span').get_attribute(
                        'textContent')
                    if '正确' in p_cell_info:
                        logger.info(f'乘客 {self.passenger_info[i][0]} 电话信息有误，系统将不为该乘客进行购票')
                        self.mySignal.emit(f'乘客 {self.passenger_info[i][0]} 电话信息有误，系统将不为该乘客进行购票')
                        error_flag = True
                except:
                    pass
            # 出现错误，删除当前已填写的乘车人

            if error_flag:
                if i == passenger_num - 1:
                    de_bt = self.brow.find_element(by=By.XPATH,
                                                   value=f'//*[@id="passengerMain"]/div[{succ_count + 1}]/a/span')
                    self.brow.execute_script('arguments[0].click();', de_bt)
            else:
                succ_count += 1

            if i < passenger_num - 1 and not error_flag:
                add_passenger_bt.click()
                time.sleep(0.5)
            # if i < passenger_num - 1:
            #     add_passenger_bt.click()
            #     time.sleep(0.5)

        save_order = self.brow.find_element(by=By.XPATH, value='.//a[@id="J_saveOrder"]')
        time.sleep(0.5)

        save_order.click()

        flight_info = self.brow.find_element(by=By.XPATH, value='.//div[@id="J_flightInfo"]').get_attribute(
            "textContent")

        logger.info(flight_info)
        self.mySignal.emit(flight_info)
        total_price = self.brow.find_element(by=By.XPATH, value='.//span[@id="J_totalPrice"]').get_attribute(
            "textContent")
        logger.debug(total_price)

        # 判断有无滑块验证
        self.brow.switch_to.default_content()
        time.sleep(2)
        try:

            # '滑块'
            sliding_block = self.brow.find_element(by=By.XPATH,
                                                   value='//*[@id="J_slider_verification"]/div[1]/div[2]/div/i[1]')
            logger.info('捕获到滑块验证弹窗')
            self.mySignal.emit('捕获到滑块验证弹窗')
            slider_area = self.brow.find_element(by=By.XPATH, value='//*[@id="J_slider_verification"]/div[1]/div[4]')

            # ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
            #                                                 sliding_block.size['height']).perform()
            distance = slider_area.size['width'] / 4
            for i in range(3):
                ActionChains(self.brow).click_and_hold(sliding_block).move_by_offset(distance, 0).perform()
                distance += distance
                time.sleep(0.2)
            # ActionChains(self.brow).click_and_hold(sliding_block).release().perform()

            # 判断有无第二重图标验证
            try:
                self.brow.switch_to.default_content()
                time.sleep(2)
                code_image = self.brow.find_element(by=By.XPATH,
                                                    value='//*[@id="J_slider_verification-choose"]/div[2]')
                element = self.brow.find_element(by=By.XPATH,
                                                 value='//*[@id="J_slider_verification-choose"]/div[2]/div[3]/img')

                login_bt = self.brow.find_element(by=By.XPATH,
                                                  value='//*[@id="J_slider_verification-choose"]/div[2]/div[4]/a')
                self.click_code(code_image, element, login_bt, 2003)
            except:
                logger.info('无图标验证')
                self.mySignal.emit('无图标验证')

            time.sleep(0.2)
            '//button[@i-id="继续提交"]'
            continue_bt = self.brow.find_element(by=By.XPATH, value='//button[@i-id="继续提交"]')
            # continue_bt.click()
            self.brow.execute_script('arguments[0].click();', continue_bt)
        except:
            logger.info('未捕获到验证弹窗')
            self.mySignal.emit('未捕获到验证弹窗')

        ordered_flag = False
        try:
            time.sleep(2)
            ordered = self.brow.find_element(by=By.XPATH, value='//*[@id="J_step2"]/div[1]/div')
            ordered_content = ordered.get_attribute("textContent")
            if '完成支付' in ordered_content.strip():
                ordered_flag = True
                logger.info('成功生成订单，向指定邮箱发送通知')
                self.mySignal.emit('成功生成订单，向指定邮箱发送通知')
                pass
            else:
                logger.info('订单生成失败,请重新购买')
                self.mySignal.emit('订单生成失败,请重新购买')
                return False
        except Exception:
            logger.info('订单生成失败,请重新购买')
            self.mySignal.emit('订单生成失败,请重新购买')
            return False

        if ordered_flag:
            content = f'用户您好，系统已为您抢到 {self.depart_date} {depart_time} 由 {self.from_}{depart_airport} 飞往 {self.to_}{arrive_airport} 预计{arrive_time}到达\n' \
                      f'的单程航班票。详细信息以及请访问 https://passport.ctrip.com/user/login 请尽快完成支付。'
            se = Send_QQ_Email(self.email_add, content)
            se.send()
            logger.info('邮件发送完成')
            self.mySignal.emit('邮件发送完成')

            return True

    # 往返机票
    def generate_round_order(self):
        # 需传入 起始地点 目的地 日期 选择的起飞时间段 舱位等级
        # depart_option 1：代表6点到12点 2：代表12点到18点 3：代表18点到24点
        # self.class_option 1:经济舱 2:商务舱/头等舱
        # self.depart_date = '-'.join(self.depart_date)  # date 形如['2022','06','18']
        # self.back_date = '-'.join(self.back_date)
        # 时间限制
        depart_st_t = int(self.depart_time_limit[0])
        depart_end_t = int(self.depart_time_limit[1])

        back_st_t = int(self.back_time_limit[0])
        back_end_t = int(self.back_time_limit[1])

        logger.info(
            f'开始查找 在 {self.depart_date} {depart_st_t}点 到 {depart_end_t}点 时间段，由 {self.from_} 去往 {self.to_} '
            f'在 {self.back_date}  {back_st_t}点 到 {back_end_t}点时间段 由 {self.to_} 去往 {self.from_}的 往返机票')
        self.mySignal.emit(
            f'开始查找 在 {self.depart_date} {depart_st_t}点 到 {depart_end_t}点 时间段，由 {self.from_} 去往 {self.to_} '
            f'在 {self.back_date}  {back_st_t}点 到 {back_end_t}点时间段 由 {self.to_} 去往 {self.from_}的 往返机票')
        time.sleep(1)
        # 出发地点输入框
        start = time.time()
        while True:
            try:
                self.from_lable = self.brow.find_element(by=By.XPATH,
                                                         value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[1]/div/div/div[1]/input')
                break
            except Exception as e:
                end = time.time()
                if end - start > 15:
                    ret = subprocess.run("ping www.taobao.com -n 1", shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    if ret.returncode != 0:
                        logger.info('网络错误，请检查网络重试')
                        self.mySignal.emit('网络错误，请检查网络重试')
                        return False

        self.from_lable.click()
        self.from_lable.send_keys(self.from_)

        self.to_lable = self.brow.find_element(by=By.XPATH,
                                               value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[3]/div/div/div[1]/input')
        self.to_lable.click()
        self.to_lable.send_keys(self.to_)
        self.to_lable.send_keys(Keys.ENTER)

        time.sleep(1)
        round_button = self.brow.find_element(by=By.XPATH,
                                              value='//*[@id="searchForm"]/div/div/div/div[1]/ul/li[2]/span')
        round_button.click()

        time.sleep(1)
        search_button = self.brow.find_element(by=By.XPATH, value='//*[@id="searchForm"]/div/button')
        search_button.click()

        # 指定日期
        # date = '-'.join(date)  # date 形如['2022','06','18']
        url = self.brow.current_url
        pattern = re.compile('(?<=depdate=).*?(?=&cabin)')
        url = re.sub(pattern, self.depart_date + '_' + self.back_date, url)
        self.url = url
        self.brow.get(url)
        # 疫情弹窗处理
        try:
            self.brow.implicitly_wait(2)
            yiqing_button = self.brow.find_element(by=By.XPATH, value='//*[@id="outerContainer"]/div/div[3]/div')
            yiqing_button.click()
        except:
            pass

        # 判断输入城市与搜索城市是否匹配，以此判断用户地点是否输入错误
        '//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[1]/div/div/div[1]/input'
        dep_info = self.brow.find_element(by=By.XPATH,
                                          value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[1]/div/div/div[1]/input').get_attribute(
            'value')
        '//div[@class="form-item-v3 flt-depart active show-animate    "]//input[@class="form-input-v3"]'
        '//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[1]/div/div/div[1]/input'
        arr_info = self.brow.find_element(by=By.XPATH,
                                          value='//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[3]/div/div/div[1]/input').get_attribute(
            'value')
        '//div[@class="form-item-v3 flt-arrival     "]//input[@class="form-input-v3"]'
        '//*[@id="searchForm"]/div/div/div/div[2]/div[1]/div/div[3]/div/div/div[1]/input'
        if self.from_ in dep_info and self.to_ in arr_info:
            pass
        else:
            logger.info('出发地点或目的地点有误，请检查重新输入')
            self.mySignal.emit('出发地点或目的地点有误，请检查重新输入')
            return False
        # 爬取航班信息前的处理

        # 直飞选项
        while True:
            try:
                zhifei_button = self.brow.find_element(by=By.XPATH,
                                                       value='//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[1]/div/ul[1]/li[1]/div/span')
                break
            except:
                pass
        zhifei_button.click()

        # 选择舱位 经济舱 or 商务舱/头等舱
        # self.class_option = 1  # 1：经济舱 2：商务舱/头等舱 默认为1

        class_grade = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_class_grade"]/div')
        class_grade.click()
        class_ul = self.brow.find_element(by=By.XPATH,
                                          value=f'.//ul[@id="filter_group_class_grade__default"]/li[{self.class_option}]')
        class_ul.click()
        class_grade.click()

        logger.info('正在获取去程航班信息...,筛选符合条件的航班')
        self.mySignal.emit('正在获取去程航班信息...,筛选符合条件的航班')
        # js脚本循环几次向下滑动,便于获取动态加载数据 需注意一次不能滑动太多，否则数据加载不全
        for i in range(8):
            time.sleep(0.5)
            self.brow.execute_script('window.scrollBy(0,500)')
        time.sleep(2)
        # 回到顶部
        self.brow.execute_script('window.scrollTo(0,0)')
        flight_index = 0

        # 符合条件标志位
        sat_flag = False
        while True:
            try:
                # 起飞时间
                depart_time = self.brow.find_element(by=By.XPATH,
                                                     value=f'//div[@index="{flight_index}"]//div[@class="depart-box'
                                                           f'"]/div[@class="time"]').get_attribute(
                    'textContent')

                f_t = int(depart_time.split(':')[0])
                if depart_st_t <= f_t < depart_end_t:
                    # 满足时间条件，获取当前航班的其他信息
                    f'//div[@index="{flight_index}"]//div[@class="depart-box"]'
                    # 航空公司名称
                    airline_company = self.brow.find_element(by=By.XPATH,
                                                             value=f'//div[@index="{flight_index}"]//div['
                                                                   f'@class="airline-name"]/span').get_attribute(
                        'textContent')
                    # 航班号
                    plane_no = self.brow.find_element(by=By.XPATH,
                                                      value=f'//div[@index="{flight_index}"]//span['
                                                            f'@class="plane-No"]').get_attribute(
                        'textContent')
                    # 飞机类型
                    plane_type = self.brow.find_element(by=By.XPATH,
                                                        value=f'//div[@index="{flight_index}"]//span['
                                                              f'@class="plane-No"]/span').get_attribute(
                        'textContent')
                    # 预计到达时间
                    arrive_time = self.brow.find_element(by=By.XPATH,
                                                         value=f'//div[@index="{flight_index}"]//div[@class="arrive-box'
                                                               f'"]/div[@class="time"]').get_attribute(
                        'textContent')
                    # 出发机场
                    depart_airport = self.brow.find_element(by=By.XPATH,
                                                            value=f'//div[@index="{flight_index}"]//div['
                                                                  f'@class="depart-box"]/div['
                                                                  f'@class="airport"]/span').get_attribute(
                        'textContent')
                    # 到达机场
                    arrive_airport = self.brow.find_element(by=By.XPATH,
                                                            value=f'//div[@index="{flight_index}"]//div['
                                                                  f'@class="arrive-box"]/div['
                                                                  f'@class="airport"]/span').get_attribute(
                        'textContent')
                    sat_flag = True
                    info = f'匹配到符合条件航班 {airline_company} {plane_no} {plane_type} 出发时间 {depart_time} 预计到达时间 {arrive_time}'
                    logger.info(info)
                    self.mySignal.emit(info)
                    break
                else:
                    flight_index += 1
            except:
                break
        if not sat_flag:
            info = f'未寻找到合适的航班，请更改条件重新查找'
            logger.info(info)
            self.mySignal.emit(info)
            return False

        qc_bt = self.brow.find_element(by=By.XPATH, value=f'//div[@index="{flight_index}"]//div[@class="btn btn-book"]')
        self.brow.execute_script('arguments[0].click();', qc_bt)

        # 获取返程航班信息
        time.sleep(3)
        while True:
            try:
                zhifei_button = self.brow.find_element(by=By.XPATH,
                                                       value='//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[1]/div/ul[1]/li[1]/div/span')
                break
            except:
                pass
        zhifei_button.click()
        class_grade = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_class_grade"]/div')
        class_grade.click()
        class_ul = self.brow.find_element(by=By.XPATH,
                                          value=f'.//ul[@id="filter_group_class_grade__default"]/li[{self.class_option}]')
        #class_ul.click()
        self.brow.execute_script('arguments[0].click();',class_ul)
        class_grade.click()

        logger.info('正在获取返程航班信息...,筛选符合条件的航班')
        self.mySignal.emit('正在获取返程航班信息...,筛选符合条件的航班')
        # js脚本循环几次向下滑动,便于获取动态加载数据 需注意一次不能滑动太多，否则数据加载不全
        for i in range(8):
            time.sleep(0.5)
            self.brow.execute_script('window.scrollBy(0,500)')
        time.sleep(2)
        # 回到顶部
        self.brow.execute_script('window.scrollTo(0,0)')
        flight_index = 0

        # 符合条件标志位
        sat_flag = False
        while True:
            try:
                # 起飞时间
                back_time = self.brow.find_element(by=By.XPATH,
                                                   value=f'//div[@index="{flight_index}"]//div[@class="depart-box'
                                                         f'"]/div[@class="time"]').get_attribute(
                    'textContent')

                f_t = int(back_time.split(':')[0])
                if back_st_t <= f_t < back_end_t:
                    # 满足时间条件，获取当前航班的其他信息
                    f'//div[@index="{flight_index}"]//div[@class="depart-box"]'
                    # 航空公司名称
                    back_airline_company = self.brow.find_element(by=By.XPATH,
                                                                  value=f'//div[@index="{flight_index}"]//div['
                                                                        f'@class="airline-name"]/span').get_attribute(
                        'textContent')
                    # 航班号
                    back_plane_no = self.brow.find_element(by=By.XPATH,
                                                           value=f'//div[@index="{flight_index}"]//span['
                                                                 f'@class="plane-No"]').get_attribute(
                        'textContent')
                    # 飞机类型
                    back_plane_type = self.brow.find_element(by=By.XPATH,
                                                             value=f'//div[@index="{flight_index}"]//span['
                                                                   f'@class="plane-No"]/span').get_attribute(
                        'textContent')
                    # 预计到达时间
                    back_arrive_time = self.brow.find_element(by=By.XPATH,
                                                              value=f'//div[@index="{flight_index}"]//div[@class="arrive-box'
                                                                    f'"]/div[@class="time"]').get_attribute(
                        'textContent')
                    # 出发机场
                    back_depart_airport = self.brow.find_element(by=By.XPATH,
                                                                 value=f'//div[@index="{flight_index}"]//div['
                                                                       f'@class="depart-box"]/div['
                                                                       f'@class="airport"]/span').get_attribute(
                        'textContent')
                    # 到达机场
                    back_arrive_airport = self.brow.find_element(by=By.XPATH,
                                                                 value=f'//div[@index="{flight_index}"]//div['
                                                                       f'@class="arrive-box"]/div['
                                                                       f'@class="airport"]/span').get_attribute(
                        'textContent')
                    sat_flag = True
                    info = f'匹配到符合条件航班 {back_airline_company} {back_plane_no} {back_plane_type} 出发时间 {back_time} 预计到达时间 {back_arrive_time}'
                    logger.info(info)
                    self.mySignal.emit(info)
                    break
                else:
                    flight_index += 1
            except:
                break
        if not sat_flag:
            info = f'未寻找到合适的返程航班，请更改条件重新查找'
            logger.info(info)
            self.mySignal.emit(info)
            return False
        logger.info('开始生成订单')
        self.mySignal.emit('开始生成订单')
        # # 生成订单
        '//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[2]/div[2]/span/div[1]/div/div/div[2]/div/div[2]/div[2]'
        expend_all_price = self.brow.find_element(by=By.XPATH,
                                                  value=f'//div[@index="{flight_index}"]//button[@class="btn btn-book"]')
        self.brow.execute_script("arguments[0].click();", expend_all_price)
        # 判断当前航班是否有购票限制
        i = 0
        while True:
            try:
                tag_limit = self.brow.find_element(by=By.XPATH, value=f'//span[@id="tagLimit_0_{i}"]')
                tag_content = tag_limit.get_attribute('textContent')
                logger.info(tag_content)
                self.mySignal.emit(tag_content)
                i += 1
            except:
                break
        # 判断是选购还是预订
        order_ = self.brow.find_element(by=By.XPATH,
                                        value=f'//*[@id="0_{i}"]')
        order_text = order_.get_attribute("textContent")
        if order_text == '选购':
            order_.click()
            time.sleep(1)
            order_expend = self.brow.find_element(by=By.XPATH,
                                                  value=f'//*[@id="hp_container"]//div[@index="{flight_index}"]//div[@class="seat-row seat-row-v3 has-related-price"]/div/div[2]/button')
            order_expend.click()
        order_.click()
        #order_.click()

        # 捕获机票售完弹窗信息
        try:
            sold_out_info = self.brow.find_element(by=By.XPATH, value='//div[@id="content:1656141028600"]')
            # '您预订的航班机票已售完，请重新查询预订。'
            '/html/body/div[8]/div/div[3]/div[2]/button'
            re_search_bt = self.brow.find_element(by=By.XPATH, value='//button[@i-id="重新搜索其他航班"]')
            # re_search_bt.click()
            logger.info('当前航班没有余票')
            self.mySignal.emit('当前航班没有余票')

        except:
            logger.info('当前航班有余票')
            self.mySignal.emit('当前航班有余票')

        try:
            # 预防登录没有成功，这里再次捕捉登录弹窗
            self.brow.switch_to.default_content()
            time.sleep(1)
            # 账户名称
            nloginame = self.brow.find_element(by=By.XPATH, value='//*[@id="nloginname"]')
            # 账户密码
            npwd = self.brow.find_element(by=By.XPATH, value='//*[@id="npwd"]')

            nloginame.send_keys(self.account)
            npwd.send_keys(self.password)

            # 登录按钮
            nsubmit = self.brow.find_element(by=By.XPATH, value='//*[@id="nsubmit"]')
            nsubmit.click()
            time.sleep(3)
            # 判断用户密码是否正确
            try:
                self.brow.switch_to.default_content()
                time.sleep(1)
                personErr_info = self.brow.find_element(by=By.XPATH, value='//*[@id="nerr"]').get_attribute(
                    "textContent")
                if '密码不正确' in personErr_info:
                    logger.info('用户名或密码错误，请检查之后重新登录')
                    self.mySignal.emit('用户名或密码错误，请检查之后重新登录')
                    return False
                else:
                    pass
            except:
                pass
        except:
            pass

        # 填写乘机人信息
        passenger_num = len(self.passenger_info)  # 乘客人数
        # 根据乘客人数点击 新增乘机人 按钮
        add_passenger_bt = self.brow.find_element(by=By.XPATH, value='.//span[@class="psg-passenger__add-text"]')

        # 填写乘机人信息
        succ_count = 0
        for i in range(passenger_num):

            p_name = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_name_{succ_count}"]')
            p_id = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_card_no_{succ_count}"]')
            try:
                p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_cellphone_{succ_count}"]')
            except:
                p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_contact_{succ_count}"]')
            # 姓名
            p_name.click()
            p_name.clear()
            p_name.send_keys(self.passenger_info[i][0])
            # 身份证
            time.sleep(0.2)
            p_id.click()
            p_id.clear()
            p_id.send_keys(self.passenger_info[i][1])
            # 电话号码 (可不填)
            time.sleep(0.2)
            p_cellphone.click()
            p_cellphone.clear()
            p_cellphone.send_keys(self.passenger_info[i][2])
            p_cellphone.send_keys(Keys.ENTER)

            # # 判断 当前乘车人信息是否正确
            # time.sleep(1)
            error_flag = False
            try:
                p_id_error_info = self.brow.find_element(by=By.XPATH,
                                                         value=f'//*[@id="passengerMain"]/div[{succ_count + 1}]/div[2]/div/div[3]/div[2]/div[4]/span').get_attribute(
                    'textContent')
                if '正确' in p_id_error_info:
                    logger.info(f'乘客 {self.passenger_info[i][0]} 身份证信息有误，系统将不为该乘客进行购票')
                    self.mySignal.emit(f'乘客 {self.passenger_info[i][0]} 身份证信息有误，系统将不为该乘客进行购票')
                    error_flag = True
            except:
                pass

            if not error_flag:
                try:
                    p_cell_info = self.brow.find_element(by=By.XPATH,
                                                         value=f'//*[@id="passengerMain"]/div[{succ_count + 1}]/div[2]/div/div[6]/div[2]/div/span').get_attribute(
                        'textContent')
                    if '正确' in p_cell_info:
                        logger.info(f'乘客 {self.passenger_info[i][0]} 电话信息有误，系统将不为该乘客进行购票')
                        self.mySignal.emit(f'乘客 {self.passenger_info[i][0]} 电话信息有误，系统将不为该乘客进行购票')
                        error_flag = True
                except:
                    pass
            # 出现错误，删除当前已填写的乘车人

            if error_flag:
                if i == passenger_num - 1:
                    de_bt = self.brow.find_element(by=By.XPATH,
                                                   value=f'//*[@id="passengerMain"]/div[{succ_count + 1}]/a/span')
                    self.brow.execute_script('arguments[0].click();', de_bt)
            else:
                succ_count += 1

            if i < passenger_num - 1 and not error_flag:
                add_passenger_bt.click()
                time.sleep(0.5)

        save_order = self.brow.find_element(by=By.XPATH, value='.//a[@id="J_saveOrder"]')
        time.sleep(0.5)

        save_order.click()

        flight_info = self.brow.find_element(by=By.XPATH, value='.//div[@id="J_flightInfo"]').get_attribute(
            "textContent")

        logger.info(flight_info)
        self.mySignal.emit(flight_info)

        total_price = self.brow.find_element(by=By.XPATH, value='.//span[@id="J_totalPrice"]').get_attribute(
            "textContent")
        logger.debug(total_price)
        # 判断有无滑块验证
        self.brow.switch_to.default_content()
        time.sleep(2)
        try:

            # '滑块'
            sliding_block = self.brow.find_element(by=By.XPATH,
                                                   value='//*[@id="J_slider_verification"]/div[1]/div[2]/div/i[1]')
            logger.info('捕获到滑块验证弹窗')
            self.mySignal.emit('捕获到滑块验证弹窗')
            slider_area = self.brow.find_element(by=By.XPATH,
                                                 value='//*[@id="J_slider_verification"]/div[1]/div[4]')

            # ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
            #                                                 sliding_block.size['height']).perform()
            distance = slider_area.size['width'] / 4
            for i in range(3):
                ActionChains(self.brow).click_and_hold(sliding_block).move_by_offset(distance, 0).perform()
                distance += distance
                time.sleep(0.2)
            # ActionChains(self.brow).click_and_hold(sliding_block).release().perform()

            # 判断有无第二重图标验证
            try:
                self.brow.switch_to.default_content()
                time.sleep(2)
                code_image = self.brow.find_element(by=By.XPATH,
                                                    value='//*[@id="J_slider_verification-choose"]/div[2]')
                element = self.brow.find_element(by=By.XPATH,
                                                 value='//*[@id="J_slider_verification-choose"]/div[2]/div[3]/img')

                login_bt = self.brow.find_element(by=By.XPATH,
                                                  value='//*[@id="J_slider_verification-choose"]/div[2]/div[4]/a')
                self.click_code(code_image, element, login_bt, 2003)
            except:
                logger.info('无图标验证')
                self.mySignal.emit('无图标验证')

            time.sleep(0.2)
            continue_bt = self.brow.find_element(by=By.XPATH, value='//button[@i-id="继续提交"]')
            self.brow.execute_script('arguments[0].click();', continue_bt)
        except:
            logger.info('未捕获到验证弹窗')
            self.mySignal.emit('未能捕获到验证弹窗')

        try:
            ordered = self.brow.find_element(by=By.XPATH, value='//*[@id="J_step2"]/div[1]/div')
            ordered_content = ordered.get_attribute("textContent")
            if '完成支付' in ordered_content.strip():
                ordered_flag = True
                logger.info('成功生成订单，向指定邮箱发送通知')
                self.mySignal.emit('成功生成订单，向指定邮箱发送通知')
                pass
            else:
                logger.info('订单生成失败,请重新购买')
                self.mySignal.emit('订单生成失败,请重新购买')
                return False
        except Exception:
            logger.info('订单生成失败,请重新购买')
            self.mySignal.emit('订单生成失败,请重新购买')
            return False

        if ordered_flag:
            content = f'用户您好，系统已为您抢到在 {self.depart_date} {depart_time} 由{self.from_}{depart_airport} 飞往 {self.to_}{arrive_airport}\n' \
                      f'并在 {self.back_date} {back_time} 由{self.to_}{back_depart_airport} 飞回 {self.from_}{back_arrive_airport} 的往返航班票\n' \
                      f'详细航班信息以及乘机人信息访问 https://passport.ctrip.com/user/login  进行查看，请尽快完成支付'
            se = Send_QQ_Email(self.email_add, content)
            se.send()
            logger.info('邮件发送成功')
            self.mySignal.emit('邮件发送成功')
            return True

    def run(self):
        self.brow = webdriver.Edge(service=s, options=edge_options)
        self.brow.get('https://passport.ctrip.com/user/login')  # 用户的登录界面网址

        status = self.login()

        if status:
            count = 1
            while True:
                logger.info(f'开始进行第 {count} 次轮询')
                self.mySignal.emit(f'开始进行第 {count} 次轮询')
                if self.url == '':
                    pass
                else:
                    self.brow.get('https://flights.ctrip.com/online/channel/domestic')
                status = self.generate_order()
                if status:
                    logger.info('购票流程结束，停止轮询')
                    self.mySignal.emit('购票流程结束，停止轮询')
                    break
                else:
                    time.sleep(self.second)
                    count += 1


class Train(QThread):
    mySignal = pyqtSignal(str)

    def __init__(self, account, password, from_station, to_station, depart_date, depart_time_limit,
                 train_type_option, passenger_info,
                 seat_type_option, email_add, second):
        super(Train, self).__init__()

        self.url = ''
        self.from_station = from_station  # 出发站
        self.to_station = to_station  # 目的站
        self.depart_date = depart_date  # 出发日期
        self.depart_time_limit = depart_time_limit  # 出发时间段限制 ['11','12']
        self.train_type_option = train_type_option  # 车次类型 1：高铁/城际 2：动车 3：直达 4：特快 5：快速
        self.passenger_info = passenger_info  # 乘客信息
        self.seat_type_option = seat_type_option  # 座位类型
        # 2: '商务座/特等座', 3: '一等座', 4: '二等座/二等包座', 5: '高级软卧', 6: '软卧/一等卧', 7: '动卧', 8: '硬卧/二等卧', 9: '软座',
        #                     10: '硬座', 11: '无座'
        self.email_add = email_add  # 邮件地址
        self.second = second
        self.account = account
        self.password = password

        # 账号的登录

    def login(self):
        logger.info(f'开始登陆12306账户 {self.account}')
        self.mySignal.emit(f'开始登陆12306账户 {self.account}')
        # 捕捉账号登录的相关xpath
        user_name = self.brow.find_element(by=By.XPATH, value='//*[@id="J-userName"]')
        user_password = self.brow.find_element(by=By.XPATH, value='//*[@id="J-password"]')
        login_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="J-login"]')
        user_name.send_keys(self.account)
        user_password.send_keys(self.password)
        login_bt.click()
        while True:
            try:
                sliding_block = self.brow.find_element(by=By.XPATH,
                                                       value='/html/body/div[1]/div[4]/div[2]/div[2]/div/div/div[2]/div/div[1]/span')
                break
            except Exception as e:
                pass

        logger.info('捕获到弹窗')
        self.mySignal.emit('捕获到弹窗')

        slider_area = self.brow.find_element(by=By.XPATH, value='//*[@id="nc_1__scale_text"]/span')

        ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
                                                        sliding_block.size['height']).perform()
        flag = False
        try:
            sleep(2)
            self.brow.switch_to.default_content()
            sleep(1)
            yq_bt = self.brow.find_element(by=By.XPATH, value='/html/body/div[2]/div[7]/div[2]')
            flag = True
        except Exception as e:
            while True:
                try:
                    fresh_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="nc_1_refresh1"]')
                    fresh_bt.click()
                    sleep(1)
                    sliding_block = self.brow.find_element(by=By.XPATH,
                                                           value='//*[@id="nc_1_n1z"]')
                    logger.info('捕获到滑块验证码刷新弹窗')
                    self.mySignal.emit('捕获到滑块验证码刷新弹窗')
                    slider_area = self.brow.find_element(by=By.XPATH, value='//*[@id="nc_1__scale_text"]/span')
                    ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
                                                                    sliding_block.size['height']).perform()

                    if True:
                        break
                except Exception as e:
                    try:
                        try:
                            password_erro = self.brow.find_element(by=By.XPATH, value='//*[@id="J-login-error"]/span')
                            logger.info('登录密码错误')
                            self.mySignal.emit('登录密码错误')
                            return False
                        except:
                            pass
                        self.brow.switch_to.default_content()
                        logger.info('捕获疫情弹窗之前')
                        self.mySignal.emit('捕获疫情弹窗之前')
                        sleep(2)
                        yq_bt = self.brow.find_element(by=By.XPATH,
                                                       value='//div[@role="alertdialog"]')
                        '/html/body/div[4]/div[2]'
                        '/html/body/div[4]/div[2]'
                        logger.info('捕获到疫情弹窗')
                        self.mySignal.emit('捕获到疫情弹窗')
                        flag = True
                        if flag:
                            break
                    except:
                        logger.info('未捕获到疫情弹窗')
                        self.mySignal.emit('未捕获到疫情弹窗')
                        pass

        # 登录成功之后：添加乘客信息
        sleep(1)
        logger.info('登录成功')
        self.mySignal.emit('登录成功')
        self.brow.get('https://kyfw.12306.cn/otn/view/passengers.html')
        # if not flag:
        #     yq_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="pop_165623983124549719"]/div[2]/div[3]/a')
        #     yq_bt.click()
        # passenger_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="cylianxiren"]/a')
        # passenger_bt.click()

        # 跳转之后添加乘车人的信息

        # 姓名的xpath: '//*[@id="content_list"]/div/div[2]/table/tbody/tr[1]/td[2]/div
        #     //*[@id="content_list"]/div/div[2]/table/tbody/tr[2]/td[2]/div

        # //*[@id="content_list"]/div/div[2]/table/tbody
        sleep(3)
        i = 1
        name_list = []
        while True:
            try:
                now_name = self.brow.find_element(by=By.XPATH,
                                                  value=f'//*[@id="content_list"]/div/div[2]/table/tbody/tr[{i}]/td[2]/div')
                name_list.append(now_name.text)
                i += 1
            except:
                break
        fail_list = []
        for i in range(len(self.passenger_info)):
            if self.passenger_info[i][0] not in name_list:

                add_contact = self.brow.find_element(by=By.XPATH, value='//*[@id="add_contact"]')
                add_contact.click()
                name = self.brow.find_element(by=By.XPATH, value='//*[@id="name"]')
                cardcode = self.brow.find_element(by=By.XPATH, value='//*[@id="cardCode"]')
                tele = self.brow.find_element(by=By.XPATH, value='//*[@id="mobileNo"]')
                save_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="save_btn"]')
                name.click()
                name.send_keys(self.passenger_info[i][0])
                cardcode.click()
                cardcode.send_keys(self.passenger_info[i][1])
                tele.click()
                tele.send_keys(self.passenger_info[i][2])
                save_bt.click()
                try:
                    self.brow.switch_to.default_content()
                    sleep(1)
                    erro = self.brow.find_element(by=By.XPATH, value='/html/body/div[4]/div[2]/div[2]/div/div[2]/h2')
                    logger.info(erro.text + f'{self.passenger_info[i][0]}添加失败')
                    self.mySignal.emit(erro.text + f'{self.passenger_info[i][0]}添加失败')
                    fail_list.append(i)
                    self.brow.get('https://kyfw.12306.cn/otn/view/passengers.html')
                except Exception as e:
                    sleep(1)
                    try:
                        tele_erro = self.brow.find_element(by=By.XPATH,
                                                           value='/html/body/div[2]/div[2]/div[2]/form/div/div[2]/div[2]/div[2]/div[2]/div[2]/label')
                        logger.info(f'{self.passenger_info[i][0]}添加失败' + tele_erro.text)
                        self.mySignal.emit(f'{self.passenger_info[i][0]}添加失败' + tele_erro.text)
                        fail_list.append(i)
                        self.brow.get('https://kyfw.12306.cn/otn/view/passengers.html')
                    except:
                        back = self.brow.find_element(by=By.XPATH,
                                                      value='//*[@id="J-verification-way"]/div[2]/div[3]/a[1]')
                        logger.info(f'{self.passenger_info[i][0]}添加成功')
                        self.mySignal.emit(f'{self.passenger_info[i][0]}添加成功')
                        back.click()

        sleep(2)
        for i in fail_list:
            del self.passenger_info[i]
        self.brow.get('https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc')
        self.url = 'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc'
        return True

    # 单程车票
    def generate_order_one_way(self):
        # 出发站点 目的站点 出发日期 车次类型
        seat_type_dic = {2: '商务座', 3: '一等座', 4: '二等座', 5: '高级软卧', 6: '软卧', 7: '动卧', 8: '硬卧', 9: '软座',
                         10: '硬座', 11: '无座'}

        # 出发站点
        from_lable = self.brow.find_element(by=By.XPATH, value='//*[@id="fromStationText"]')
        from_lable.click()
        from_lable.send_keys(self.from_station)
        from_lable.send_keys(Keys.ENTER)

        # 到达站点
        to_lable = self.brow.find_element(by=By.XPATH, value='//*[@id="toStationText"]')
        to_lable.click()
        # to_lable.clear()
        to_lable.send_keys(self.to_station)
        to_lable.send_keys(Keys.ENTER)

        # 日期
        date_lable = self.brow.find_element(by=By.XPATH, value='//*[@id="train_date"]')
        date_lable.click()
        date_lable.clear()
        date_lable.send_keys(self.depart_date)
        date_lable.send_keys(Keys.ENTER)

        date_li = self.brow.find_element(by=By.XPATH, value='//*[@id="date_icon_1"]')
        date_li.click()

        # 查询按钮
        search_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="query_ticket"]')
        self.brow.execute_script("arguments[0].click();", search_bt)

        # 筛选出发站点，首先与用户输入出发站进行匹配
        try:
            time.sleep(1)
            fr_station = self.brow.find_element(by=By.XPATH, value=f'//*[@id="cc_from_station_{self.from_station}"]')
            fr_station.click()
        except Exception as e:
            logger.debug(e)
            logger.info('未能找到出发站点，请检查站点名称，重新输入')
            self.mySignal.emit('未能找到出发站点，请检查站点名称，重新输入')
            return False
        logger.info('匹配到出发站点')
        self.mySignal.emit('匹配到出发站点')

        # 选择车次类型,并判断当前车次类型有无车次
        # 选择所有车次按钮，当用户指定的车次类型 车次为0 时，选用全部车次类型
        train_type_all = self.brow.find_element(by=By.XPATH, value='//*[@id="cc_train_type_btn_all"]')
        # 车次类型选择
        train_type = self.brow.find_element(by=By.XPATH,
                                            value=f'//*[@id="_ul_station_train_code"]/li[{self.train_type_option}]')
        train_type.click()
        time.sleep(0.5)
        # 判断当前车次类型是否车次数是否为 0
        train_num = int(self.brow.find_element(by=By.XPATH, value='//*[@id="trainum"]').get_attribute('textContent'))
        if train_num == 0:
            train_type_all.click()
        time.sleep(0.5)
        train_num = int(self.brow.find_element(by=By.XPATH, value='//*[@id="trainum"]').get_attribute('textContent'))

        # 时间段限制 time_limit 形如 [12,18]
        start_t = int(self.depart_time_limit[0])
        end_t = int(self.depart_time_limit[1])
        ticket_flag = False
        # 开始查找有无符号条件的班次
        logger.info('开始查找符合条件的班次')
        self.mySignal.emit('开始查找符合条件的班次')
        tr_index = 1
        for i in range(train_num):
            # 判断终点站点 是否与目标终点站一致
            des_info = self.brow.find_element(by=By.XPATH,
                                              value=f'//*[@id="train_num_{i}"]/div[2]/strong[2]').get_attribute(
                'textContent')
            if des_info.strip() == self.to_station:
                # 判断出发时间是否符合要求
                st_t = self.brow.find_element(by=By.XPATH,
                                              value=f'//*[@id="train_num_{i}"]/div[3]/strong[1]').get_attribute(
                    'textContent')
                t_ = int(st_t.split(':')[0])
                arri_t = self.brow.find_element(by=By.XPATH,
                                                value=f'//*[@id="train_num_{i}"]/div[3]/strong[2]').get_attribute(
                    'textContent')
                if start_t <= t_ < end_t:
                    # 时间满足要求 获取对应舱位余票信息
                    left_ = self.brow.find_element(by=By.XPATH,
                                                   value=f'//*[@id="queryLeftTable"]//tr[{tr_index}]/td[{self.seat_type_option}]').get_attribute(
                        'textContent')
                    # 当前的车次
                    train_title = self.brow.find_element(by=By.XPATH,
                                                         value=f'//*[@id="queryLeftTable"]//tr[{tr_index}]/td[1]/div/div[1]/div/a').get_attribute(
                        'textContent')
                    # 判断余票 可能出现 '--' '无' '有' '数字'
                    if left_ == '--' or left_ == '无' or left_ == '候补':
                        logger.info(f'车次 {train_title} {seat_type_dic[self.seat_type_option]} 无余票,继续寻找下一个班次')
                        self.mySignal.emit(f'车次 {train_title} {seat_type_dic[self.seat_type_option]} 无余票,继续寻找下一个班次')
                    elif left_ == '有':
                        logger.info(f'车次 {train_title} {seat_type_dic[self.seat_type_option]} 有 余票(有 意味着余票较多)')
                        self.mySignal.emit(f'车次 {train_title} {seat_type_dic[self.seat_type_option]} 有 余票(有 意味着余票较多)')
                        ticket_flag = True
                        break
                    else:
                        logger.info(f'车次 {train_title} {seat_type_dic[self.seat_type_option]} 余票数量为 {left_}')
                        self.mySignal.emit(f'车次 {train_title} {seat_type_dic[self.seat_type_option]} 余票数量为 {left_}')
                        # 判断余票数量与当前购票人数
                        if int(left_) >= len(self.passenger_info):
                            logger.info('余票数量大于乘车人数，可以正常购买')
                            self.mySignal.emit('余票数量大于乘车人数，可以正常购买')
                            ticket_flag = True
                            break
                        else:
                            # logger.info('余票数量小于乘车人数，系统将按照乘车信息先后顺序进行购票')
                            logger.info('余票数量小于乘车人数，继续寻找下一个班次')
                            self.mySignal.emit('余票数量小于乘车人数，继续寻找下一个班次')
            tr_index += 2
        if not ticket_flag:
            logger.info('无符合条件的班次，请更改条件，再次购票')
            self.mySignal.emit('无符合条件的班次，请更改条件，再次购票')
            return False
        else:
            logger.info(
                f'找到合适的班次 {train_title} 在 {self.depart_date} {st_t} 从{self.from_station}出发 预计{arri_t} 到达 {self.to_station}')
            self.mySignal.emit(
                f'找到合适的班次 {train_title} 在 {self.depart_date} {st_t} 从{self.from_station}出发 预计{arri_t} 到达 {self.to_station}')

        # 有足够余票，进行购票操作
        logger.info('开始生成订单')
        self.mySignal.emit('开始生成订单')
        time.sleep(0.5)
        order_bt = self.brow.find_element(by=By.XPATH, value=f'//*[@id="queryLeftTable"]//tr[{tr_index}]/td[13]/a')
        order_bt.click()

        'content_defaultwarningAlert_id'

        # 根据座位类型，定位到座位类型下标
        seat_index = 0
        while True:
            try:
                seat_type = self.brow.find_element(by=By.XPATH,
                                                   value=f'//*[@id="seatType_1"]/option[{seat_index}]').get_attribute(
                    'textContent')
                if seat_type_dic[self.seat_type_option] in seat_type:
                    break
                else:
                    seat_index += 1
            except:
                break
        # 从 self.passenger_info里面挨个读取姓名，进行选择 (这里忽略重名情况)
        # 选取乘车人
        passenger_num = len(self.passenger_info)
        succ_count = 0  # 成功添加乘客的人数
        for i in range(passenger_num):
            time.sleep(0.5)
            name_search_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="quickQueryPassenger_id"]')
            name_search_bt.click()
            time.sleep(0.4)
            name_search_bt.clear()
            name_search_bt.click()
            name_search_bt.send_keys(self.passenger_info[i][0])

            # 选择按钮
            # 判断当前选择的乘车人是否能够乘车

            time.sleep(1)
            select_info = self.brow.find_element(by=By.XPATH, value='//*[@id="normal_passenger_id"]/li').get_attribute(
                'title')
            if '修改身份信息' in select_info:
                logger.info(f'{self.passenger_info[i][0]} 乘车人信息有误，系统将不为该乘客购票,请检查该乘客信息')
                self.mySignal.emit(f'{self.passenger_info[i][0]} 乘车人信息有误，系统将不为该乘客购票,请检查该乘客信息')
                passenger_num -= 1
            else:
                select_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="normal_passenger_id"]/li/label')
                select_bt.click()
                # self.brow.execute_script('arguments[0].click();', select_bt)

                # 利用下拉选择框 进行选择座位类型
                seat_select = Select(self.brow.find_element(by=By.ID, value=f'seatType_{succ_count + 1}'))
                seat_select.select_by_index(seat_index)
                succ_count += 1

        time.sleep(2)
        sumbit_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="submitOrder_id"]')
        sumbit_bt.click()

        # 座位位置的选择，暂不设置
        # 现阶段座位默认选择相邻座位,需根据选择的票的类型来进行选择
        # 查找符合当前座位类型的 座位表
        logger.info('开始选取座位')
        self.mySignal.emit('开始选取座位')
        sel_bd_num = 1
        seat_select_count = 0  # 已经选择座位计数
        seat_id_list = []
        is_selected = False
        self.brow.switch_to.default_content()
        time.sleep(1)
        while True:
            try:

                seat_sel_bd = self.brow.find_element(by=By.XPATH,
                                                     value=f'//*[@id="id-seat-sel"]/div[2]/div[{sel_bd_num}]').get_attribute(
                    'style')
                if 'block' in seat_sel_bd:
                    # 表示匹配到了当前座位类型的座位表,开始选择相邻座位
                    # ul 标签有两个
                    for i in range(2):
                        j = 1
                        while True:
                            try:
                                seat_list_li = self.brow.find_element(by=By.XPATH,
                                                                      value=f'//*[@id="id-seat-sel"]/div[2]/div[{sel_bd_num}]/ul[{i}]/li[{j}]/a')
                                seat_info = seat_list_li.get_attribute('class')
                                if 'cur' in seat_info:
                                    pass
                                else:
                                    self.brow.execute_script('arguments[0].click();', seat_list_li)
                                    # seat_id_list.append(seat_list_li.get_attribute('id'))
                                    seat_select_count += 1
                                    if seat_select_count == succ_count:
                                        is_selected = True
                                        break
                                j += 1

                            except:
                                break
                        if is_selected:
                            break
                    if is_selected:
                        break
                sel_bd_num += 1
            except:
                break
        logger.info('座位选取完毕')
        self.mySignal.emit('座位选取完毕')

        # # 确认购票
        self.brow.switch_to.default_content()
        time.sleep(1)
        qr_submit_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="qr_submit_id"]')
        qr_submit_bt.click()

        # 判断购买是否成功
        start_time = time.time()
        while True:
            try:
                sleep(0.5)
                pay_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="payButton"]')
                self.brow.get('https://kyfw.12306.cn/otn/view/train_order.html')
                for i in range(succ_count):
                    if i == 0:
                        seat_id_info = self.brow.find_element(by=By.XPATH,
                                                              value=f'//*[@id="not_complete"]//tbody/tr[{i + 1}]/td[3]/div[2]').get_attribute(
                            'textContent')
                    else:
                        seat_id_info = self.brow.find_element(by=By.XPATH,
                                                              value=f'//*[@id="not_complete"]//tbody/tr[{i + 1}]/td[2]/div[2]').get_attribute(
                            'textContent')
                    seat_id_list.append(seat_id_info)
                '//*[@id="not_complete"]/div[2]/table/tbody/tr[1]/td[3]/div[2]'
                '//*[@id="not_complete"]/div[2]/table/tbody/tr[2]/td[2]/div[2]'
                logger.info('订单生成成功，请及时登录12306网站进行支付')
                self.mySignal.emit('订单生成成功，请及时登录12306网站进行支付')
                logger.info('开始发送邮件')
                self.mySignal.emit('开始发送邮件')

                content = f'系统已为您买到 {succ_count}张 {train_title} 在 {self.depart_date} {st_t} 从{self.from_station}出发 预计{arri_t} 到达 {self.to_station}\n' \
                          f'的座位为 {seat_type_dic[self.seat_type_option]} {" ".join(seat_id_list)} 的单程车票，请尽快支付！更多车票详细信息请访问 https://kyfw.12306.cn/otn/view/train_order.html'
                se = Send_QQ_Email(self.email_add, content)
                se.send()
                logger.info('邮件发送成功')
                self.mySignal.emit('邮件发送成功')

                return True
            except:
                end_time = time.time()
                if end_time - start_time < 1:
                    logger.info('订单已提交，等待12306系统回应')
                    self.mySignal.emit('订单已提交，等待12306系统回应')
                elif end_time - start_time > 150:
                    logger.info('订单长时间未得到响应，可能购买成功，可自行登入12306进行查看')
                    self.mySignal.emit('订单长时间未得到响应，可能购买成功，可自行登入12306进行查看')
                    return False

    def generate_order(self):

        status = self.generate_order_one_way()

        if status:
            return True
        else:
            return False

    def run(self):
        self.brow = webdriver.Edge(service=s, options=edge_options)
        self.brow.get('https://kyfw.12306.cn/otn/resources/login.html')

        status = self.login()
        if status:
            count = 1
            while True:
                logger.info(f'开始进行第 {count} 次轮询')
                self.mySignal.emit(f'开始进行第 {count} 次轮询')
                if self.url == '':
                    pass
                else:
                    self.brow.get('https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc')
                status = self.generate_order()
                if status:
                    logger.info('购票流程结束，停止轮询')
                    self.mySignal.emit('购票流程结束，停止轮询')
                    break
                else:
                    time.sleep(self.second)
                    count += 1


