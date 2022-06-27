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

from Send_Email import Send_QQ_Email
from chaojiying import Chaojiying_Client
from dpi_get import WindowsCommon

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
    def __init__(self):
        self.brow = webdriver.Edge(service=s, options=edge_options)
        self.brow.get('https://passport.ctrip.com/user/login')  # 用户的登录界面网址
        # self.login(account, password)
        self.url = ''

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

        # # 判断登录验证码类型 或没有验证码
        while flag:
            # 捕获滑块验证
            start_time = time.time()
            try:
                time.sleep(2)
                ver_scroll = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div/div[4]/div[3]')
                flag = True
                dialog_info = self.brow.find_element(by=By.XPATH,
                                                     value='//*[@id="sliderddnormal"]/div/div[4]/div[5]/span').get_attribute(
                    "textContent")
                if dialog_info.strip() == '拖动滑块填充拼图':
                    logger.info('正在破解滑块验证码')
                    time.sleep(1)
                    ver_scroll.click()
                else:
                    raise Exception
            except:
                try:
                    icon_ = self.brow.find_element(by=By.XPATH,
                                                   value='//*[@id="sliderddnormal"]/div/div[4]/div[2]/div/span/span/span[1]')
                    flag = True
                    self.click_code()
                except:
                    flag = False
            if not flag:
                end_time = time.time()
                if end_time - start_time >= 2:  # 如果超过 几秒 未捕获到弹窗 判断当前网络状态
                    ret = subprocess.run("ping www.baidu.com -n 1", shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    if ret.returncode == 0:  # 当前网络良好,则代表已成功登录，无验证码弹窗
                        break
                    else:  # 网络状态不好，应该抛出异常，这里暂时不写
                        logger.info('当前网络状态较差，请检查网络状态，重新登录。')
                        return False
                else:
                    flag = True

        # try:
        #     self.ver_slidecode()
        #     sleep(10)
        #     # self.click_code()
        # except:
        #     flag = False
        #     # 在规定时间内没有捕获到验证码弹窗 判断当前网络状态
        #     ret = subprocess.run("ping www.baidu.com -n 1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #     if ret.returncode == 0:  # 当前网络良好,则代表已成功登录，无验证码弹窗
        #         pass
        #     else:  # 网络状态不好，应该抛出异常，这里暂时不写
        #         logger.info('当前网络状态较差，请检查网络状态，重新登录。')
        #         return False

        # 在登录成功后

        # try:
        #     first_option = self.brow.find_element(by=By.XPATH,
        #                                           value='//*[@id="hp_nfes_homepage"]/span')  # 在登陆界面之后是需要点击首页的选项
        #     #first_option.click()
        #     self.brow.execute_script("arguments[0].click();", first_option)
        # except Exception as e:#selenium.common.exceptions.NoSuchElementException as e:
        #     logger.debug(e)
        #     logger.info('出现异常，若此异常提示较多，请更换网络环境或是稍后使用')
        #     return False
        # logger.info(f'账户 {account} 已成功登录')
        #
        # # 飞机票的选项
        #
        # sleep(0.5)
        # first_option_tk = self.brow.find_element(by=By.XPATH,
        #                                          value='//*[@id="leftSideNavLayer"]/div/div/div[2]/div/div[1]/div/div[2]/button')
        #
        # first_option_tk.click()
        # airplane_tk_option = self.brow.find_element(by=By.XPATH,
        #                                             value='//*[@id="leftSideNavLayer"]/div/div/div[2]/div/div[1]/div/div[2]/button')
        # airplane_tk_option.click()
        # sleep(0.4)
        logger.info(f'账户 {account} 已成功登录')
        sleep(0.5)

        self.brow.get('https://flights.ctrip.com/online/channel/domestic')
        return True

    # 滚轮验证码的点击因为不需要滚轮的点击

    # 滑块验证码的验证

    def ver_slidecode(self):  # 在验证码登录的时可以利用循环来进行点击
        start_time = time.time()
        flag = 0
        while True:
            try:
                ver_scroll = self.brow.find_element(by=By.XPATH, value='//*[@id="sliderddnormal"]/div/div[4]/div[3]')
                logger.info('正在破解滑块验证码')
                sleep(1)
                ver_scroll.click()
                flag = 1
                if flag:
                    break
            except:
                # num +=1
                end_time = time.time()
                if end_time - start_time >= 4:
                    break
        if flag != 1:
            raise Exception

        # 顺序点击的验证码

    def click_code(self):
        logger.info('正在破解图标验证码')
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

    def generate_order(self, from_, to_, depart_date, back_date, depart_option, back_option, class_option, ticket_type,
                       passenger_info):
        status = False
        if ticket_type == 0:  # 表示单程票
            status = self.generate_one_way_order(from_, to_, depart_date, depart_option, class_option, passenger_info)
        else:
            status = self.generate_round_order(from_, to_, depart_date, back_date, depart_option, back_option,
                                               class_option,
                                               passenger_info)
        if status:
            return True
        else:
            return False

    # 单程机票
    def generate_one_way_order(self, from_, to_, date, depart_option, class_option, passenger_info):
        # 需传入 起始地点 目的地 日期 选择的起飞时间段 舱位等级
        # depart_option 1：代表6点到12点 2：代表12点到18点 3：代表18点到24点
        # class_option 1:经济舱 2:商务舱/头等舱
        date = '-'.join(date)  # date 形如['2022','06','18']
        depart_option_dic = {1: '6点到12点', 2: '12点到18点', 3: '18点到24点'}
        class_option_dic = {1: '经济舱', 2: '商务舱/头等舱'}
        logger.info(
            f'开始查找 在 {date} {depart_option_dic[depart_option]} 时间段，由 {from_} 去往 {to_} {class_option_dic[class_option]}的 单程机票')

        time.sleep(0.5)
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

        # 爬取航班信息前的处理

        time.sleep(2)
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
        # for i in range(8):
        #     time.sleep(0.5)
        #     self.brow.execute_script('window.scrollBy(0,500)')
        # time.sleep(2)
        page_text = self.brow.page_source

        logger.info('正在获取航班信息...')
        # 利用xpath解析数据
        tree = etree.HTML(page_text)
        self.flight_info_dict = {}
        # 航班divs
        divs = tree.xpath('//div[@class="flight-item domestic"]')

        # 航班信息形如 ['河北航空', 'NS8456\xa0', '波音737(中)', '共享 '] ‘共享’项不一定均存在
        flight_airline = divs[0].xpath('.//div[@class="flight-airline"]//text()')

        # 航班详细信息 flight_detail

        # 出发地 ['17:05', '江北国际机场', 'T3'] 可能出现没有 航站楼Terminal信息
        depart = divs[0].xpath('.//div[@class="depart-box"]//text()')

        # 目的地信息 ['00:40', ' +1天', '大兴国际机场', 'T2']  第二个信息为 附加信息，可能为空 第四个信息为航站楼信息，可能不会出现该信息
        arrival = divs[0].xpath('.//div[@class="arrive-box"]//text()')

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

        # 判断当前航班是否有购票限制
        i = 0
        while True:
            try:
                tag_limit = self.brow.find_element(by=By.XPATH, value=f'//span[@id="tagLimit_0_{i}"]')
                tag_content = tag_limit.get_attribute('textContent')
                logger.info(tag_content)
                i += 1
            except:
                break

        order_ = self.brow.find_element(by=By.XPATH,
                                        value=f'//*[@id="0_{i}"]')
        order_.click()

        # 捕获机票售完弹窗信息
        try:
            sold_out_info = self.brow.find_element(by=By.XPATH, value='//div[@div="popup-info"]')
            # '您预订的航班机票已售完，请重新查询预订。'
            if '已售完' in sold_out_info.get_attribute('textContent').strip():
                # re_search_bt.click()
                logger.info('当前航班没有余票')

        except:
            logger.info('当前航班有余票')
        # 填写乘机人信息

        passenger_num = len(passenger_info)  # 乘客人数
        # 根据乘客人数点击 新增乘机人 按钮
        add_passenger_bt = self.brow.find_element(by=By.XPATH, value='.//span[@class="psg-passenger__add-text"]')
        # for i in range(passage_num - 1):
        #     add_passage_bt.click()
        #     time.sleep(0.5)
        # 填写乘机人信息
        for i in range(passenger_num):

            p_name = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_name_{i}"]')
            p_id = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_card_no_{i}"]')
            try:
                p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_cellphone_{i}"]')
            except:
                p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_contact_{i}"]')
            # 姓名
            p_name.send_keys(passenger_info[i][0])
            # 身份证
            p_id.send_keys(passenger_info[i][1])
            # 电话号码 (可不填)
            p_cellphone.send_keys(passenger_info[i][2])
            if i < passenger_num - 1:
                add_passenger_bt.click()
                time.sleep(0.5)

        save_order = self.brow.find_element(by=By.XPATH, value='.//a[@id="J_saveOrder"]')
        time.sleep(0.5)

        save_order.click()

        flight_info = self.brow.find_element(by=By.XPATH, value='.//div[@id="J_flightInfo"]').get_attribute(
            "textContent")

        logger.info(flight_info)
        total_price = self.brow.find_element(by=By.XPATH, value='.//span[@id="J_totalPrice"]').get_attribute(
            "textContent")
        logger.debug(total_price)

        # 判断有无滑块验证
        self.brow.switch_to.default_content()
        time.sleep(2)
        try:
            '''滑块的弹窗的xpath：'/html/body/div[29]/div'''
            # 滑块的：'//*[@id="J_slider_verification"]/div[1]/div[2]/div/i[1]'

            # dia = self.brow.find_element(by=By.XPATH, value='//div[@style="position: fixed; outline: 0px; left: 564px; top: 63px; z-index: 1025;"]')
            # sleep(4)
            # dia = self.brow.find_element(by=By.XPATH, value='/html/body/div[29]/div')

            # '滑块'
            sliding_block = self.brow.find_element(by=By.XPATH,
                                                   value='//*[@id="J_slider_verification"]/div[1]/div[2]/div/i[1]')
            logger.info('捕获到弹窗')
            slider_area = self.brow.find_element(by=By.XPATH, value='//*[@id="J_slider_verification"]/div[1]/div[4]')

            # ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
            #                                                 sliding_block.size['height']).perform()
            distance = slider_area.size['width'] / 4
            for i in range(4):
                ActionChains(self.brow).click_and_hold(sliding_block).move_by_offset(distance, 0).perform()
                distance += distance
                time.sleep(0.2)
            ActionChains(self.brow).click_and_hold(sliding_block).release().perform()

            # sliding = ActionChains(self.brow).click_and_hold(sliding_block)
            # distance = sliding_block.location['x'] + 250  # 偏移距离
            # sliding.move_by_offset(distance, 0).perform()
            # sliding.release().perform()

            # 判断有无第二重图标验证
            time.sleep(2)
            try:
                aa = self.brow.find_element(by=By.XPATH,
                                            value='//*[@id="J_slider_verification-choose"]/div[2]/div[1]/div/span')
            except:
                pass

            time.sleep(0.2)
            continue_bt = self.brow.find_element(by=By.XPATH, value='/html/body/div[27]/div/div[3]/div[2]/button')
            # /html/body/div[25]/div/div[3]/div[2]/button
            continue_bt.click()
        except:
            logger.info('未捕获到验证弹窗')
        ordered_flag = False
        try:
            ordered = self.brow.find_element(by=By.XPATH, value='//*[@id="J_step2"]/div[1]/div')
            ordered_content = ordered.get_attribute("textContent")
            if '完成支付' in ordered_content.strip():
                ordered_flag = True
                logger.info('成功生成订单，向指定邮箱发送通知')
                pass
            else:
                logger.info('订单生成失败,请重新购买')
                return False
        except Exception:
            logger.info('订单生成失败,请重新购买')
            return False

        if ordered_flag:
            self.send_email(from_, to_, date, None, depart, arrival, None, None)
            return True

        # self.brow.quit()

    # 往返机票
    def generate_round_order(self, from_, to_, depart_date, back_date, depart_option, back_option, class_option,
                             passenger_info):
        # 需传入 起始地点 目的地 日期 选择的起飞时间段 舱位等级
        # depart_option 1：代表6点到12点 2：代表12点到18点 3：代表18点到24点
        # class_option 1:经济舱 2:商务舱/头等舱
        depart_date = '-'.join(depart_date)  # date 形如['2022','06','18']
        back_date = '-'.join(back_date)

        depart_option_dic = {1: '6点到12点', 2: '12点到18点', 3: '18点到24点'}

        logger.info(
            f'开始查找 在 {depart_date} {depart_option_dic[depart_option]} 时间段，由 {from_} 去往 {to_} '
            f'在 {back_date} {depart_option_dic[back_option]} 时间段 由 {to_} 去往 {from_}的 往返机票')

        time.sleep(1)
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
        url = re.sub(pattern, depart_date + '_' + back_date, url)
        self.url = url
        self.brow.get(url)
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
                                               value='//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[1]/div/ul[1]/li[1]/div/span')

        zhifei_button.click()
        # 起飞时间段/抵达时间段
        depart_arrival = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_time"]/div')
        depart_arrival.click()
        time.sleep(0.8)

        # 选择起飞时间段
        depart_ul = self.brow.find_element(by=By.XPATH,
                                           value=f'.//ul[@id="filter_group_time__depart"]/li[{depart_option}]/span/i')
        depart_ul.click()

        depart_arrival.click()

        # 选择舱位 经济舱 or 商务舱/头等舱
        # class_option = 1  # 1：经济舱 2：商务舱/头等舱 默认为1

        class_grade = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_class_grade"]/div')
        class_grade.click()
        class_ul = self.brow.find_element(by=By.XPATH,
                                          value=f'.//ul[@id="filter_group_class_grade__default"]/li[{class_option}]')
        class_ul.click()
        class_grade.click()

        page_text = self.brow.page_source

        logger.info('正在获取航班信息...')
        # 利用xpath解析数据
        tree = etree.HTML(page_text)

        # 航班divs
        divs = tree.xpath('//div[@class="flight-item domestic"]')

        # 航班信息形如 ['河北航空', 'NS8456\xa0', '波音737(中)', '共享 '] ‘共享’项不一定均存在
        flight_airline = divs[0].xpath('.//div[@class="flight-airline"]//text()')

        # 航班详细信息 flight_detail

        # 出发地 ['17:05', '江北国际机场', 'T3'] 可能出现没有 航站楼Terminal信息
        depart = divs[0].xpath('.//div[@class="depart-box"]//text()')

        # 目的地信息 ['00:40', ' +1天', '大兴国际机场', 'T2']  第二个信息为 附加信息，可能为空 第四个信息为航站楼信息，可能不会出现该信息
        arrival = divs[0].xpath('.//div[@class="arrive-box"]//text()')

        # 获取航空公司及飞机编号
        info = ' '.join(flight_airline) + ' '.join(depart) + ' '.join(arrival)
        logger.info(info)

        select_from = self.brow.find_element(by=By.XPATH,
                                             value='//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[2]/div[2]/span/div[1]/div/div/div/div/div[2]/div[2]/div')
        select_from.click()

        # 获取返程航班信息

        logger.info('正在获取返程航班信息')
        time.sleep(2)
        # 直飞选项

        zhifei_button = self.brow.find_element(by=By.XPATH,
                                               value='//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[1]/div/ul[1]/li[1]/div/span/i')
        # time.sleep(0.5)
        # zhifei_button.click()
        self.brow.execute_script("arguments[0].click();", zhifei_button)
        # 起飞时间段/抵达时间段
        depart_arrival = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_time"]/div')
        depart_arrival.click()
        time.sleep(0.8)

        # 选择起飞时间段
        depart_ul = self.brow.find_element(by=By.XPATH,
                                           value=f'.//ul[@id="filter_group_time__depart"]/li[{back_option}]/span/i')
        depart_ul.click()

        depart_arrival.click()

        # 选择舱位 经济舱 or 商务舱/头等舱
        # class_option = 1  # 1：经济舱 2：商务舱/头等舱 默认为1

        class_grade = self.brow.find_element(by=By.XPATH, value='//*[@id="filter_item_class_grade"]/div')
        class_grade.click()
        class_ul = self.brow.find_element(by=By.XPATH,
                                          value=f'.//ul[@id="filter_group_class_grade__default"]/li[{class_option}]')
        class_ul.click()
        class_grade.click()

        page_text = self.brow.page_source
        tree = etree.HTML(page_text)

        # 航班divs
        divs = tree.xpath('//div[@class="flight-item domestic"]')

        # 航班信息形如 ['河北航空', 'NS8456\xa0', '波音737(中)', '共享 '] ‘共享’项不一定均存在
        back_flight_airline = divs[0].xpath('.//div[@class="flight-airline"]//text()')

        # 航班详细信息 flight_detail

        # 出发地 ['17:05', '江北国际机场', 'T3'] 可能出现没有 航站楼Terminal信息
        back_depart = divs[0].xpath('.//div[@class="depart-box"]//text()')

        # 目的地信息 ['00:40', ' +1天', '大兴国际机场', 'T2']  第二个信息为 附加信息，可能为空 第四个信息为航站楼信息，可能不会出现该信息
        back_arrival = divs[0].xpath('.//div[@class="arrive-box"]//text()')

        # 获取航空公司及飞机编号
        info = ' '.join(back_flight_airline) + ' '.join(back_depart) + ' '.join(back_arrival)
        logger.info(info)

        # self.brow.execute_script('window.scrollTo(0,0)')
        logger.info('开始生成订单')
        # # 生成订单
        '//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[2]/div[2]/span/div[1]/div/div/div[2]/div/div[2]/div[2]'
        expend_all_price = self.brow.find_element(by=By.XPATH,
                                                  value='//*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[2]/div[2]/span/div[1]/div/div/div/div/div[2]/div[2]/button')
        # expend_all_price.click()                      //*[@id="hp_container"]/div[2]/div/div[2]/div/div[3]/div[2]/div[2]/span/div[1]/div/div/div/div/div[2]/div[2]/button
        self.brow.execute_script("arguments[0].click();", expend_all_price)
        # 判断当前航班是否有购票限制
        i = 0
        while True:
            try:
                tag_limit = self.brow.find_element(by=By.XPATH, value=f'//span[@id="tagLimit_0_{i}"]')
                tag_content = tag_limit.get_attribute('textContent')
                logger.info(tag_content)
                i += 1
            except:
                break

        order_ = self.brow.find_element(by=By.XPATH,
                                        value=f'//*[@id="0_{i}"]')
        order_.click()

        # 捕获机票售完弹窗信息
        try:
            sold_out_info = self.brow.find_element(by=By.XPATH, value='//div[@id="content:1656141028600"]')
            # '您预订的航班机票已售完，请重新查询预订。'
            '/html/body/div[8]/div/div[3]/div[2]/button'
            re_search_bt = self.brow.find_element(by=By.XPATH, value='//button[@i-id="重新搜索其他航班"]')
            # re_search_bt.click()
            logger.info('当前航班没有余票')

        except:
            logger.info('当前航班有余票')

        # 填写乘机人信息

        passenger_num = len(passenger_info)  # 乘客人数
        # 根据乘客人数点击 新增乘机人 按钮
        add_passenger_bt = self.brow.find_element(by=By.XPATH, value='.//span[@class="psg-passenger__add-text"]')

        try:
            # 填写乘机人信息
            for i in range(passenger_num):

                p_name = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_name_{i}"]')
                p_id = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_card_no_{i}"]')
                try:
                    p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_cellphone_{i}"]')
                except:
                    p_cellphone = self.brow.find_element(by=By.XPATH, value=f'.//input[@id="p_contact_{i}"]')

                # 姓名
                p_name.send_keys(passenger_info[i][0])
                # 身份证
                p_id.send_keys(passenger_info[i][1])
                # 电话号码 (可不填)
                p_cellphone.send_keys(passenger_info[i][2])
                if i < passenger_num - 1:
                    add_passenger_bt.click()
                    time.sleep(0.5)

            save_order = self.brow.find_element(by=By.XPATH, value='.//a[@id="J_saveOrder"]')
            time.sleep(0.5)

            save_order.click()

            flight_info = self.brow.find_element(by=By.XPATH, value='.//div[@id="J_flightInfo"]').get_attribute(
                "textContent")

            logger.info(flight_info)
            total_price = self.brow.find_element(by=By.XPATH, value='.//span[@id="J_totalPrice"]').get_attribute(
                "textContent")
            logger.debug(total_price)
            ordered_flag = False
        except Exception as e:
            logger.debug(e)
            logger.info('出现异常等待轮询')
            return False

        # 判断有无滑块验证

        self.brow.switch_to.default_content()
        time.sleep(2)
        try:
            '''滑块的弹窗的xpath：'/html/body/div[29]/div'''
            # 滑块的：'//*[@id="J_slider_verification"]/div[1]/div[2]/div/i[1]'

            # dia = self.brow.find_element(by=By.XPATH, value='//div[@style="position: fixed; outline: 0px; left: 564px; top: 63px; z-index: 1025;"]')
            # sleep(4)
            # dia = self.brow.find_element(by=By.XPATH, value='/html/body/div[29]/div')

            # '滑块'
            sliding_block = self.brow.find_element(by=By.XPATH,
                                                   value='//*[@id="J_slider_verification"]/div[1]/div[2]/div/i[1]')
            logger.info('捕获到弹窗')
            slider_area = self.brow.find_element(by=By.XPATH, value='//*[@id="J_slider_verification"]/div[1]/div[4]')

            # ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
            #                                                 sliding_block.size['height']).perform()
            distance = slider_area.size['width'] / 4
            for i in range(4):
                ActionChains(self.brow).click_and_hold(sliding_block).move_by_offset(distance, 0).perform()
                distance += distance
                time.sleep(0.2)
            ActionChains(self.brow).click_and_hold(sliding_block).release().perform()

            # sliding = ActionChains(self.brow).click_and_hold(sliding_block)
            # distance = sliding_block.location['x'] + 250  # 偏移距离
            # sliding.move_by_offset(distance, 0).perform()
            # sliding.release().perform()

            # 判断有无第二重图标验证
            time.sleep(2)
            try:
                aa = self.brow.find_element(by=By.XPATH,
                                            value='//*[@id="J_slider_verification-choose"]/div[2]/div[1]/div/span')
            except:
                pass

            time.sleep(0.2)
            continue_bt = self.brow.find_element(by=By.XPATH, value='/html/body/div[27]/div/div[3]/div[2]/button')
            # /html/body/div[25]/div/div[3]/div[2]/button
            continue_bt.click()
        except:
            logger.info('未捕获到验证弹窗')

        try:
            ordered = self.brow.find_element(by=By.XPATH, value='//*[@id="J_step2"]/div[1]/div')
            ordered_content = ordered.get_attribute("textContent")
            if '完成支付' in ordered_content.strip():
                ordered_flag = True
                logger.info('成功生成订单，向指定邮箱发送通知')
                pass
            else:
                logger.info('订单生成失败,请重新购买')
                return False
        except Exception:
            logger.info('订单生成失败,请重新购买')
            return False

        if ordered_flag:
            self.send_email(from_, to_, depart_date, back_date, depart, arrival, back_depart, back_arrival)
            return True

    def send_email(self, from_, to_, depart_date, back_date, depart, arrival, back_depart, back_arrival):
        if back_date is not None:
            content = f'用户您好，系统已为您抢到在 {depart_date} {depart[0]} 出发，由 {from_}{depart[1]} 去往 {to_}{arrival[2]} \n' \
                      f'在 {back_date} {back_depart[0]} 出发，由 {to_}{back_depart[1]} 去往 {from_}{back_arrival[2]} 的往返航班票\n 详细航班信息以及乘机人信息请访问 https://passport.ctrip.com/user/login  进行查看，请在十五分钟内支付'
        else:
            content = f'用户您好，系统已为您抢到在 {depart_date} {depart[0]} 出发，由 {from_}{depart[1]} 去往 {to_}{arrival[2]} 的单程航班票\n 详细航班信息以及乘机人信息请访问 https://passport.ctrip.com/user/login  进行查看，请在十五分钟内支付'
        se = Send_QQ_Email('1784800289@qq.com', content)
        se.send()
        logger.info('邮件发送成功')

    def loop_func(self, second, from_, to_, depart_date, back_date, depart_option, back_option, class_option,
                  ticket_type,
                  passenger_info):
        count = 1
        while True:
            logger.info(f'开始进行第 {count} 次轮询')
            if self.url == '':
                pass
            else:
                self.brow.get('https://flights.ctrip.com/online/channel/domestic')
            status = self.generate_order(from_, to_, depart_date, back_date, depart_option, back_option, class_option,
                                         ticket_type, passenger_info)
            if status:
                logger.info('购票流程结束，停止轮询')
                break
            else:
                time.sleep(second)
                count += 1


