"""
# 文件说明 :windows的一些函数
# @Time :  2022-3-26 14:23
# @Author : hewuhun
# @File : windows_common.py 
# @Software : python
"""
# !/usr/bin/python
# -*- coding: utf-8 -*-
import win32api
import win32con
import win32gui
import win32print


class WindowsCommon:
    """
    windows的一些函数
    """

    def __init__(self):
        self.hdc = win32gui.GetDC(0)

    def getScreenResolution(self):
        """
        得到屏幕的真实分辨率
        :return:
        """
        sx = win32print.GetDeviceCaps(self.hdc, win32con.DESKTOPHORZRES)
        sy = win32print.GetDeviceCaps(self.hdc, win32con.DESKTOPVERTRES)
        return sx, sy

    @staticmethod
    def getScreenCurrent():
        """
        得到屏幕缩放后的分辨率
        :return:
        """
        sx = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        sy = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        return sx, sy

    def getScreenScaleRate(self):
        """
        得到当前屏幕的缩放比例
        :return:
        """
        screen_x, screen_y = self.getScreenResolution()
        current_x, current_y = self.getScreenCurrent()
        rate = round(screen_x / current_x, 2)
        return rate


if __name__ == '__main__':
    windows_common = WindowsCommon()
    print(windows_common.getScreenScaleRate())