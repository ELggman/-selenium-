import requests

import json

city = {'深圳': 'SZX', '无锡': 'WUX'}  ##定义一个存放城市和对应三字码的字典，这里就随便写两个城市
url = 'https://flights.ctrip.com/itinerary/api/12808/products'
headers = {
    'User-Agent': UserAgent().chrome,
    "Content-Type": "application/json"}


def pachong(dcity, acity, date):
    request_payload = {"flightWay": "Oneway",
                       "army": "false",
                       "classType": "ALL",
                       "hasChild": 'false',
                       "hasBaby": 'false',
                       "searchIndex": 1,
                       "portingToken": "3fec6a5a249a44faba1f245e61e2af88",
                       "airportParams": [
                           {"dcity": city.get(dcity),
                            "acity": city.get(acity),
                            "dcityname": dcity,
                            "acityname": acity,
                            "date": date}]}  ##这里是需要传入的参数
    response = requests.post(url, headers=headers, data=json.dumps(request_payload))  # 发送post请求
    data = json.loads(response.text)['data']
    datalist = data.get("routeList")  ##得到存放所有航班信息的列表
    for num in range(len(datalist)):  ##遍历所有航班
        flight = datalist[num].get("legs")[0].get("flight")  ##找到航班信息
        flight_no = flight.get("flightNumber")  ##航班号
        plane_type = flight.get("craftTypeName")  ##机型
        departuredate = flight.get("departureDate")  ##出发时间
        arrivaldate = flight.get("arrivalDate")  ##到达时间
        print(flight_no, '---', plane_type, '---', departuredate, '---', arrivaldate)  ##打印结果
        print('-------------------------------------------------------------------')


if __name__ == '__main__':
    pachong('深圳', '无锡', '2020-06-28')