class Train:
    def __init__(self):
        self.brow = webdriver.Edge(service=s, options=edge_options)
        self.brow.get('https://kyfw.12306.cn/otn/resources/login.html')

        # 账号的登录

    def login(self, account, password, passenger_info):
        logger.info(f'开始登陆账户 {account}')
        # 捕捉账号登录的相关xpath
        user_name = self.brow.find_element(by=By.XPATH, value='//*[@id="J-userName"]')
        user_password = self.brow.find_element(by=By.XPATH, value='//*[@id="J-password"]')
        login_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="J-login"]')
        user_name.send_keys(account)
        user_password.send_keys(password)
        login_bt.click()
        sleep(1.5)
        sliding_block = self.brow.find_element(by=By.XPATH,
                                               value='//*[@id="nc_1_n1z"]')

        logger.info('捕获到弹窗')
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
                    logger.info('捕获到弹窗')
                    slider_area = self.brow.find_element(by=By.XPATH, value='//*[@id="nc_1__scale_text"]/span')
                    ActionChains(self.brow).drag_and_drop_by_offset(sliding_block, slider_area.size['width'],
                                                                    sliding_block.size['height']).perform()

                    print(4)
                    if True:
                        break
                except Exception as e:
                    try:
                        self.brow.switch_to.default_content()
                        sleep(2)
                        yq_bt = self.brow.find_element(by=By.XPATH,
                                                       value='/html/body/div[2]/div[7]/div[2]')
                        flag = True
                        if flag:
                            break
                    except:
                        pass
                    pass

        # 登录成功之后：添加乘客信息
        sleep(1)
        logger.info('登录成功')
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
        for i in passenger_info:
            if i[0] not in name_list:

                add_contact = self.brow.find_element(by=By.XPATH, value='//*[@id="add_contact"]')
                add_contact.click()
                name = self.brow.find_element(by=By.XPATH, value='//*[@id="name"]')
                cardcode = self.brow.find_element(by=By.XPATH, value='//*[@id="cardCode"]')
                tele = self.brow.find_element(by=By.XPATH, value='//*[@id="mobileNo"]')
                save_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="save_btn"]')
                name.send_keys(i[0])
                cardcode.send_keys(i[1])
                tele.send_keys(i[2])
                save_bt.click()
                try:
                    erro = self.brow.find_element(by=By.XPATH, value='//*[@id="pop_165624530613827184"]/div[2]/div[2]')
                    logger.info(erro.text + f'{i[0]}添加失败')
                    self.brow.get('https://kyfw.12306.cn/otn/view/passengers.html')
                except Exception as e:
                    back = self.brow.find_element(by=By.XPATH, value='//*[@id="J-verification-way"]/div[2]/div[3]/a[1]')
                    logger.info(f'{i[0]}添加成功')
                    back.click()

        sleep(2)
        self.brow.get('https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc')
        return True

    def generate_order(self, from_station, to_station, depart_date, train_type_option, passenger_info,
                       seat_type_option):
        # 出发站点 目的站点 出发日期 车次类型
        seat_type_dic = {2: '商务座/特等座', 3: '一等座', 4: '二等座/二等包座', 5: '高级软卧', 6: '软卧/一等卧', 7: '动卧', 8: '硬卧/二等卧', 9: '软座',
                         10: '硬座', 11: '无座'}
        depart_date = '-'.join(depart_date)

        # 出发站点
        from_lable = self.brow.find_element(by=By.XPATH, value='//*[@id="fromStationText"]')
        from_lable.click()
        from_lable.send_keys(from_station)
        from_lable.send_keys(Keys.ENTER)

        # 到达站点
        to_lable = self.brow.find_element(by=By.XPATH, value='//*[@id="toStationText"]')
        to_lable.click()
        # to_lable.clear()
        to_lable.send_keys(to_station)
        to_lable.send_keys(Keys.ENTER)

        # 日期
        date_lable = self.brow.find_element(by=By.XPATH, value='//*[@id="train_date"]')
        date_lable.click()
        date_lable.clear()
        date_lable.send_keys(depart_date)
        date_lable.send_keys(Keys.ENTER)

        date_li = self.brow.find_element(by=By.XPATH, value='//*[@id="date_icon_1"]')
        date_li.click()

        # 查询按钮
        search_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="query_ticket"]')
        self.brow.execute_script("arguments[0].click();", search_bt)

        # 筛选出发站点，首先与用户输入出发站进行匹配
        try:
            time.sleep(1)
            from_station = self.brow.find_element(by=By.XPATH, value=f'//*[@id="cc_from_station_{from_station}"]')
            from_station.click()
        except Exception as e:
            logger.debug(e)
            logger.info('未能找到出发站点，请检查站点名称，重新输入')
            return False
        logger.info('匹配到出发站点')
        # 选择车次类型,并判断当前车次类型有无车次
        # 选择所有车次按钮，当用户指定的车次类型 车次为0 时，选用全部车次类型
        train_type_all = self.brow.find_element(by=By.XPATH, value='//*[@id="cc_train_type_btn_all"]')
        # 车次类型选择
        train_type = self.brow.find_element(by=By.XPATH,
                                            value=f'//*[@id="_ul_station_train_code"]/li[{train_type_option}]')
        train_type.click()
        time.sleep(0.5)
        # 判断当前车次类型是否车次数是否为 0
        train_num = int(self.brow.find_element(by=By.XPATH, value='//*[@id="trainum"]').get_attribute('textContent'))
        if train_num == 0:
            train_type_all.click()
        time.sleep(0.5)
        train_num = int(self.brow.find_element(by=By.XPATH, value='//*[@id="trainum"]').get_attribute('textContent'))

        # 时间段限制
        start_t = 12
        end_t = 18
        ticket_flag = False
        # 开始查找有无符号条件的班次
        logger.info('开始查找符合条件的班次')
        tr_index = 1
        for i in range(train_num):
            # 判断终点站点 是否与目标终点站一致
            des_info = self.brow.find_element(by=By.XPATH,
                                              value=f'//*[@id="train_num_{i}"]/div[2]/strong[2]').get_attribute(
                'textContent')
            if des_info.strip() == to_station:
                # 判断出发时间是否符合要求
                st_t = int(self.brow.find_element(by=By.XPATH,
                                                  value=f'//*[@id="train_num_{i}"]/div[3]/strong[1]').get_attribute(
                    'textContent').split(':')[0])
                if start_t <= st_t < end_t:
                    # 时间满足要求 获取对应舱位余票信息
                    left_ = self.brow.find_element(by=By.XPATH,
                                                   value=f'//*[@id="queryLeftTable"]//tr[{tr_index}]/td[{seat_type_option}]').get_attribute(
                        'textContent')
                    # 当前的车次
                    train_title = self.brow.find_element(by=By.XPATH,
                                                         value=f'//*[@id="queryLeftTable"]//tr[{tr_index}]/td[1]/div/div[1]/div/a').get_attribute(
                        'textContent')
                    # 判断余票 可能出现 '--' '无' '有' '数字'
                    if left_ == '--' or left_ == '无':
                        logger.info(f'车次 {train_title} {seat_type_dic[seat_type_option]} 无余票,继续寻找下一个班次')
                    elif left_ == '有':
                        logger.info(f'车次 {train_title} {seat_type_dic[seat_type_option]} 有 余票(有 意味着余票较多)')
                        ticket_flag = True
                        break
                    else:
                        logger.info(f'车次 {train_title} {seat_type_dic[seat_type_option]} 余票数量为 {left_}')
                        # 判断余票数量与当前购票人数
                        if int(left_) >= len(passenger_info):
                            logger.info('余票数量大于乘车人数，可以正常购买')
                            ticket_flag = True
                            break
                        else:
                            # logger.info('余票数量小于乘车人数，系统将按照乘车信息先后顺序进行购票')
                            logger.info('余票数量小于乘车人数，继续寻找下一个班次')
            tr_index += 2
        if not ticket_flag:
            logger.info('无符合条件的班次，请更改条件，再次购票')
            return False

        # 有足够余票，进行购票操作
        logger.info('开始生成订单')
        time.sleep(0.5)
        order_bt = self.brow.find_element(by=By.XPATH, value=f'//*[@id="queryLeftTable"]//tr[{tr_index}]/td[13]/a')
        order_bt.click()

        # 选取乘车人
        # 从 passenger_info里面挨个读取姓名，进行选择 (这里忽略重名情况)
        passenger_num = len(passenger_info)
        for i in range(passenger_num):
            time.sleep(0.5)
            name_search_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="quickQueryPassenger_id"]')
            name_search_bt.click()
            time.sleep(0.4)
            name_search_bt.clear()
            name_search_bt.click()
            name_search_bt.send_keys(passenger_info[i][0])

            # 选择按钮
            # 判断当前选择的乘车人是否能够乘车

            time.sleep(1)
            select_info = self.brow.find_element(by=By.XPATH, value='//*[@id="normal_passenger_id"]/li').get_attribute(
                'title')
            if '修改身份信息' in select_info:
                logger.info(f'{passenger_info[i][0]} 乘车人信息有误，系统将不为该乘客购票')
            else:
                select_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="normal_passenger_id"]/li/label')
                select_bt.click()
                # self.brow.execute_script('arguments[0].click();', select_bt)

            # 利用下拉选择框 进行选择座位类型
            # se = Select(self.brow.find_element(by=By.ID, value=f'seatType_{i + 1}'))

        time.sleep(2)
        sumbit_bt = self.brow.find_element(by=By.XPATH, value='//*[@id="submitOrder_id"]')
        sumbit_bt.click()

        # 座位位置的选择，暂不设置

        # 确认购票
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
                logger.info('订单生成成功，请及时登录12306网站进行支付')
                break
            except:
                end_time = time.time()
                if end_time - start_time < 1:
                    logger.info('订单已提交，等待12306系统回应')
                elif end_time - start_time > 120:
                    logger.info('订单长时间未得到响应，可能购买成功，可以登入12306进行查看')
                    break



