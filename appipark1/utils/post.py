# -*- coding: utf-8 -*-
'''
使用post方法把文件和数据发送到服务器
'''

import requests
import json
import base64
from datetime import datetime

def getImg64(imgpath):
    with open(imgpath, "rb") as f:
        base64_data = base64.b64encode(f.read())
        s = base64_data.decode()
        # print('data:image/jpeg;base64,%s'%s)
        return s

def post_to_server(img_path):
    # 上传地址， 暂时没有做登录验证
    posturl = 'http://127.0.0.1:8000/zhuapai/'
    # 使用json格式上传
    headers = {'Content-Type': "application/json"}
    # 上传的数据
    data = json.dumps({
        "image": getImg64(img_path),
    })
    # 发送post请求，正常回复位'OK'
    req = requests.post(posturl, data=data, headers=headers)
    return req

if __name__ == '__main__':
    img = 'C:\\Users\\Administrator\\Desktop\\李福全-131182198504092057.png'
    req = post_to_server(img)
    print(req)