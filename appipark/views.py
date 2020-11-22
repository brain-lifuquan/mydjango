import os
import json

from django.shortcuts import render
from django.db.utils import IntegrityError

from . import models
from . import forms
from .utils.mydjango import MyView
from .utils import myfunc
from .utils import myffmpeg


def index(request):
    return render(request, 'appipark/index.html')


class MaterialListView(MyView):

    def get(self, request, material_type):
        material_types = models.MaterialType.objects.all()
        mtype = material_types.get(name=material_type)
        materials = models.Material.objects.filter(type=material_type)
        context = {
            # 当前的素材类型
            'material_type': material_type,
            # 输入类型限制
            'file_selector_accept': mtype.file_selector_accept,
            # 素材类型列表
            'material_types': material_types,
            # 当前类型的素材列表
            'materials': materials,
        }
        return render(request, 'appipark/material_list.html', context=context)

    def upload_files(self, request, material_type):
        result = {'errmsg': []}
        # 通过getilist方法可以直接获得列表
        list_files = request.FILES.getlist('files')
        list_materials = []
        for file in list_files:
            # 检查是否已存在同名文件
            query = models.Material.objects.filter(name=file.name)
            if query:
                result['errmsg'].append("{}--已存在同名文件".format(file.name))
            else:
                # 获取缩略图
                image = myfunc.get_thumbnail(file, material_type, (200, 150))
                # 生成material对象
                material = models.Material(name=file.name, type=material_type, file=file, thumbnail=image)
                list_materials.append(material)
        # 只有不存在任何err时 才进行保存
        if not result['errmsg']:
            for material in list_materials:
                material.save()
        return result

    def delete_material(self, request, material_type):
        result = {'errmsg': []}
        name = request.POST.get('name_to_delete')
        material = models.Material.objects.get(name=name)
        # 删除文件
        path = material.file.path
        os.remove(path)
        # 删除缩略图文件
        thumbnail = material.thumbnail.path
        os.remove(thumbnail)
        # 删除数据库记录
        material.delete()
        return result


# 素材预览页面
def view_material(request, material_name):
    context = {
        'material': models.Material.objects.get(name=material_name)
    }
    return render(request, 'appipark/material_view.html', context=context)


# 节目预览页面
def view_program(request, program_name):
    program = models.Program.objects.get(name=program_name)
    context = {
        'program': program.path
    }
    return render(request, 'appipark/program_view.html', context=context)


# 节目分辨率
class ScaleTypeView(MyView):

    def get_form_info(self, request):
        result = {
            'errmsg': [],
            'form': forms.ScaleTypeForm().as_ul()
        }
        return result

    def add_scale_type(self, request):
        result = {'errmsg': []}
        scale_type = forms.ScaleTypeForm(request.POST)
        if scale_type.is_valid():
            scale_type.save()
        else:
            for err in scale_type.errors:
                result['errmsg'].append(scale_type.errors[err])
        return result


class ProgramListView(MyView):

    def get(self, request):
        context = {
            'programs': models.Program.objects.all()
        }
        return render(request, 'appipark/program_list.html', context=context)

    def delete_program(self, request):
        result = {'errmsg': []}
        program_name = request.POST.get('program_name')
        program = models.Program.objects.get(name=program_name)
        # 删除硬盘文件
        os.remove(program.path)
        # 删除数据库记录
        program.delete()
        return result


