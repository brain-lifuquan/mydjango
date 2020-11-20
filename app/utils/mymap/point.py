import math
import heapq
from .segment import Segment
from .region import Region


class Point:
    # 经纬度精度 小数点后面的位数 通过设置Point.precision 可以指定精度
    precision = 5

    def __init__(self, lng, lat):
        lng = float(lng)
        lat = float(lat)
        if lng < -180 or lng > 180:
            raise ValueError('经度必须在[-180° - 180°]范围内，输入值“{2}”超出范围。')
        if lat < -90 or lat > 90:
            raise ValueError('纬度必须在[-90° - 90°]范围内，输入值“{2}”超出范围。')
        self.lng = round(lng, self.precision)
        self.lat = round(lat, self.precision)

    def to_json(self):
        return {
            'lng': self.lng,
            'lat': self.lat,
        }

    def __str__(self):
        return str(self.to_json())

    def __repr__(self):
        return 'Point: {}'.format(str(self))

    def __eq__(self, other):
        if other:
            if id(self) == id(other):
                return True
            if self.lng == other.lng and self.lat == other.lat:
                return True
        return False

    def __hash__(self):
        return hash(self.lng) ^ hash(self.lat)

    def distance(self, other):
        # other 是另一个点
        if isinstance(other, Point):
            return distence(self.lng, self.lat, other.lng, other.lat)
        # other 是一条线段
        elif isinstance(other, Segment):
            dis0 = self.distance(other.ends[0])
            dis1 = self.distance(other.ends[1])
            # 问题转化为已知3角形3条边的长度，求一个顶点到底边的距离 锐角三角形为高 钝角三角形为短边
            # 底角存在钝角
            if abs(math.pow(dis0, 2) - math.pow(dis1, 2)) > math.pow(other.get_length(), 2):
                return min([dis0, dis1])
            # 底角权威锐角 使用海伦公式求三角形的高
            else:
                p = (dis0 + dis1 + other.get_length()) / 2
                s = math.sqrt(p * (p - other.get_length()) * (p - dis0) * (p - dis1))
            return s * 2 / other.get_length()
        # other 是一个区域 则返回一个二元组 分别为点到边界上的最近及最远距离
        elif isinstance(other, Region):
            # 计算到每个顶点的距离
            list_dis = [self.distance(point) for point in other.ends]
            max_dis = max(list_dis)
            # 使用heapq堆排序算法进行排序选定最近的两个距离
            min_n = 2
            temp = map(list_dis.index, heapq.nsmallest(min_n, list_dis))
            temp = list(temp)
            # 距离最近的两个顶点相邻, 则最近距离
            if abs(temp[0] - temp[1]) == 1:
                pa = other.ends[temp[0]]
                pb = other.ends[temp[1]]
                segment = Segment(pa, pb)
                min_dis = self.distance(segment)
            # 距离最近的两个顶点不相邻, 需要计算到4条边的距离
            else:
                pa = other.ends[temp[0]]
                pb = other.ends[temp[1]]
                ends_number = len(other.ends)
                index_a1 = divmod(temp[0] + 1, ends_number)[1]
                pa1 = other.ends[index_a1]
                dis_a1 = self.distance(Segment(pa, pa1))
                index_a2 = divmod(temp[0] + ends_number - 1, ends_number)[1]
                pa2 = other.ends[index_a2]
                dis_a2 = self.distance(Segment(pa, pa2))
                index_b1 = divmod(temp[1] + 1, ends_number)[1]
                pb1 = other.ends[index_b1]
                dis_b1 = self.distance(Segment(pb, pb1))
                index_b2 = divmod(temp[1] + ends_number - 1, ends_number)[1]
                pb2 = other.ends[index_b2]
                dis_b2 = self.distance(Segment(pb, pb2))
                min_dis = min([dis_a1, dis_a2, dis_b1, dis_b2])
            return min_dis, max_dis
        else:
            raise TypeError('输入值应为Point或Segment或Region的实例')

    def azimuth(self, other):
        """求self到other的射线的角度,正北为0度"""
        # 两点相同
        if self == other:
            raise ValueError("相同的两个点不存在方向角")
        if isinstance(other, Point):
            # 两点不同 但是纬度相同
            if self.lat == other.lat:
                if self.lng > other.lng:
                    return 270
                else:
                    return 90
            # 两点经度相同
            if self.lng == other.lng:
                if self.lat > other.lat:
                    return 180
                else:
                    return 0
            # 经度 纬度 都不同  组1个直角三角形  p0是直角顶点 dis1 和dis2 是直角边
            p0 = Point(self.lng, other.lat)
            dis1 = p0.distance(self)
            dis2 = p0.distance(other)
            # 反正切函数  结果是弧度  此时的角度并非以正北为0度
            azimuth = math.atan(dis2 / dis1)
            # 转换成角度并取整
            azimuth = round(azimuth * 180 / math.pi, 0)
            # 将角度转化成正北为0度的表示方式 方法是按不同的区间进行计算
            if other.lng > self.lng and other.lat > self.lat:
                return azimuth
            elif other.lng > self.lng and other.lat < self.lat:
                return 180 - azimuth
            elif other.lng < self.lng and other.lat < self.lat:
                return 180 + azimuth
            else:
                return 360 - azimuth
        elif isinstance(other, Region):
            return self.azimuth(other.get_center())
        else:
            raise TypeError('输入值应为Point或Region的实例')

    def in_region(self, region):
        """
        判断Point与Region实例的位置关系
        判断方法： 从被测点开始向右画一条射线，考察射线与区域边框的交点数量
        交点数量为奇数，说明被测点在区域内
        交点数量为偶数， 说明被测点在区域外
        """
        if not isinstance(region, Region):
            raise TypeError('输入值应为Region的实例')
        result = False
        # 如果在框外,直接返回False, 只有在框内的需要继续判断
        border = region.get_border()
        if border['minlng'] <= self.lng <= border['maxlng'] and border['minlat'] <= self.lat <= border['maxlat']:
            ends_number = len(region.ends)
            for i in range(ends_number):
                p1 = region.ends[i]
                # p2索引可能为0
                index_p2 = divmod(i + 1, ends_number)[1]
                p2 = region.ends[index_p2]
                # 判断测试点是否在本次测试的边的范围内（y轴） 只有在范围内，才可能产生交点
                if p1.lat < self.lat < p2.lat or p2.lat < self.lat < p1.lat:
                    # 判断是否有交点  求一下两点连线上 testy对应的x值
                    if self.lng < (p2.lng - p1.lng) * (self.lat - p1.lat) / (p2.lat - p1.lat) + p1.lng:
                        # 有1次交点就取反1次
                        result = not result
                elif self.lat == p1.lat:
                    # 被测点穿越顶点1
                    if self.lat > p2.lat and self.lng < p1.lng:
                        # 如果顶点2在射线下侧， 并且被测点在顶点1左侧（相等情况在上面已考虑），认为是一次穿越，取反
                        result = not result
                elif self.lat == p2.lat:
                    # 北侧点穿越顶点2
                    if self.lat > p1.lat and self.lng < p2.lng:
                        result = not result
        return result


def distence(lng1, lat1, lng2, lat2):
    """
    计算经纬度 （lng1, lat1） 和 （lng2, lat2）之间的距离，单位 米
    :param lng1:
    :param lat1:
    :param lng2:
    :param lat2:
    :return:
    """
    # 地球半径 单位米
    earth_redius = 6378137
    radlat1 = rad(lat1)
    radlat2 = rad(lat2)
    _a = radlat1 - radlat2
    _b = rad(lng1) - rad(lng2)
    _s = 2 * math.asin(
        math.sqrt(
            math.pow(math.sin(_a / 2), 2) +
            math.cos(radlat1) * math.cos(radlat2) *
            math.pow(math.sin(_b / 2), 2)
        )
    )
    return round(_s * earth_redius, 1)


def rad(_d):
    """
    角度转化为弧度
    :param _d: 角度
    :return:
    """
    return _d * math.pi / 180.0