if __name__ == '__main__':
    depart_date = ['2022', '06', '29']
    back_date = ['2022', '07', '01']
    passenger_info = [['姓名', '身份证号码', '电话号码'],
                      ['姓名', '身份证号码', '电话号码']]
    account = '携程账号'
    password = '携程密码'
 

    from_ = '西安'
    to_ = '青岛'
    class_option = 1
    depart_option = 1
    back_option = 1
    second = 60
    ticket_type = 1
    ret = subprocess.run("ping www.baidu.com -n 1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ret.returncode != 0:
        logger.info('网络错误，请检查网络重试')
    else:
        lg = Subprice()
        login_status = lg.login(account, password)
        if login_status:
            # lg.generate_order(from_, to_, date, depart_option, class_option, passenger_info)
            lg.loop_func(second, from_, to_, depart_date, back_date, depart_option, back_option, class_option,
                         ticket_type, passenger_info)

    # current_datetime = datetime.datetime.now().strftime('%Y-%m-%d')
    # ret = os.system("ping baidu.com -n 1")
    # print(ret)
    
    #12306测试部分
    from_station = '长寿湖'
    to_station = '重庆北'
    seat_type_option = 4
    train = Train()
    status = train.login(account, password,passenger_info)
    if status:
        train.generate_order(from_station, to_station, depart_date, class_option, passenger_info, seat_type_option)
