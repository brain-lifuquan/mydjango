import traceback
import json
import base64
from os import path
from datetime import datetime
from django.shortcuts import render, HttpResponse, redirect
from django.views import View
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
from .utils.pager import Pager
from .utils.baiduFace import face_add, face_del, face_search
from .utils import myutils
from . import models
from project import settings


class MyView(View):
    query_info = {}  # 页面传送的查询参数
    query_dict = {}  # 传递给filter的参数字典  与上面的区别在于对字符串字段添加了模糊查询
    current_page = 1  # 当前页码
    per_page = 20  # 每页显示数量
    deleted_visible = False  # 是否显示已删除

    # @method_decorator(login_required())

    def dispatch(self, request, *args, **kwargs):
        print('enter MyView.dispatch', request.method)
        return super(MyView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        post_type = request.POST.get('post_type')
        print('enter MyView.post', request.method, post_type)
        if post_type == 'add':
            return self.add_obj(request)
        elif post_type == 'get':
            return self.get_obj(request)
        elif post_type == 'edit':
            return self.edit_obj(request)
        elif post_type == 'delete':
            return self.delete_obj(request)
        elif post_type == 'recover':
            return self.recover_obj(request)
        elif post_type == 'delete_some':
            return self.delete_some(request)
        elif post_type == 'query':
            return self.query_obj(request)
        elif post_type == 'show_page':
            return self.show_page(request)
        elif post_type == 'change_deleted_visible':
            return self.change_deleted_visible(request)
        else:
            return HttpResponse(
                'post_type “{0}” 不合法，请联系管理员修复BUG！'.format(post_type))

    def add_obj(self, request):
        print('enter MyView.add_obj', request.POST)
        return HttpResponse('是不是忘记重写add_obj')

    def get_obj(self, request):
        print('enter MyView.get_obj', request.POST)
        return HttpResponse('是不是忘记重写get_obj')

    def edit_obj(self, request):
        print('enter MyView.edit_obj', request.POST)
        return HttpResponse('是不是忘记重写edit_obj')

    def delete_obj(self, request):
        print('enter MyView.delete_obj', request.POST)
        return HttpResponse('是不是忘记重写delete_obj')

    def recover_obj(self, request):
        print('enter MyView.recover_obj', request.POST)
        return HttpResponse('是不是忘记重写recover_obj')

    def delete_some(self, request):
        print('enter MyView.delete_some', request.POST)
        return HttpResponse('是不是忘记重写delete_some')

    def query_obj(self, request):
        print('enter MyView.query_obj', request.POST)
        return HttpResponse('是不是忘记重写query_obj')

    def show_page(self, request):
        print('enter TestView.show_page', request.POST)
        try:
            MyView.current_page = request.POST.get('current_page')
            MyView.per_page = request.POST.get('per_page')
            return HttpResponse('OK')
        except Exception as err:
            traceback.print_exc()
            return HttpResponse(repr(err))

    def change_deleted_visible(self, request):
        print('enter MyView.change_deleted_visible', request.POST)
        try:
            b = request.POST.get('deleted_visible')
            if b == 'False':
                MyView.deleted_visible = False
            else:
                MyView.deleted_visible = True
            print(MyView.deleted_visible)
            return HttpResponse('OK')
        except Exception as err:
            traceback.print_exc()
            return HttpResponse(repr(err))


class BlacklistView(MyView):
    def get(self, request):
        if self.deleted_visible:
            print(self.deleted_visible, True)
            obj_list = models.Blacklist.objects.filter(**self.query_dict)
        else:
            print(self.deleted_visible, False)
            obj_list = models.Blacklist.objects.filter(isdelete=False).filter(
                **self.query_dict)
        # 分页
        pager = Pager(current_page=BlacklistView.current_page,
                      total_items=obj_list.count(),
                      per_page=BlacklistView.per_page)
        obj_list = obj_list[pager.start():pager.end()]
        # 给返回数据添加网页标题
        data = {
            'title': 'test',
            'obj_list': obj_list,
            'pager': pager,
        }
        # 把筛选条件加到返回的obj中
        data.update(BlacklistView.query_info)
        data.update({'deleted_visible': BlacklistView.deleted_visible})
        return render(request, 'appipark1/blacklist.html', data)

    def add_obj(self, request):
        print('enter BlacklistView.add_obj', request.POST)
        try:
            # # 获取上传的文件并存储到media目录
            file = request.FILES.get('uploadfile')
            # # 存储前先获取一个不重复的face_id, 这个id同时作为存储在服务器上的文件名
            # face_id = myutils.get_unique_str()
            # name = face_id + '.' + file.name.split('.')[-1]
            # file_path = path.join(settings.MEDIA_ROOT, 'blacklist', name)
            # with open(file_path, 'wb') as f:
            #     for i in file.chunks():
            #         f.write(i)
            # print(file_path, '---已保存')
            if file:
                result = myutils.save_uploadfile(file)
                # 发送到百度并获取face_token
                face_add_result = face_add(result['file_path'], 'blackList',
                                           result['face_id'])
                if face_add_result['error_msg'] == 'SUCCESS':
                    obj = models.Blacklist(
                        photo=result['photo'],
                        tag=request.POST.get('tag'),
                        comment=request.POST.get('comment'),
                        face_id=result['face_id'],
                        face_token=face_add_result['face_token'],
                        isdelete=False,
                    )
                    obj.save()
                    return HttpResponse('OK')
                else:
                    return HttpResponse(face_add_result['error_msg'])
            else:
                return HttpResponse('uploadfile 不存在！')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def get_obj(self, request):
        try:
            obj_id = request.POST.get('id')
            obj = models.Blacklist.objects.get(id=obj_id)
            # 返回数据添加class属性
            data = {'class': 'blacklist'}
            # 将obj的自有属性添加到返回数据data
            data.update(myutils.todict(obj))
            # 返回数据data转换成json数据
            data = json.dumps(data)
            return HttpResponse(data)
        except Exception as e:
            # 打印报错
            traceback.print_exc()
            return HttpResponse(repr(e))

    def edit_obj(self, request):
        try:
            obj_id = request.POST.get('id')
            obj = models.Blacklist.objects.get(id=obj_id)
            # 此处需要修改图片信息， 并修改百度列表中 的信息
            # 获取上传的文件并存储到media目录
            file = request.FILES.get('uploadfile')
            if file:
                # # 存储前先获取一个不重复的face_id, 这个id同时作为存储在服务器上的文件名
                # face_id = myutils.get_unique_str()
                # name = face_id + '.' + file.name.split('.')[-1]
                # file_path = path.join(settings.MEDIA_ROOT, 'blacklist', name)
                # with open(file_path, 'wb') as f:
                #     for i in file.chunks():
                #         f.write(i)
                # print(file_path, '---已保存')
                result = myutils.save_uploadfile(file)
                # 发送到百度并获取face_token
                face_add_result = face_add(result['file_path'], 'blackList',
                                           result['face_id'])
                if face_add_result['error_msg'] == 'SUCCESS':
                    obj.face_token = face_add_result['face_token']
                    obj.face_id = result['face_id']
                    obj.photo = result['photo']
                    obj.tag = request.POST.get('tag')
                    obj.comment = request.POST.get('comment')
                    obj.save()
                    return HttpResponse('OK')
                else:
                    return HttpResponse(face_add_result['error_msg'])
            else:
                obj.tag = request.POST.get('tag')
                obj.comment = request.POST.get('comment')
                obj.save()
                return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_obj(self, request):
        print('enter BlacklistView.delete_obj', request.POST)
        try:
            # 此处需要删除百度list的图片
            obj_id = request.POST.get('id')
            obj = models.Blacklist.objects.get(id=obj_id)
            # 发送给百度并删除
            face_del_result = face_del(group_id='blackList',
                                       face_token=obj.face_token,
                                       user_id=obj.face_id)
            print(face_del_result)
            if face_del_result['error_msg'] == 'SUCCESS':
                obj.face_token = ''
                obj.isdelete = True
                obj.save()
                return HttpResponse('OK')
            else:
                print(face_del_result['error_msg'])
                return HttpResponse(face_del_result['error_msg'])
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def recover_obj(self, request):
        print('enter BlacklistView.recover_obj', request.POST)
        try:
            # 需要重新将图片发送给百度并注册face_token
            obj_id = request.POST.get('id')
            obj = models.Blacklist.objects.get(id=obj_id)
            file_path = path.join(settings.MEDIA_ROOT, obj.photo)
            # 发送到百度并获取face_token
            face_add_result = face_add(file_path, 'blackList', obj.face_id)
            if face_add_result['error_msg'] == 'SUCCESS':
                obj.face_token = face_add_result['face_token']
                obj.isdelete = False
                obj.save()
                return HttpResponse('OK')
            else:
                return HttpResponse(face_add_result['error_msg'])
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_some(self, request):
        print('enter BlacklistView.delete_some', request.POST)
        try:
            ids = request.POST.get('ids').split(',')
            success_list = []
            err_list = []
            for obj_id in ids:
                # 此处需要删除百度list的图片
                obj = models.Blacklist.objects.get(id=obj_id)
                # 发送给百度并删除
                face_del_result = face_del(group_id='blackList',
                                           face_token=obj.face_token,
                                           user_id=obj.face_id)
                if face_del_result['error_msg'] == 'SUCCESS':
                    obj.face_token = ''
                    obj.isdelete = True
                    obj.save()
                    success_list.append(obj)
                else:
                    err_list.append(face_del_result['error_msg'])
            if len(err_list) == 0:
                return HttpResponse('OK')
            else:
                return HttpResponse(err_list)
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def query_obj(self, request):
        print('enter BlacklistView.query_obj', request.POST)
        try:
            query_str = request.POST.get('query_str')
            BlacklistView.query_info = myutils.get_query_info(query_str)
            BlacklistView.query_dict = myutils.get_query_dict(
                BlacklistView.query_info, models.Blacklist)
            # 设置显示第一页
            BlacklistView.current_page = 1
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))