# 新建节目view
class ProgramNewView(MyView):

    def get(self, request, program_name, scale_type):
        # 节目初始名称
        context = {'program_name': program_name}
        # 获取分辨率 宽度和高度 单位是px像素
        scale_type = models.ScaleType.objects.get(id=scale_type)
        size = scale_type.name.split('*')
        context['scale_type'] = scale_type.name
        context['width'] = size[0]
        context['height'] = size[1]
        return render(request, 'appipark/program_new.html', context=context)

    def get_form_info(self, request, program_name, scale_type):
        result = {
            'errmsg': [],
            'form': forms.ProgramForm().as_ul()
        }
        return result

    def save_program(self, request, program_name, scale_type):
        result = {'errmsg': []}
        # 获取提交上来的节目信息
        program = request.POST.get('program')
        program = json.loads(program)
        # 分辨率
        scale = models.ScaleType.objects.get(id=scale_type)
        scale_size = scale.name.split('*')
        material_list = models.Material.objects.all()
        # 背景图片
        bg_image = None
        if program['bg_image']:
            bg_image = material_list.get(name=program['bg_image']['name'])
            # 格式化myffmpeg的输入
            myffmpeg_in = {
                'duration': program['duration'],
                'size': {'width': scale_size[0], 'height': scale_size[1]},
                'bg_image': bg_image.file.path,
                'bg_image_name': bg_image.name,
                'bg_image_url': bg_image.file.url,
                'groups': [],
            }
        else:
            myffmpeg_in = {
                'duration': program['duration'],
                'size': {'width': scale_size[0], 'height': scale_size[1]},
                'bg_image': None,
                'bg_image_name': None,
                'bg_image_url': None,
                'groups': [],
            }
        for group in program['groups']:
            grp = {
                'size': group['size'],
                'position': group['position'],
                'duration': {'start': group['duration']['start'], 'end': group['duration']['start'] + group['duration']['duration']},
                'inputs': [],
            }
            # material_start = 0
            # material_end = 0
            for material in group['materials']:
                mt = material_list.get(name=material['name'])
                # material_end = material_start + material['duration']
                inp = {
                    'name': mt.name,
                    'path': mt.file.path,
                    'url': mt.file.url,
                    'type': material['type'],
                    # start 是0 end是duration  此时未考虑从中间截取视频，视频都是从0s开始截取
                    'duration': {'start': 0, 'end': material['duration']}
                }
                grp['inputs'].append(inp)
                # material_start = material_end
            myffmpeg_in['groups'].append(grp)
        # 输出路径
        name = program['name']
        # 输出文件夹路径
        outpath = os.path.join('media', 'appipark', 'program')
        # 如果文件夹不存在 则创建文件夹
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        # 输出文件路径
        outpath = os.path.join(outpath, '{}.mp4'.format(name))
        try:
            ffmpeg_cmd = myffmpeg.run_myffmpeg(myffmpeg_in, outpath)
        except AttributeError:
            result['errmsg'].append('ffmpeg处理视频时执行错误。')
        else:
            models.Program(name=name, scale_type=scale, path=outpath, storage=myfunc.get_file_storage_size(outpath), duration=program['duration'], json_input=json.dumps(myffmpeg_in), ffmpegcmd=ffmpeg_cmd).save()
        return result


# 从服务器获取信息
class QueryView(MyView):

    def query_materials(self, request):
        result = {
            'errmsg': [],
            'materials': {},
        }
        # 获取要查询的类型
        material_types = request.POST.get('material_type')
        material_types = material_types.split('&&')
        # 全部类型
        types = models.MaterialType.objects.all()
        # 全部素材
        materials = models.Material.objects.all()
        # 分类型处理
        for type_name in material_types:
            material_type = types.get(name=type_name)
            materials_of_type = materials.filter(type=material_type)
            # 使用列表推导
            result['materials'][type_name] = [
                {
                    'name': material.name,
                    'url': material.file.url,
                    'type': material.type,
                 } for material in materials_of_type
            ]
        return result

    def query_programs(self, request):
        result = {
            'errmsg': [],
            'programs': [],
        }
        programs = models.Program.objects.all()
        for program in programs:
            result['programs'].append({
                'name': program.name,
                'url': program.path,
                'storage': program.storage,
            })
        return result


