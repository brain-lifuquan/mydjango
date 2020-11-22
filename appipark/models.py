import re
from django.core.exceptions import ValidationError
from django.db import models
from .utils import myfunc


class MaterialType(models.Model):
    # 类型名称 唯一
    name = models.CharField(verbose_name='素材类型', max_length=20, unique=True)
    # 类型中文名 唯一
    name_zh = models.CharField(verbose_name='素材类型', max_length=20, unique=True)
    # 应用于input type=file的 accpt 参数 限制输入类型
    file_selector_accept = models.CharField(verbose_name='类型选择器', max_length=200)

    def __str__(self):
        return self.name


# 视频素材类
class Material(models.Model):
    # name 唯一
    name = models.CharField(verbose_name='素材名称', max_length=40, unique=True)
    # 素材类型 不使用外键，使用字段进行关联 type字段和MaterialType的name字段一致
    # type = models.ForeignKey(MaterialType, verbose_name='素材类型', on_delete=models.PROTECT)
    type = models.CharField(verbose_name='素材类型', max_length=20)
    # 素材文件
    file = models.FileField(verbose_name='素材文件', upload_to=myfunc.upload_to_file_path)
    # 素材缩略图
    thumbnail = models.ImageField(verbose_name='缩略图', upload_to=myfunc.upload_to_thumbnail_path)


# 节目分辨率
class ScaleType(models.Model):
    # name 唯一
    name = models.CharField(verbose_name='分辨率', max_length=20, unique=True)

    def clean(self):
        # 使用正则表达式检查name字段 必须是 正整数*正整数
        name_pattern = re.compile(r'^[1-9]\d*\*[1-9]\d*$')
        if name_pattern.match(self.name):
            super(ScaleType, self).clean()
        else:
            raise ValidationError('分辨率格式应为 宽*高 格式, 例: 1366*768')

    def __str__(self):
        return self.name


# 节目
class Program(models.Model):
    # name 唯一
    name = models.CharField(verbose_name='节目名称', max_length=40, unique=True)
    # 与 ScaleType name 字段对应
    scale_type = models.ForeignKey(ScaleType, on_delete=models.PROTECT, verbose_name='分辨率')
    #  文件路径
    path = models.CharField(max_length=200)
    # 存储空间--文件大小
    storage = models.FloatField(verbose_name='文件大小(M)')
    # 节目时长
    duration = models.IntegerField(verbose_name='播放时长(秒)')
    # 格式化以后的json
    json_input = models.CharField(max_length=2000)
    # 生成的ffmpegcmd
    ffmpegcmd = models.CharField(max_length=2000)


# 设备
class Equipment(models.Model):
    # name 唯一
    name = models.CharField(verbose_name='设备ID', max_length=40, unique=True)
    # 设备存储空间
    storage_all = models.FloatField(verbose_name='存储总量(M)')
    # 设备的可用存储空间
    storage_free = models.FloatField(verbose_name='可用存储(M)')
    # 设备安装位置
    location = models.CharField(verbose_name='设备位置', max_length=100)
    # 设备当前状态
    status = models.CharField(verbose_name='设备状态', max_length=40)
    # 轮播状态
    # wheel = models.CharField(verbose_name='轮播状态', max_length=20)
    wheel = models.BooleanField(verbose_name='轮播状态')
    # 播放开始时间
    start_time = models.CharField(verbose_name='开始时间', max_length=20)
    # 播放结束时间
    end_time = models.CharField(verbose_name='结束时间', max_length=20)


# 设备中的节目列表
class EquipmentProgram(models.Model):
    # 节目名称
    program = models.CharField(verbose_name='节目名称', max_length=40)
    # 设备id
    equipment = models.CharField(verbose_name='设备ID', max_length=40)
    # 在播放列表中的index -1 表示不在播放列表中
    index = models.IntegerField(verbose_name='列表序号')

    class Meta:
        unique_together = ['program', 'equipment']
