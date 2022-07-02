import os
import sys
import time

from PyQt5.QtCore import QDate, Qt, QThread, pyqtSignal
from Ticket_Book import Subprice, Train
from 主界面 import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit
import requests
import datetime
import requests
import json


def getWeather(name):
    url = 'http://wthrcdn.etouch.cn/weather_mini'
    response = requests.get(url, {'city': name})
    result = json.loads(response.content.decode())
    line1 = []
    line1.append('city:' + str(result.get('data').get('city')))
    data = result.get('data').get('forecast')
    for i in data:
        line = str(i.get('date')) + f'\t' + str(i.get('high')) + '\t' + str(i.get('low')) + '\t' + str(
            i.get('type') + '\n')
        line1.append(line)
    return line1


class Asctime(QThread):
    mysignal = pyqtSignal(str)

    def __init__(self):
        super(Asctime, self).__init__()

    def run(self):
        while True:
            time.sleep(1)
            self.mysignal.emit(time.asctime())


class BookTicket(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(BookTicket, self).__init__()
        self.vara_all()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # self.passengerinfo = [['许茂森', '500222199908184320', '15310829546'], ['李欢', '500222199933384320', '15310833546'],
        #                       ['李茂', '500222199933384320', '15310833546']]

        self.passengerinfo = []
        self.read_pass()
        self.trigger_sth()
        self.update_time()
        self.show()


    def read_pass(self):
        with open('./pass_info.txt', encoding='utf-8') as file:
            pass_info = file.readlines()

        for one_pass_info in pass_info:
            one = one_pass_info.strip().split(' ')


            self.passengerinfo.append(one)
        print(self.passengerinfo)
        with open('./account_email.txt', encoding='utf-8') as file:
            self.account_email = file.readline().strip()
        if self.account_email != '':
            self.ui.loginaccount.setText(self.account_email.split(' ')[0])
            self.ui.emial.setText(self.account_email.split(' ')[1])



    def write_pass(self):
        with open('./pass_info.txt', 'w+', encoding='utf-8') as file:
            if len(self.passengerinfo) > 0:
                for info in self.passengerinfo:
                    passinfo = str(info[0]) + ' ' + str(info[1]) + ' ' + str(info[2]) + '\n'
                    file.write(passinfo)
        with open('./account_email.txt', 'w+',encoding='utf-8') as file:
            file.write(self.account_email)


    def vara_all(self):
        self.account = None
        self.password = None
        self.email_ = None
        self.from_ = None
        self.to_ = None
        self.bd = None
        self.ed = None
        self.bbt = None
        self.bet = None
        self.ebt = None
        self.eet = None
        self.sitetype = None
        self.cartype = None
        self.airsitetype = None
        self.infomation = None

    def update_time(self):
        self.asc_time = Asctime()
        self.asc_time.mysignal.connect(self.time_accept_signal)
        self.asc_time.start()

    def time_accept_signal(self, str):
        self.ui.retime.clear()
        self.ui.retime.setText(str)


    def main_show_sth(self):  # 主界面的显示
        date = datetime.datetime.now()

        self.datelist = [date.year, date.month, date.day]
        datestr = str(str(self.datelist[0]) + ' 年 ' + str(self.datelist[1]) + ' 月 ' + str(self.datelist[2]) + '日')
        self.bd = str(date).split(' ')[0]  # 出发日期的获取这是没有点击日历的情况下获得的
        self.ed = self.bd
        self.ui.time.setText(datestr)
        res = requests.get('http://myip.ipip.net', timeout=5).text
        res = res.split(' ')[4]
        self.city = res
        self.ui.weatheradd.clear()
        lineall = getWeather(self.city)
        for i in lineall:
            self.ui.weatheradd.append(i)
        self.ui.city.clear()
        self.ui.city.setText(res)

    def trigger_sth(self):
        self.main_show_sth()
        self.ui.begindate.setCalendarPopup(True)  # 显示出下拉日历
        self.ui.enddate.setCalendarPopup(True)  # 显示出下拉日历
        self.ui.beginplace.setText(self.city)  # 出发城市的设定
        self.ui.begindate.setDate(QDate.currentDate())
        self.ui.begindate.dateChanged.connect(self.OnDateChanged_begin)
        self.ui.enddate.dateChanged.connect(self.OnDateChanged_end)
        self.ui.max.clicked.connect(self.restore_or_maximize_window)
        self.ui.mini.clicked.connect(self.minimize_window)
        self.ui.close.clicked.connect(self.close_and_write)
        self.ui.loginpassword.setEchoMode(QLineEdit.Password)
        self.button_click()

    def close_and_write(self):
        self.write_pass()
        self.close()
    def OnDateChanged_begin(self, date):
        """获取选中的时间"""
        self.bd = date.toString(Qt.ISODate)
        bda = self.bd.split('-')
        for i in range(len(bda)):
            bda[i] = int(bda[i])
        self.ui.enddate.setMinimumDate(QtCore.QDate(bda[0], bda[1], bda[2]))
        print('bd', self.bd)

    def OnDateChanged_end(self, date):
        """获取选中的时间"""
        self.ed = date.toString(Qt.ISODate)
        print('ed', self.ed)

    def button_click(self):
        self.ui.airsingle.clicked.connect(self.trigger_airsignle)  # 飞机票单程
        self.ui.airdouble.clicked.connect(self.trigger_airdouble)  # 飞机票往返
        self.ui.trainsingle.clicked.connect(self.trigger_trainsignle)  # 火车票单程
        self.ui.begininfo.clicked.connect(self.trigger_begininfo)
        self.ui.cancleall.setEnabled(False)  # 在没有点击确定之前不能点击取消
        self.ui.pinfo.clicked.connect(self.trigger_pinfo)
        self.ui.addpassenger.clicked.connect(self.triger_addpassenger)
        self.ui.addfinish.clicked.connect(self.trigger_addfinish)  # 添加乘客完毕
        self.ui.continueadd.clicked.connect(self.trigger_addcontinue)
        self.ui.editpassenger.clicked.connect(self.trigger_editpassenegr)
        self.ui.editsave.clicked.connect(self.trigger_saveedit)
        self.ui.pushButton_4.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.deletepassenger.clicked.connect(self.trigger_delepassenger)
        self.ui.pushButton_3.clicked.connect(self.trigger_viewpassinfo)
        self.ui.loginsure.clicked.connect(self.trigger_loginsure)
        self.ui.cancleall.clicked.connect(self.cancel)
        self.ui.pushButton_6.clicked.connect(self.viewpassword)
        self.ui.back.clicked.connect(self.trigger_back)
        self.ui.loggerbutton.clicked.connect(self.logger_show)

    def trigger_back(self):
        if self.pass_back_flag == 1:
            self.ui.stackedWidget.setCurrentIndex(0)
        else:
            self.ui.stackedWidget.setCurrentIndex(4)

    def viewpassword(self):
        if self.ui.pushButton_6.text() == '查看':
            self.ui.loginpassword.setEchoMode(QLineEdit.Normal)
            self.ui.pushButton_6.setText('隐藏')
        else:
            self.ui.loginpassword.setEchoMode(QLineEdit.Password)
            self.ui.pushButton_6.setText('查看')

    def from_pass_info(self, name):
        for i in self.passengerinfo:
            if i[0] == name:
                return i
        return None

    def logger_show(self):
        path = os.getcwd()
        os.startfile(path + '/app.log')

    def trigger_loginsure(self):
        self.account = self.ui.loginaccount.text()
        self.password = self.ui.loginpassword.text()
        self.email_ = self.ui.emial.text()
        if self.account != '' and self.email_ != ' ':
            self.account_email = self.account + ' ' + self.email_
        if self.account == '' or self.email_ == '' or self.password == '':
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '有内容未填写')
            msg_box.setWindowFlag(Qt.Drawer)
            msg_box.exec_()
        else:
            self.ui.stackedWidget.setCurrentIndex(2)
            print(self.account)
            print(self.password)
            print(self.email_)
            print(self.infomation)
            print(self.bd)
            print(self.bbt)
            print(self.bet)
            print(self.cartype)
            print(self.sitetype)
            print(self.airsitetype)

            depart_time_limit = [self.bbt, self.bet]
            back_time_limit = [self.ebt, self.eet]
            self.ui.loggertext.clear()
            # 判断飞机还是火车
            if self.flag == 2:
                # 飞机票
                self.Airplane = Subprice(self.account, self.password, 60, self.from_, self.to_, self.bd, self.ed,
                                         depart_time_limit, back_time_limit, self.airsitetype, self.ds_flag,
                                         self.infomation, self.email_)
                self.Airplane.mySignal.connect(self.accept_signal)
                self.Airplane.start()
            else:
                self.train = Train(self.account, self.password, self.from_, self.to_, self.bd, depart_time_limit,
                                   self.cartype, self.infomation, self.sitetype, self.email_, 60)
                self.train.mySignal.connect(self.accept_signal)
                self.train.start()
            self.infomation = []

    def accept_signal(self, str):
        self.ui.loggertext.append(str)

    def cancel(self):
        if self.flag == 2:
            try:
                self.Airplane.brow.quit()
                self.Airplane.terminate()
                self.ui.loggertext.append('已取消购买')
            except:
                pass
        else:
            try:
                self.train.brow.quit()
                self.train.terminate()
                self.ui.loggertext.append('已取消购买')
            except:
                pass

    # 选择乘车人
    def choose_pass(self):
        self.ui.choosepass.clear()
        self.ui.choosepass.addItem('')
        self.passinformation = dict()
        for mm in self.passengerinfo:
            self.ui.choosepass.addItem(mm[0])
        self.ui.choosepass.currentIndexChanged.connect(self.add_pass_all_info)
        self.ui.choosefinish.clicked.connect(self.trigger_choosefinish)

    def trigger_choosefinish(self):
        namelist = self.ui.alreadypassname.text()
        namelist = namelist.split(' ')
        self.infomation = []
        for name in namelist:
            if name in self.passinformation:
                print('passinfor', self.passinformation[name])
                self.infomation.append(self.passengerinfo[self.passinformation[name]])
        print('information', self.infomation)
        self.ui.stackedWidget.setCurrentIndex(1)

    def add_pass_all_info(self):
        name = self.ui.choosepass.currentText()
        i = self.ui.choosepass.currentIndex()
        self.ui.alreadypassname.clear()
        if name not in self.passinformation:
            self.passinformation[name] = i - 1
        str = ''
        for mmm in self.passinformation:
            str += mmm + ' '
        self.ui.alreadypassname.setText(str)

    # 关于删除乘车人信息
    def trigger_delepassenger(self):
        self.ui.stackedWidget_2.setCurrentIndex(2)  # 跳转页面
        self.ui.stackedWidget_4.setCurrentIndex(1)
        self.ui.delepassname.clear()
        for mm in self.passengerinfo:
            self.ui.delepassname.addItem(mm[0])
        if self.ui.delepassname.currentIndex() == 0 and len(self.passengerinfo) != 0:
            name = self.ui.delepassname.currentText()
            info = self.from_pass_info(name)
            if info != None:
                self.ui.delename.setEnabled(False)
                self.ui.deleid.setEnabled(False)
                self.ui.delename.setText(info[0])
                self.ui.deleid.setText(info[1])
                self.ui.deletele.setText(info[2])
                self.ui.deletele.setEnabled(False)
        self.ui.delepassname.currentIndexChanged.connect(self.adddeleinfo)
        self.ui.delesure.clicked.connect(self.trigger_delesure)

    def trigger_delesure(self):
        name = self.ui.delepassname.currentText()
        i = self.ui.delepassname.currentIndex()
        del self.passengerinfo[i]
        self.ui.delepassname.clear()
        for mm in self.passengerinfo:
            self.ui.delepassname.addItem(mm[0])
        self.ui.delename.clear()
        self.ui.deleid.clear()
        self.ui.deletele.clear()
        QMessageBox.information(self, '成功', f'删除成功', QMessageBox.Close)

    def adddeleinfo(self):
        name = self.ui.delepassname.currentText()
        info = self.from_pass_info(name)
        if info != None:
            self.ui.delename.setEnabled(False)
            self.ui.deleid.setEnabled(False)
            self.ui.delename.setText(info[0])
            self.ui.deleid.setText(info[1])
            self.ui.deletele.setText(info[2])
            self.ui.deletele.setEnabled(False)

    # 关于查看乘车人信息
    def trigger_viewpassinfo(self):
        self.ui.stackedWidget_2.setCurrentIndex(3)

        self.ui.textBrowser.clear()
        for i in self.passengerinfo:
            self.ui.textBrowser.append('姓名: ' + i[0] + '\n' + '身份证号码: ' + i[1] + '\n' + '电话号码: ' + i[2] + '\n\n')

    def trigger_editpassenegr(self):

        self.ui.stackedWidget_2.setCurrentIndex(1)
        self.ui.editpassname.clear()
        for i in range(len(self.passengerinfo)):
            self.ui.editpassname.addItem(self.passengerinfo[i][0])
        print(2345)
        self.ui.editpassname.currentIndexChanged.connect(self.trigger_show_sth)
        print(1)

        # except Exception as e:
        #     print('chucuole')

    def trigger_show_sth(self):
        self.ui.stackedWidget_3.setCurrentIndex(0)
        name = self.ui.editpassname.currentText()
        print(name)
        info = []
        self.j = 0
        for i in self.passengerinfo:
            if name == i[0]:
                info = i
                break
            self.j += 1
        print(self.j)
        print(info)
        if info:
            self.ui.editname.setText(info[0])
            self.ui.editid.setText(info[1])
            self.ui.edittele.setText(info[2])

    def trigger_saveedit(self):
        self.trigger_edit()
        self.ui.stackedWidget_3.setCurrentIndex(5)  # 暂时不知道跳转到哪里去先乱写一下

    def trigger_pinfo(self):

        self.pass_back_flag = 1  # 表明返回到首页
        self.ui.stackedWidget.setCurrentIndex(3)

    def triger_addpassenger(self):
        self.ui.stackedWidget_2.setCurrentIndex(0)
        self.ui.addname.clear()
        self.ui.addid.clear()
        self.ui.addtele.clear()

    def trigger_edit(self):
        info = []
        erro = {'0': '姓名未填', '1': '身份证未填', '2': '电话号码未填', '3': '身份证号码格式不正确', '4': '电话号码格式不正确'}
        m = -1
        flag = False
        if self.ui.editname.text() == None:
            m = 0
        else:
            info.append(self.ui.editname.text())
        if self.ui.editid.text() == None:
            m = 1
        else:
            if len(self.ui.editid.text()) == 18:
                info.append(self.ui.editid.text())
            else:
                m = 3
        if self.ui.edittele.text() == None:
            m = 2
        else:
            if len(self.ui.edittele.text()) == 11:
                info.append(self.ui.edittele.text())
            else:
                m = 4

        if len(info) != 3:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', f'{erro[str(m)]}')
            msg_box.setWindowFlag(Qt.Drawer)
            msg_box.exec_()
        else:
            print('infosth:', info)
            self.passengerinfo[self.j] = info
            self.ui.editpassname.clear()
            for i in self.passengerinfo:
                self.ui.editpassname.addItem(i[0])
        # self.passengerinfo[self.j][1] = info[1]
        # self.passengerinfo[self.j][2] = info[2]

    def trigger_add(self):
        info = []
        self.tioazhuan_flag = 0
        erro = {'0': '姓名未填', '1': '身份证未填', '2': '电话号码未填', '3': '身份证号码格式不正确', '4': '电话号码格式不正确'}
        m = -1
        flag = False
        if self.ui.addname.text() == None:

            m = 0
        else:

            info.append(self.ui.addname.text())
        if self.ui.addid.text() == None:
            m = 1
        else:

            if len(self.ui.addid.text()) == 18:
                info.append(self.ui.addid.text())
            else:
                m = 3
        if self.ui.addtele.text() == None:
            m = 2
        else:
            if len(self.ui.addtele.text()) == 11:
                info.append(self.ui.addtele.text())
            else:
                m = 4
        if len(info) != 3:
            self.tioazhuan_flag = 1
            msg_box = QMessageBox(QMessageBox.Warning, '警告', f'{erro[str(m)]}')
            msg_box.setWindowFlag(Qt.Drawer)
            msg_box.exec_()
        else:
            self.passengerinfo.append(info)

    def trigger_addfinish(self):
        self.trigger_add()
        print('passflga', self.pass_back_flag)
        if self.pass_back_flag == 1:  # 表示是乘车人添加完成自己打开乘车人信息
            self.ui.stackedWidget_2.setCurrentIndex(5)
        else:
            if self.tiaozhuan_flag == 0:
                self.ui.stackedWidget.setCurrentIndex(4)  # 跳转到添加乘车人界面
                self.choose_pass()

    def trigger_addcontinue(self):
        self.trigger_add()
        self.triger_addpassenger()

    def get_book_tk_info_common(self):  # 获取不是不管飞机还是火车都能获取得到的信息
        self.from_ = self.ui.beginplace.text()
        self.to_ = self.ui.endplace.text()
        print('to_:', type(self.to_))
        if self.to_ == '':

            msg_box = QMessageBox(QMessageBox.Critical, '错误', '目的地未填写，请重新填写')
            msg_box.setWindowFlag(Qt.Drawer)
            msg_box.exec_()
            return False
        else:
            self.bbt = self.ui.beginbegintime.currentIndex()

            self.bet = self.ui.beginendtime.currentIndex()

            if self.bbt > self.bet:
                msg_box = QMessageBox(QMessageBox.Warning, '警告', '出发时间段开始时间小于结束时间，请重新填写')
                msg_box.setWindowFlag(Qt.Drawer)
                msg_box.exec_()
                return False
        return True

    def trigger_airsignle(self):
        self.flag = 2  # 表示是飞机票
        self.ds_flag = 0  # 表示单程
        self.ui.loginwarn.setText('请登录携程账号')
        self.ui.stackedWidget.setCurrentIndex(2)
        # 单程对往返的禁止填写
        self.ui.enddate.setEnabled(False)
        self.ui.airsitetype.setEnabled(True)
        # self.ui.endplace.setEnabled(False)
        self.ui.endendtime.setEnabled(False)
        self.ui.endbegintime.setEnabled(False)
        self.ui.cartype.setEnabled(False)
        self.ui.sitetype.setEnabled(False)
        # 只能买今天以及以后的
        self.ui.begindate.setMinimumDate(QDate.currentDate())
        print(QDate.currentDate())

    def trigger_airdouble(self):
        self.flag = 2  # 表示是飞机票
        self.ds_flag = 1  # 表示往返
        self.ui.loginwarn.setText('请登录携程账号')
        self.ui.stackedWidget.setCurrentIndex(2)
        # 对往返的可以填写
        self.ui.enddate.setEnabled(True)
        self.ui.endplace.setEnabled(True)
        self.ui.endendtime.setEnabled(True)
        self.ui.endbegintime.setEnabled(True)
        self.ui.airsitetype.setEnabled(True)
        self.ui.cartype.setEnabled(False)
        self.ui.sitetype.setEnabled(False)
        # 只能买今天以及以后的
        self.ui.begindate.setMinimumDate(QDate.currentDate())
        self.ui.enddate.setMinimumDate(QDate.currentDate())

    def trigger_trainsignle(self):
        self.flag = 1  # 表示是火车票
        self.ds_flag = 0  # 表示是单程
        self.ui.loginwarn.setText('请登录12306账号')
        self.ui.stackedWidget.setCurrentIndex(2)
        # 单程对往返的禁止填写
        self.ui.enddate.setEnabled(False)
        # self.ui.endplace.setEnabled(False)
        self.ui.endendtime.setEnabled(False)
        self.ui.endbegintime.setEnabled(False)
        self.ui.airsitetype.setEnabled(False)
        self.ui.cartype.setEnabled(True)
        self.ui.sitetype.setEnabled(True)
        # 对某些时间的限定
        self.ui.begindate.setMinimumDate(QDate.currentDate())  # 只能买今天以及以后的
        print(self.ui.sitetype.currentIndex())
        print(self.ui.cartype.currentText())
        print(self.ui.cartype.currentIndex())

    def trigger_begininfo(self):
        self.ui.cancleall.setEnabled(True)
        flag = self.get_book_tk_info_common()

        if not flag:
            pass
        else:
            flag = True
            if self.flag == 1 and self.ds_flag == 0:  # 表示是火车票单程
                self.cartype = self.ui.cartype.currentIndex() + 1
                self.sitetype = self.ui.sitetype.currentIndex() + 2
            elif self.flag == 2 and self.ds_flag == 0:  # 表示飞机单程票
                self.airsitetype = self.ui.airsitetype.currentIndex() + 1
            elif self.flag == 2 and self.ds_flag == 1:  # b表示飞机票往返

                self.airsitetype = self.ui.airsitetype.currentIndex() + 1
                self.ebt = self.ui.endbegintime.currentIndex()
                self.eet = self.ui.endendtime.currentIndex()
                if self.ebt > self.eet:
                    msg_box = QMessageBox(QMessageBox.Warning, '警告', '返回时间段开始时间小于结束时间，请重新填写')
                    msg_box.setWindowFlag(Qt.Drawer)
                    msg_box.exec_()
                    flag = False
            else:
                msg_box = QMessageBox(QMessageBox.Warning, '警告', '还没有选择票的类型，请选择后进行尝试')
                msg_box.setWindowFlag(Qt.Drawer)
                msg_box.exec_()
                flag = False
            if flag:
                if len(self.passengerinfo) > 0:  # 说明有乘客信息直接跳转到登录界面
                    self.ui.stackedWidget.setCurrentIndex(4)  # 是跳转到登录界面进行乘客的选择
                    self.choose_pass()
                else:
                    # 需要添加乘车人的额信息
                    self.pass_back_flag = 0  # 表示跳转到登录界1的话跳转到首页
                    self.ui.stackedWidget.setCurrentIndex(3)  # 乘车人信息的添加

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.isMaximized() == False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, mouse_event):
        if QtCore.Qt.LeftButton and self.m_flag:
            self.move(mouse_event.globalPos() - self.m_Position)
            mouse_event.accept()

    def mouseReleaseEvent(self, mouse_event):
        self.m_flag = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def restore_or_maximize_window(self):  # 放大缩小
        if self.isMaximized():
            self.showNormal()
            pass
            # self.ui.max.setIcon(QtGui.QIcon(u':/图标/最大化.png'))
        else:
            self.showMaximized()

    def minimize_window(self):  # 最小化
        #

        self.showMinimized()


if __name__ == '__main__':
    app = QApplication([])
    win = BookTicket()
    win.resize(1500, 1000)
    sys.exit(app.exec_())