# 编辑节目
class ProgramEditView(MyView):

    def get(self, request, program_name):
        context = {'program_name': program_name}
        # 节目
        program = models.Program.objects.get(name=program_name)
        scale_type = program.scale_type
        size = scale_type.name.split('*')
        context['scale_type'] = scale_type.name
        context['width'] = size[0]
        context['height'] = size[1]
        context['duration'] = program.duration
        return render(request, 'appipark/program_edit.html', context=context)

    def get_program_json(self, request, program_name):
        result = {'errmsg': []}
        program = models.Program.objects.get(name=program_name)
        result['json'] = program.json_input
        return result

    def save_program(self, request, program_name):
        result = {'errmsg': []}
        # 获取提交上来的节目信息
        program = request.POST.get('program')
        program = json.loads(program)
        # 分辨率
        s_program = models.Program.objects.get(name=program_name)
        # 删除原文件
        if os.path.exists(s_program.path):
            os.remove(s_program.path)
        scale = s_program.scale_type
        scale_size = scale.name.split('*')
        material_list = models.Material.objects.all()
        # 背景图片
        bg_image = None
        if program['bg_image']:
            bg_image = material_list.get(name=program['bg_image']['name'])
        # 格式化myffmpeg的输入
        myffmpeg_in = {
            'duration': program['duration'],
            'size': {'width': scale_size[0], 'height': scale_size[1]},
            'bg_image': bg_image.file.path,
            'bg_image_name': bg_image.name,
            'bg_image_url': bg_image.file.url,
            'groups': [],
        }
        for group in program['groups']:
            grp = {
                'size': group['size'],
                'position': group['position'],
                'duration': {'start': group['duration']['start'], 'end': group['duration']['start'] + group['duration']['duration']},
                'inputs': [],
            }
            # material_start = 0
            # material_end = 0
            for material in group['materials']:
                mt = material_list.get(name=material['name'])
                # material_end = material_start + material['duration']
                inp = {
                    'name': mt.name,
                    'path': mt.file.path,
                    'url': mt.file.url,
                    'type': material['type'],
                    # start 是0 end是duration  此时未考虑从中间截取视频，视频都是从0s开始截取
                    'duration': {'start': 0, 'end': material['duration']}
                }
                grp['inputs'].append(inp)
                # material_start = material_end
            myffmpeg_in['groups'].append(grp)
        # 输出路径
        name = program['name']
        # 输出文件夹路径
        outpath = os.path.join('media', 'appipark', 'program')
        # 如果文件夹不存在 则创建文件夹
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        # 输出文件路径
        outpath = os.path.join(outpath, '{}.mp4'.format(name))
        try:
            ffmpeg_cmd = myffmpeg.run_myffmpeg(myffmpeg_in, outpath)
        except AttributeError:
            result['errmsg'].append('ffmpeg处理视频时执行错误。')
        else:
            # models.Program(name=name, scale_type=scale, path=outpath, duration=program['duration'], json_input=json.dumps(myffmpeg_in), ffmpegcmd=ffmpeg_cmd).save()
            s_program.path = outpath
            s_program.storage = myfunc.get_file_storage_size(outpath)
            s_program.name = name
            s_program.json_input = json.dumps(myffmpeg_in)
            s_program.ffmpegcmd = ffmpeg_cmd
            s_program.save()
        return result


class EquipmentListView(MyView):

    def get(self, request):
        context = {
            'equipments': models.Equipment.objects.all()
        }
        return render(request, 'appipark/equipment_list.html', context=context)

    def get_form_info(self, request):
        result = {'errmsg': []}
        equipment_name = request.POST.get('equipment_name')
        if equipment_name:
            equipment = models.Equipment.objects.get(name=equipment_name)
            result['form'] = forms.EquipmentForm(instance=equipment).as_ul()
        else:
            result['form'] = forms.EquipmentForm().as_ul()
        return result

    def add_equipment(self, request):
        result = {'errmsg': []}
        equipment = forms.EquipmentForm(request.POST)
        if equipment.is_valid():
            equipment.save()
        else:
            for err in equipment.errors:
                result['errmsg'].append(equipment.errors[err])
        return result

    def delete_equipment(self, request):
        result = {'errmsg': []}
        equipment_name = request.POST.get('equipment_name')
        equipment = models.Equipment.objects.get(name=equipment_name)
        equipment.delete()
        return result

    def edit_equipment(self, request):
        result = {'errmsg': []}
        equipment_name = request.POST.get('equipment_name')
        equipment = models.Equipment.objects.get(name=equipment_name)
        equipment_form = forms.EquipmentForm(request.POST, instance=equipment)
        if equipment_form.is_valid():
            equipment_form.save()
        else:
            for err in equipment_form.errors:
                result['errmsg'].append(equipment_form.errors[err])
        return result


