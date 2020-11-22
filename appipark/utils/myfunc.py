import numpy
import cv2
import os
from io import BytesIO
from PIL import Image

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile

app_name = 'appipark1'


# upload_to 的目录
def upload_to_directory_path(instance):
    class_name = instance.__class__.__name__.lower()
    if hasattr(instance, 'type'):
        result = os.path.join(app_name, class_name, instance.type)
    else:
        result = os.path.join(app_name, class_name)
    return result


#  upload_to 的文件目录
def upload_to_file_path(instance, filename):
    directory_path = upload_to_directory_path(instance)
    result = os.path.join(directory_path, filename)
    return result


# upload_to 的文件缩略图目录
def upload_to_thumbnail_path(instance, filename):
    directory_path = upload_to_directory_path(instance)
    result = os.path.join(directory_path, 'thumbnail', filename)
    return result


def get_thumbnail(file, material_type, size):
    if material_type == 'video':
        image = get_video_frame(file)
    elif material_type == 'image' or material_type == 'bg_image':
        image = Image.open(file)
    else:
        raise ValueError("{} is not acceptable".format(material_type))
    image.thumbnail(size)
    buffer = BytesIO()
    image.save(buffer, 'PNG')
    image_name = file.name[0:file.name.rfind('.')] + '.PNG'
    image = InMemoryUploadedFile(file=buffer, field_name=None, name=image_name, content_type='image/png', size=ContentFile(buffer.getvalue()).tell, charset='utf8')
    return image


def get_video_frame(video):
    if isinstance(video, TemporaryUploadedFile):
        # VideoCapture()中参数是0，表示打开笔记本的内置摄像头，参数是视频文件路径则打开视频，如cap = cv2.VideoCapture("../test.avi")
        # 当文件比较大时 好像默认是超过2.5M django上传的文件是 TemporaryUploadedFile的实例， 可以用 .temporary_file_path()方法获取路径
        vidcap = cv2.VideoCapture(video.temporary_file_path())
    elif isinstance(video, InMemoryUploadedFile):
        # 上传较小的文件 时为InMemoryUploadedFile实例
        # 这个时候写入本地文件然后读取，这是个权益之计，
        path = os.path.join('utils', 'temp', video.name)
        with open(path, 'wb') as f:
            f.write(video.read())
        vidcap = cv2.VideoCapture(path)
    else:
        raise TypeError("need type TemporaryUploadedFile or InMemoryUploadedFile but got {}".format(type(video)))
    success, image = vidcap.read()
    image = Image.fromarray(numpy.uint8(image))
    return image


# 获取filepath路径对应文件大小，单位M 精度默认为2
def get_file_storage_size(filepath, precision=2):
    # 获取存储空间大小 单位字节
    filesize = os.path.getsize(filepath)
    # 单位从字节转化为 M
    filesize /= float(1024 * 1024)
    # 控制精度
    return round(filesize, precision)