class EquipmentView(MyView):
    def get(self, request):
        print('enter EquipmentView.get', request.GET)
        if self.deleted_visible:
            # print(self.deleted_visible, True)
            obj_list = models.Equipment.objects.filter(**self.query_dict)
        else:
            # print(self.deleted_visible, False)
            obj_list = models.Equipment.objects.filter(isdelete=False).filter(
                **self.query_dict)
        # 分页
        pager = Pager(current_page=EquipmentView.current_page,
                      total_items=obj_list.count(),
                      per_page=EquipmentView.per_page)
        obj_list = obj_list[pager.start():pager.end()]
        # 给返回数据添加网页标题
        data = {
            'title': '设备管理',
            'obj_list': obj_list,
            'pager': pager,
        }
        # 把筛选条件加到返回的obj中
        data.update(EquipmentView.query_info)
        data.update({'deleted_visible': EquipmentView.deleted_visible})
        return render(request, 'appipark1/equipment.html', data)

    def add_obj(self, request):
        print('enter EquipmentView.add_obj', request.POST)
        try:
            obj = models.Equipment(
                name=request.POST.get('name'),
                type=request.POST.get('type'),
                location=request.POST.get('location'),
                state='在线',
                isdelete=False,
            )
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def get_obj(self, request):
        print('enter EquipmentView.get_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Equipment.objects.get(id=obj_id)
            # 返回数据添加class属性
            data = {'class': '设备'}
            # 将obj的自有属性添加到返回数据data
            data.update(myutils.todict(obj))
            # 返回数据data转换成json数据
            data = json.dumps(data)
            print(data)
            return HttpResponse(data)
        except Exception as e:
            # 打印报错
            traceback.print_exc()
            return HttpResponse(repr(e))

    def edit_obj(self, request):
        print('enter EquipmentView.edit_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Equipment.objects.get(id=obj_id)
            obj.name = request.POST.get('name')
            obj.type = request.POST.get('type')
            obj.location = request.POST.get('location')
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_obj(self, request):
        print('enter EquipmentView.delete_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Equipment.objects.get(id=obj_id)
            obj.isdelete = True
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def recover_obj(self, request):
        print('enter EquipmentView.recover_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Equipment.objects.get(id=obj_id)
            obj.isdelete = False
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_some(self, request):
        print('enter EquipmentView.delete_some', request.POST)
        try:
            ids = request.POST.get('ids').split(',')
            models.Equipment.objects.filter(id__in=ids).update(isdelete=True, )
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def query_obj(self, request):
        print('enter EquipmentView.query_obj', request.POST)
        try:
            query_str = request.POST.get('query_str')
            EquipmentView.query_info = myutils.get_query_info(query_str)
            EquipmentView.query_dict = myutils.get_query_dict(
                EquipmentView.query_info, models.Equipment)
            # 设置显示第一页
            EquipmentView.current_page = 1
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))


# 使用CBV处理登录
class Login(View):
    # 通过url访问login.html时为get方法
    def get(self, request):
        data = {
            'title': '登录',
            'msg': '',
        }
        return render(request, 'appipark1/login.html', data)

    # 表单提交时为post方法
    def post(self, request):
        # 使用get方法获取，如果没有此属性，返回None
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        # 使用django.contrib.auth 模块的认证方法进行账号密码验证,返回的时User对象
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            # user对象存在,说明验证通过
            auth.login(request, user)
            username_auth = user.first_name + ' ' + user.last_name
            if username_auth != ' ':
                request.session['username'] = username_auth
            else:
                request.session['username'] = username
            return redirect('app:index')
        else:
            # 验证未通过
            data = {
                'title': '登录',
                'msg': '账号或密码错误,请重新输入!!!',
            }
            return render(request, 'appipark1/login.html', data)


"""
抓拍记录有两种方式考虑：
1. 由抓拍设备识别面部并抓拍包含面部信息的照片，将照片传送到后台服务器，由后台服务器将抓拍图片发送到百度服务器进行人脸搜索，
根据搜索结果存储或抛弃抓拍图片
2. 由抓拍设备识别面部并抓拍照片，照片由抓拍设备进行人脸识别（或由抓拍设备发送给百度做人脸搜索），将结果进行处理后发送给后台。
"""


class RecordView(MyView):
    def get(self, request):
        # 不使用外键的话，需要修改这边获取数据的方式，把tag信息加进来，使用外键的话需要2层关联，合适吗？
        # 添加字段，把blacklist的图片也存进来就可以了
        print('enter RecordView.get', request.GET)
        if self.deleted_visible:
            # print(self.deleted_visible, True)
            obj_list = models.Record.objects.filter(**self.query_dict)
        else:
            # print(self.deleted_visible, False)
            obj_list = models.Record.objects.filter(isdelete=False).filter(
                **self.query_dict)
        # 分页
        pager = Pager(current_page=RecordView.current_page,
                      total_items=obj_list.count(),
                      per_page=RecordView.per_page)
        obj_list = obj_list[pager.start():pager.end()]
        # 给返回数据添加网页标题
        data = {
            'title': '黑名单标签管理',
            'obj_list': obj_list,
            'pager': pager,
        }
        # 把筛选条件加到返回的obj中
        data.update(RecordView.query_info)
        data.update({'deleted_visible': RecordView.deleted_visible})
        return render(request, 'appipark1/record.html', data)

    def add_obj(self, request):
        print('enter RecordView.add_obj', request.POST)
        try:
            obj = models.Record(
                name=request.POST.get('name'),
                comment=request.POST.get('comment'),
                isdelete=False,
            )
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def get_obj(self, request):
        print('enter RecordView.get_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Record.objects.get(id=obj_id)
            # 返回数据添加class属性
            data = {'class': '黑名单标签'}
            # 将obj的自有属性添加到返回数据data
            data.update(myutils.todict(obj))
            # 返回数据data转换成json数据
            data = json.dumps(data)
            print(data)
            return HttpResponse(data)
        except Exception as e:
            # 打印报错
            traceback.print_exc()
            return HttpResponse(repr(e))

    def edit_obj(self, request):
        print('enter RecordView.edit_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Record.objects.get(id=obj_id)
            obj.name = request.POST.get('name')
            obj.comment = request.POST.get('comment')
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_obj(self, request):
        print('enter RecordView.delete_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Record.objects.get(id=obj_id)
            obj.isdelete = True
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def recover_obj(self, request):
        print('enter RecordView.recover_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Record.objects.get(id=obj_id)
            obj.isdelete = False
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_some(self, request):
        print('enter RecordView.delete_some', request.POST)
        try:
            ids = request.POST.get('ids').split(',')
            models.Record.objects.filter(id__in=ids).update(isdelete=True, )
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def query_obj(self, request):
        print('enter RecordView.query_obj', request.POST)
        try:
            query_str = request.POST.get('query_str')
            RecordView.query_info = myutils.get_query_info(query_str)
            RecordView.query_dict = myutils.get_query_dict(
                RecordView.query_info, models.Record)
            # 设置显示第一页
            RecordView.current_page = 1
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))


class TagView(MyView):
    def get(self, request):
        print('enter TagView.get', request.GET)
        if self.deleted_visible:
            # print(self.deleted_visible, True)
            obj_list = models.Tag.objects.filter(**self.query_dict)
        else:
            # print(self.deleted_visible, False)
            obj_list = models.Tag.objects.filter(isdelete=False).filter(
                **self.query_dict)
        # 分页
        pager = Pager(current_page=TagView.current_page,
                      total_items=obj_list.count(),
                      per_page=TagView.per_page)
        obj_list = obj_list[pager.start():pager.end()]
        # 给返回数据添加网页标题
        data = {
            'title': '黑名单标签管理',
            'obj_list': obj_list,
            'pager': pager,
        }
        # 把筛选条件加到返回的obj中
        data.update(TagView.query_info)
        data.update({'deleted_visible': TagView.deleted_visible})
        return render(request, 'appipark1/tag.html', data)

    def add_obj(self, request):
        print('enter TagView.add_obj', request.POST)
        try:
            obj = models.Tag(
                name=request.POST.get('name'),
                comment=request.POST.get('comment'),
                isdelete=False,
            )
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def get_obj(self, request):
        print('enter TagView.get_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Tag.objects.get(id=obj_id)
            # 返回数据添加class属性
            data = {'class': '黑名单标签'}
            # 将obj的自有属性添加到返回数据data
            data.update(myutils.todict(obj))
            # 返回数据data转换成json数据
            data = json.dumps(data)
            print(data)
            return HttpResponse(data)
        except Exception as e:
            # 打印报错
            traceback.print_exc()
            return HttpResponse(repr(e))

    def edit_obj(self, request):
        print('enter TagView.edit_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Tag.objects.get(id=obj_id)
            obj.name = request.POST.get('name')
            obj.comment = request.POST.get('comment')
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_obj(self, request):
        print('enter TagView.delete_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Tag.objects.get(id=obj_id)
            obj.isdelete = True
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def recover_obj(self, request):
        print('enter TagView.recover_obj', request.POST)
        try:
            obj_id = request.POST.get('id')
            obj = models.Tag.objects.get(id=obj_id)
            obj.isdelete = False
            obj.save()
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def delete_some(self, request):
        print('enter TagView.delete_some', request.POST)
        try:
            ids = request.POST.get('ids').split(',')
            models.Tag.objects.filter(id__in=ids).update(isdelete=True, )
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))

    def query_obj(self, request):
        print('enter TagView.query_obj', request.POST)
        try:
            query_str = request.POST.get('query_str')
            TagView.query_info = myutils.get_query_info(query_str)
            TagView.query_dict = myutils.get_query_dict(
                TagView.query_info, models.Tag)
            # 设置显示第一页
            TagView.current_page = 1
            return HttpResponse('OK')
        except Exception as e:
            traceback.print_exc()
            return HttpResponse(repr(e))


# 主页
# @login_required
def index(request):
    data = {
        'title': '主页',
        'username': request.user.username,
    }
    return render(request, 'appipark1/index.html', data)


# 注销
# @login_required
def logout(request):
    # 使用django.contrib.auth模块的logout方法
    auth.logout(request)
    # 注销后重定向到登录界面
    return redirect('app:index')


def frindex(request):
    return render(request, 'appipark1/monitor.html')


# 抓拍照片上传
# 绕过csrf
@csrf_exempt
def zhuapai(request):
    print('enter zhuapai', request.method, request.POST)
    data = json.loads(request.body)
    file = 'record/' + myutils.get_unique_str() + '.jpg'
    _path = path.join(settings.MEDIA_ROOT, file)
    image_data = base64.b64decode(data['image'])
    with open(_path, 'wb') as f:
        f.write(image_data)
    record_time = datetime.now()
    print('begin face_search')
    result = face_search(_path, "blackList")
    print(result)
    face_token = result['face_token']
    blacklist = models.Blacklist.objects.get(face_token=face_token)
    if result['error_msg'] == 'SUCCESS':
        # 抓拍照片匹配成功
        models.Record(img=file,
                      photo=blacklist.photo,
                      tag=blacklist.tag,
                      face_id=blacklist.face_id,
                      score=result['score'],
                      equipment='抓拍机1号',
                      record_time=record_time).save()
        print('已保存1条抓拍！')
    return HttpResponse('OK')