# 终端上的节目列表
class EquipmentProgramListView(MyView):

    def get(self, request, equipment_name):
        # 设备实例
        equipment = models.Equipment.objects.get(name=equipment_name)
        equipment_programs = models.EquipmentProgram.objects.filter(equipment=equipment_name)
        # 全部节目
        programs_all = models.Program.objects.all()
        programs = []
        if equipment_programs:
            # 将节目名转化为节目实例
            for p in equipment_programs:
                program = programs_all.get(name=p.program)
                programs.append({
                    'index': p.index,
                    'name': program.name,
                    'scale_type': program.scale_type.name,
                    'duration': program.duration,
                    'storage': program.storage,
                })
        context = {
            'equipment': equipment,
            'programs': programs,
        }
        # print(context)
        return render(request, 'appipark/equipment_program_list.html', context=context)

    def send_program_to_equipment(self, request, equipment_name):
        result = {'errmsg': []}
        equipment = models.Equipment.objects.get(name=equipment_name)
        program_names = request.POST.getlist('program_name')
        programs_all = models.Program.objects.all()
        # programs = [programs_all.get(name=name) for name in program_names]
        # 此处将选中的文件推送到设备
        # 存储设备节目实例
        equipment_programs = []
        # 开始时的可用空间
        storage_free = equipment.storage_free
        for name in program_names:
            program = programs_all.get(name=name)
            storage_free -= program.storage
            if storage_free <= 0.0:
                result['errmsg'].append('存储空间不足！')
            else:
                equipment_program = models.EquipmentProgram(equipment=equipment_name, program=name)
                equipment_programs.append(equipment_program)
        # 在不发生错误的境况下才进行实际的存储操作
        if not result['errmsg']:
            for pro in equipment_programs:
                try:
                    pro.save()
                except IntegrityError as e:
                    result['errmsg'].append(repr(e))
            equipment.storage_free = storage_free
            equipment.save()
        return result

    def delete_program_from_equipment(self, request, equipment_name):
        result = {'errmsg': []}
        equipment = models.Equipment.objects.get(name=equipment_name)
        program_name = request.POST.get('program_name')
        equipment_program = models.EquipmentProgram.objects.get(equipment=equipment_name, program=program_name)
        program = models.Program.objects.get(name=program_name)
        storage_free = equipment.storage_free
        storage_free += program.storage
        if storage_free > equipment.storage_all:
            storage_free = equipment.storage_all
        equipment_program.delete()
        equipment.storage_free = storage_free
        equipment.save()
        return result

    def change_wheel_status(self, request, equipment_name):
        result = {'errmsg': []}
        equipment = models.Equipment.objects.get(name=equipment_name)
        equipment.wheel = not equipment.wheel
        equipment.save()
        return result

    def add_program_to_play_list(self, request, equipment_name):
        result = {'errmsg': []}
        # equipment = models.Equipment.objects.get(name=equipment_name)
        program_name = request.POST.get('program_name')
        # index__gte=0 大于等于0
        equipment_programs = models.EquipmentProgram.objects.filter(equipment=equipment_name)
        play_list = equipment_programs.filter(index__gte=0)
        index = len(play_list)
        equipment_program = equipment_programs.get(program=program_name)
        equipment_program.index = index
        equipment_program.save()
        return result

    def delete_program_from_play_list(self, request, equipment_name):
        result = {'errmsg': []}
        # equipment = models.Equipment.objects.get(name=equipment_name)
        program_name = request.POST.get('program_name')
        equipment_program = models.EquipmentProgram.objects.get(equipment=equipment_name, program=program_name)
        equipment_program.index = -1
        equipment_program.save()
        return result

    def set_play_time(self, request, equipment_name):
        result = {'errmsg': []}
        equipment = models.Equipment.objects.get(name=equipment_name)
        time_start = request.POST.get('time_start')
        time_end = request.POST.get('time_end')
        equipment.start_time = time_start
        equipment.end_time = time_end
        equipment.save()
        return result
