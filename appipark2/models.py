from operator import methodcaller
from django.db import models


class MyModel(models.Model):
    def __str__(self):
        if hasattr(self, 'name'):
            name = self.name
        else:
            name = self.pk
        return '{}: {}'.format(self._meta.verbose_name, name)

    @classmethod
    def get_listview_fields(cls):
        if hasattr(cls, 'listview_fields') and cls.listview_fields:
            return [dict(name=field.name, verbose_name=field.verbose_name) for field in cls.listview_fields]
        else:
            return [dict(name=field.name, verbose_name=field.verbose_name) for field in cls._meta.fields if field.name != 'id']

    def values_to_listview_dict(self):
        dict_obj = {}
        if hasattr(self, 'listview_fields'):
            listview_fields = self.listview_fields
        else:
            listview_fields = [field for field in self._meta.fields if field.name != 'id']
        for field in listview_fields:
            method_name = 'get_{}_display'.format(field.name)
            if hasattr(self, method_name):
                dict_obj[field.name] = methodcaller(method_name)(self)
            elif field.get_internal_type() == 'ForeignKey':
                dict_obj[field.name] = str(getattr(self, field.name))
            else:
                dict_obj[field.name] = field.value_to_string(self)
        return dict_obj

    class Meta:
        abstract = True


class Equipment(MyModel):
    type_choices = [(1, 'GPS'), ]
    state_choices = [(0, '离线'), (1, '在线')]
    name = models.CharField(verbose_name='终端名称', max_length=40, unique=True)
    eid = models.CharField(verbose_name='终端标识', max_length=12, unique=True)
    type = models.IntegerField(verbose_name='终端类型', choices=type_choices)
    state = models.IntegerField(verbose_name='终端状态', choices=state_choices)
    comment = models.CharField(verbose_name='备注', max_length=200, blank=True)

    listview_fields = [name, eid, type, state]

    class Meta:
        verbose_name = '设备'


class Vehicle(MyModel):
    type_choices = [(1, '小巴'), (2, '中巴')]
    name = models.CharField(verbose_name='车牌号', max_length=40, unique=True)
    type = models.IntegerField(verbose_name='车辆类型', choices=type_choices)
    location = models.ForeignKey(Equipment, on_delete=models.PROTECT, verbose_name='定位设备')
    comment = models.CharField(verbose_name='备注', max_length=200, blank=True)

    listview_fields = [name, type, location]

    class Meta:
        verbose_name = '车辆'


class Route(models.Model):
    choice_routetype = [(1, '早班车'), (2, '晚班车')]
    name = models.CharField(verbose_name='线路名称', max_length=40, unique=True)
    type = models.IntegerField(verbose_name='线路类型', choices=choice_routetype)
    runningtime = models.CharField(verbose_name='运行时间', max_length=100)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, verbose_name='车牌号')
    comment = models.CharField(verbose_name='备注', max_length=200, blank=True)

    class Meta:
        verbose_name = '班车线路'


class Polyline(models.Model):
    points = models.TextField()
    orderid = models.IntegerField()
    route = models.ForeignKey('Route', on_delete=models.PROTECT)


class Station(models.Model):
    name = models.CharField(verbose_name='站点名称', max_length=40)
    lng = models.FloatField(verbose_name='站点经度')
    lat = models.FloatField(verbose_name='站点纬度')
    route = models.ForeignKey(Route, on_delete=models.PROTECT)
    orderid = models.IntegerField(verbose_name='站点序号')

    def __str__(self):
        return self.name


class LocationRecord(MyModel):
    eid = models.CharField(verbose_name='终端标识', max_length=12)
    time = models.DateTimeField(verbose_name='定位时间', auto_now=True)
    lng = models.FloatField(verbose_name='经度')
    lat = models.FloatField(verbose_name='纬度')

    class Meta:
        verbose_name = '定位记录'


class RoutePath(models.Model):
    route = models.ForeignKey(Route, on_delete=models.PROTECT)
    pathindex = models.IntegerField()
    orderid = models.IntegerField()
    lng = models.FloatField()
    lat = models.FloatField()
