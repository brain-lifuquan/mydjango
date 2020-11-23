# -*- coding: utf-8 -*-
# 各种数据转换

from os import path

def get_unique_str():
    print('enter myutils.get_unique_str')
    import uuid
    import hashlib
    uuid_str = str(uuid.uuid4())
    md5 = hashlib.md5()
    md5.update(uuid_str.encode('utf-8'))
    return md5.hexdigest()

def save_uploadfile(file):
    print('enter myutils.save_file')
    # 获取一个不重复的face_id 32位16进制字符串 作为face_id
    face_id = get_unique_str()
    # photo 保存文件在media文件夹下的目录信息
    photo = 'blacklist/' + face_id + '.' + file.name.split('.')[-1]
    # photo = path.join('blacklist', photo)
    # 存储文件系统目录
    from ipark import settings
    file_path = path.join(settings.MEDIA_ROOT, photo)
    # 写入文件
    with open(file_path, 'wb') as f:
        for i in file.chunks():
            f.write(i)
    print(file_path, '----写入完成')
    result = {
        'face_id': face_id,
        'photo': photo,
        'file_path': file_path,
    }
    return result


def get_query_info(query_str):
    # 每条属性之间以****分割符间隔开， 属性名与属性值之间以----分割
    str_list = query_str.split('****')[:-1]
    result = {}
    for st in str_list:
        s = st.split('----')
        result[s[0]] = s[1]
    return result


def get_query_dict(query_info, obj):
    # 对 CharField 字段添加 __contains 以实现 模糊查询
    attrs = dict([(f.name, f.get_internal_type()) for f in obj._meta.fields])
    result = {}
    for key, value in query_info.items():
        if key in attrs.keys():
            if attrs[key] == 'CharField':
                result[key + '__contains'] = value
            else:
                result[key] = value
        else:
            raise MyError(key + '---字段错误')
    return result


# 将模型转换成字典格式
def todict(obj):
    # print('enter myutils.todic', obj)
    # 模型参数名
    attrlist = [f.name for f in obj._meta.fields]
    result = dict([(attr, getattr(obj, attr)) for attr in attrlist])
    # print(result)
    return result


# 自定义exception
class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
