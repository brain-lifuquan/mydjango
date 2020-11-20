import json
from app.utils import mymap


class Region:

    def __init__(self, fmt_str):
        # 可以接收 json_str 或者 单引号的类似json_str结构
        # 也可以接收  {[,]; 连接的经纬度
        if "'" in fmt_str:
            fmt_str = fmt_str.replace("'", '"')
        try:
            reg_dict = json.loads(fmt_str)
        except ValueError:
            # 去掉全部的 {} 和 []
            points = fmt_str.replace('{', '').replace('}', '').replace('[', '').replace(']', '')
            # 每对经纬度之间时以；间隔的
            points = points.split(';')
            # 经度和纬度间以，分割
            points = (s.split(',') for s in points)
            points = [mymap.Point(*_l) for _l in points]
        else:
            if 'ends' in reg_dict.keys():
                points = [mymap.Point(**p) for p in reg_dict['ends']]
            else:
                raise ValueError("输入参数中应包含'ends'")
        # 去掉points中相邻的重复点位
        temp_point = None
        list_point = []
        for point in points:
            if point != temp_point:
                temp_point = point
                list_point.append(point)
        # 闭合区域的第一个点和最后一个点应该相同, 为计算方便,默认去掉在ends里不包含最后一个重复的点
        # 如果第一个点和最后一点个相同, 则去除
        if list_point[0] == list_point[-1]:
            list_point = list_point[0:-1]
        if len(list_point) < 3:
            raise ValueError('一个闭合区域区域至少要包含3个不重合的经纬度点')
        # 如果使用生成器，只能遍历一次，转化成tuple对象就不再有此限制
        self.ends = tuple(_p for _p in list_point)

    def to_json(self):
        _l = []
        for _p in self.ends:
            _l.append(_p.to_json())
        return {
            'ends': _l
        }

    def __str__(self):
        return str(self.to_json())

    def __repr__(self):
        return 'Region: {}'.format(str(self))

    def get_border(self):
        _lngs = []
        _lats = []
        # ends 可能是一个生成器的性质， 不能多次遍历
        for _p in self.ends:
            _lngs.append(_p.lng)
            _lats.append(_p.lat)
        return {
            'maxlng': max(_lngs),
            'maxlat': max(_lats),
            'minlng': min(_lngs),
            'minlat': min(_lats),
        }

    def get_center(self):
        border = self.get_border()
        return mymap.Point((border['maxlng'] + border['minlng']) / 2, (border['maxlat'] + border['minlat']) / 2)
