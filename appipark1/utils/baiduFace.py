# -*- coding: utf-8 -*-

"""
Created on 2019年11月5日

@author: SNIPER
"""

import requests
import json
import base64


def get_access_token():
    # posturl = "http://106.12.114.89/baidu"
    # headers = {'Content-Type': "application/json"}
    # body = json.dumps({"checkInfo": "hyue1596321"})
    # req = requests.post(posturl, data=body, headers=headers)
    # print(req.text)
    # return req.text
    return '24.6bd68cbeae2eb951667fd380a9e1bac5.2592000.1576305901.282335-17240840'


def getImg64(imgpath):
    with open(imgpath, "rb") as f:
        base64_data = base64.b64encode(f.read())
        s = base64_data.decode()
        # print('data:image/jpeg;base64,%s'%s)
        return s


'''
人脸注册（图片地址，用户分组，用户ID）
img_path:传入本地图片地址，后在程序内进行base64编码，base64编码后的图片大小不超过2M
group_id:用户组id，标识一组用户（由数字、字母、下划线组成），长度限制48B，目前三个分组：employee,visitor,blackList
user_id：用户id（由数字、字母、下划线组成），长度限制128B
'''


def face_add(img_path, group_id, user_id):
    acct = get_access_token()
    posturl = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add?access_token={}".format(acct)
    headers = {'Content-Type': "application/json"}
    body = json.dumps(
        {"image": getImg64(img_path), 
         "image_type": "BASE64",
         "group_id": group_id,
         "user_id": user_id,
         "action_type": "REPLACE", })
    req = requests.post(posturl, data=body, headers=headers)
    req_dic = json.loads(req.text)
    # print(req_dic)
    rst_dic = {}
    rst_dic["error_code"] = req_dic["error_code"]
    rst_dic["error_msg"] = req_dic["error_msg"]
    rst_dic["log_id"] = req_dic["log_id"]
    rst_dic["timestamp"] = req_dic["timestamp"]
    rst_dic["cached"] = req_dic["cached"]
    if req_dic["result"] is not None:
        result = req_dic["result"]
        rst_dic["face_token"] = result["face_token"]
        rst_dic["left"] = result["location"]["left"]
        rst_dic["top"] = result["location"]["top"]
        rst_dic["width"] = result["location"]["width"]
        rst_dic["height"] = result["location"]["height"]
    return rst_dic


'''
人脸删除（用户分组，用户ID，face_token）
group_id:用户组id（由数字、字母、下划线组成） 长度限制48B，删除指定group_id中的user_id信息
user_id:用户id（由数字、字母、下划线组成），长度限制128B
face_token:需要删除的人脸图片token，（由数字、字母、下划线组成）长度限制64B
'''


def face_del(group_id, user_id, face_token):
    acct = get_access_token()
    posturl = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/face/delete?access_token={}".format(acct)
    headers = {'Content-Type': "application/json"}
    body = json.dumps(
        {"group_id": group_id,
         "user_id": user_id,
         "face_token": face_token,})
    req = requests.post(posturl, data=body, headers=headers)
    return json.loads(req.text)


''''
人脸搜索（图片地址）
img_path:传入本地图片地址，后在程序内进行base64编码，base64编码后的图片大小不超过2M
group_id_list:从指定的group中进行查找 用逗号分隔，上限10个
'''


def face_search(img_path,group_id_list):
    acct = get_access_token()
    posturl = "https://aip.baidubce.com/rest/2.0/face/v3/search?access_token={}".format(acct)
    headers = {'Content-Type': "application/json"}
    body = json.dumps(
        {"image": getImg64(img_path), 
         "image_type": "BASE64",
         "group_id_list": group_id_list,
         "max_user_num": 1 })
    req = requests.post(posturl, data=body, headers=headers)
    req_dic = json.loads(req.text)
    # print(req_dic)
    rst_dic = {}
    rst_dic["error_code"] = req_dic["error_code"]
    rst_dic["error_msg"] = req_dic["error_msg"]
    rst_dic["log_id"] = req_dic["log_id"]
    rst_dic["timestamp"] = req_dic["timestamp"]
    rst_dic["cached"] = req_dic["cached"]
    if req_dic["result"] is not None:
        result = req_dic["result"]
        rst_dic["face_token"] = result["face_token"]
        rst_dic["group_id"] = result["user_list"][0]["group_id"]
        rst_dic["user_id"] = result["user_list"][0]["user_id"]
        rst_dic["user_info"] = result["user_list"][0]["user_info"]
        rst_dic["score"] = result["user_list"][0]["score"]
    return rst_dic


if __name__ == "__main__":
    # result=face_add("img2.jpg","visitor","test")
    # result=face_del("visitor","test","ce369cb5879f6203ef6929b1f586144a")
    result = face_search("33ca8e42d27fedebf268c4659061a958.jpg", "employee,visitor, blackList")
    print(result)
