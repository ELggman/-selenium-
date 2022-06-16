import smtplib
from email.mime.text import MIMEText
from email.header import Header


class Send_QQ_Email:
    def __init__(self, to_addr, content):
        self.from_addr = '41384896@qq.com'
        self.to_addr = to_addr
        self.password = 'wynbizrpnsnjcaeh'  # 授权码
        self.content = content

        self.smtp_server = 'smtp.qq.com'  # 发信服务器

    def send(self):
        # 第一个参数为内容，第二个参数为内容格式 plain为纯文本 发送链接可以使用html，第三个参数是 编码
        msg = MIMEText(self.content, 'plain', 'utf-8')
        msg['From'] = Header('抢票系统')
        msg['To'] = Header('用户')
        msg['Subject'] = Header('Python Email Test')

        server = smtplib.SMTP_SSL(self.smtp_server)
        server.connect(self.smtp_server, 465)  # 连接指定的服务器 self.smtp_server 端口号：465
        server.login(self.from_addr, self.password)  # 登录
        server.sendmail(from_addr=self.from_addr, to_addrs=self.to_addr, msg=msg.as_string())  # 发送邮件
        server.quit()  # 关闭服务器




if __name__ == '__main__':
    content = '稳过，老铁'
    se = Send_QQ_Email('1466590740@qq.com', content)
    se.send()
