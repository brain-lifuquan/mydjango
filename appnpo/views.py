import json
from copy import copy
from django.shortcuts import render
from django.db import models
from app.views import MyView
from app.utils import mymap, myfuncs
from django.db.models import Count
from .models import WorkSpace, WorkSpaceEditForm, WorkSpaceForm
from .models import Cell, CellForm
from .models import Site, SiteForm
from .models import Scene, SceneForm
from .models import get_type_display


def index(request):
    return render(request, 'appnpo/index.html')


class WorkSpaceListView(MyView):
    def get(self, request):
        workspaces = WorkSpace.objects.all()
        context = {
            'workspaces': workspaces,
        }
        return render(request, 'appnpo/workspace_list.html', context=context)

    def get_form(self, request):
        result = {
            'errmsg': [],
        }
        workspace_name = request.POST.get('workspace_name')
        if workspace_name:
            workspace = WorkSpace.objects.get(workspace_name=workspace_name)
            workspace_form = WorkSpaceEditForm(instance=workspace)
            result['form'] = workspace_form.as_form(),
        else:
            result['form'] = WorkSpaceForm().as_form()
        return result

    def new_object(self, request):
        result = {
            'errmsg': [],
        }
        form = WorkSpaceForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            for key, value in form.errors.items():
                result['errmsg'].append('{}:{}'.format(key, value))
        return result

    def delete_object(self, request):
        result = {
            'errmsg': [],
        }
        workspace_name = request.POST.get('workspace_name')
        workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        workspace.delete()
        return result

    def edit_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        # 在request.POST中, data数据是修改前的原数据
        # data = request.POST.get('data')
        # 修改前数据
        workspace_name = request.POST.get('old_workspace_name')
        workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        # form是修改后实例对应的form
        form = WorkSpaceForm(instance=workspace, data=request.POST)
        # has_changed() 判断是否发生了修改
        if form.has_changed():
            if 'workspace_type' in form.changed_data:
                result['errmsg'].append('无法修改工作空间类型，可以创建一个新的工作空间')
            elif form.is_valid():
                form.save()
            else:
                for key, value in form.errors.items():
                    result['errmsg'].append('{}:{}'.format(key, value))
        else:
            result['errmsg'].append('未作修改')
        return result


class WorkSpaceView(MyView):

    def get(self, request, **kwargs):
        workspace = WorkSpace.objects.get(**kwargs)

        scenes = workspace.scene_set.all()
        sites = workspace.site_set.all()
        cells = workspace.cell_set.all()

        scenes_count = scenes.count()

        sites_count = sites.count()
        indoor_sites_count = sites.filter(site_type='室分').count()
        outdoor_sites_count = sites.filter(site_type='宏站').count()
        type_unknown_sites_count = sites_count - indoor_sites_count - outdoor_sites_count

        need_recheck = False
        if not workspace.time_lastcheck:
            need_recheck = True
        elif workspace.time_lastcheck.strftime('%Y-%m-%d %H:%M:%S') != workspace.time_lastmodify.strftime('%Y-%m-%d %H:%M:%S'):
            need_recheck = True

        context = {
            'workspace': workspace,
            'scenes_count': scenes_count,
            'sites_count': sites_count,
            'indoor_sites_count': indoor_sites_count,
            'outdoor_sites_count': outdoor_sites_count,
            'type_unknown_sites_count': type_unknown_sites_count,
            'cells_count': cells.count(),
            'need_recheck': need_recheck,
        }
        return render(request, 'appnpo/workspace.html', context=context)

    def get_data_for_charts(self, request, workspace_name):
        result = {
            'errmsg': [],
            'data': {
                'scene_chart': [],
                'site_chart': [],
                'cell_chart': [],
                'site_nearby_chart': [],
            },
        }
        workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        # scenne_chart
        scenes = workspace.scene_set.all()
        type_grouped_scenes = scenes.values('scene_type').annotate(count=Count('scene_type'))
        for group in type_grouped_scenes:
            result['data']['scene_chart'].append({
                'name': group['scene_type'],
                'value': group['count'],
            })
        # site_chart
        sites = workspace.site_set.all()
        # 按照'site_type', 'is_auto_created' 进行分组计数
        type_grouped_sites = sites.values('site_type', 'is_auto_created')
        type_grouped_sites = type_grouped_sites.annotate(Count('site_type'), count=Count('is_auto_created'))
        for group in type_grouped_sites:
            _name = get_type_display(group['site_type'])
            if group['is_auto_created']:
                _name += '_auto'
            result['data']['site_chart'].append({
                'name': _name,
                'value': group['count'],
            })
        # cell_chart
        cells = workspace.cell_set.all()
        type_grouped_cells = cells.values('cell_type').annotate(count=Count('cell_type'))
        for group in type_grouped_cells:
            result['data']['cell_chart'].append({
                'name': get_type_display(group['cell_type']),
                'value': group['count'],
            })
        # 结果
        outdoor_sites_nearby = [_scene.outdoorsitenearbyscene_set.count() for _scene in scenes]
        from collections import Counter
        _dict = Counter(sorted(outdoor_sites_nearby))
        result['data']['site_nearby_chart'] = [[], []]
        for key, value in _dict.items():
            result['data']['site_nearby_chart'][0].append(key)
            result['data']['site_nearby_chart'][1].append(value)
            # result['data']['site_nearby_chart'].append({
            #     'name': key,
            #     'value': value,
            # })
        # print(result['data']['site_nearby_chart'])
        # indoor_sites = workspace.indoorsiteinscene_set.all()
        return result

    def check(self, request, workspace_name):
        result = {
            'errmsg': [],
        }
        from . import outdoorsitenearbyscene
        from . import indoorsiteinscene
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        _workspace.outdoorsitenearbyscene_set.all().delete()
        _workspace.indoorsiteinscene_set.all().delete()
        scenes = _workspace.scene_set.all()
        if not scenes:
            result['errmsg'].append('请先创建场景数据！')
        sites = _workspace.site_set.all()
        if not sites:
            result['errmsg'].append('请先创建站址数据!')
        if not result['errmsg']:
            outdoor_sites = sites.filter(site_type='outdoor')
            if outdoor_sites:
                _result_sites = outdoorsitenearbyscene.get_sites_nearby_scenes(
                    scenes=scenes,
                    queryset_sites=outdoor_sites
                )
                outdoorsitenearbyscene.OutdoorSiteNearbyScene.objects.bulk_create(_result_sites)
                sites_nearby_scene = outdoorsitenearbyscene.OutdoorSiteNearbyScene.objects.all()
                _result_cells = outdoorsitenearbyscene.get_cells_cover_scenes(
                    scenes=scenes,
                    queryset_sites_nearby_scene=sites_nearby_scene,
                )
                outdoorsitenearbyscene.OutdoorCellCoverScene.objects.bulk_create(_result_cells)
            indoor_sites = sites.filter(site_type='indoor')
            if indoor_sites:
                indoor_sites_in_scenes = indoorsiteinscene.get_indoor_sites_in_scenes(
                    scenes=scenes,
                    queryset_sites=indoor_sites
                )
                indoorsiteinscene.IndoorSiteInScene.objects.bulk_create(indoor_sites_in_scenes)
            from datetime import datetime
            _workspace.time_lastcheck = datetime.now()
            _workspace.save()
        return result

    def export(self, request, workspace_name):
        result = {
            'errmsg': [],
            'data': [],
        }
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        scenes = _workspace.scene_set.all()
        for _scene in scenes:
            indoor_sites = _scene.indoorsiteinscene_set.all()
            for obj in indoor_sites:
                cells = obj.site.cell_set.all()
                for _cell in cells:
                    result['data'].append({
                        '场景编号': _scene.scene_id,
                        '场景名称': _scene.scene_name,
                        '场景类型': _scene.scene_type,
                        '小区类型': '室分',
                        '小区号': _cell.cell_id,
                        '小区名': _cell.cell_name,
                    })
            outdoor_sites = _scene.outdoorsitenearbyscene_set.all()
            for obj in outdoor_sites:
                if obj.in_scene:
                    cells = obj.site.cell_set.all()
                    for _cell in cells:
                        result['data'].append({
                            '场景编号': _scene.scene_id,
                            '场景名称': _scene.scene_name,
                            '场景类型': _scene.scene_type,
                            '小区类型': '宏站',
                            '小区号': _cell.cell_id,
                            '小区名': _cell.cell_name,
                        })
                elif obj.cover_order:
                    cells = obj.outdoorcellcoverscene_set.all()
                    for _cell in cells:
                        result['data'].append({
                            '场景编号': _scene.scene_id,
                            '场景名称': _scene.scene_name,
                            '场景类型': _scene.scene_type,
                            '小区类型': '宏站',
                            '小区号': _cell.cell.cell_id,
                            '小区名': _cell.cell.cell_name,
                        })
        return result


class CellListView(MyView):

    def get(self, request, **kwargs):
        _workspace = WorkSpace.objects.get(**kwargs)
        context = {
            'class_type': '小区',
            'name_field': 'cell_name',
            'workspace': _workspace,
        }
        return render(request, 'appnpo/cell_list.html', context=context)

    def query(self, request, **kwargs):
        result = {
            'errmsg': [],
            'data': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        queryset = Cell.objects.filter(workspace=_workspace)
        for obj in queryset:
            result['data'].append(
                obj.to_query()
            )
        return result

    def get_form(self, request, **kwargs):
        # 获取表单
        result = {
            'errmsg': [],
        }
        # data 存在与否标志着是新建实例还是修改现有实例
        data = request.POST.get('data')
        if data:
            # 获取实例并通过实例初始化form数据
            data = json.loads(data)
            unique_cols = Cell.get_unique_fields()
            obj_dict = {key: value for key, value in data.items() if key in unique_cols}
            _workspace = WorkSpace.objects.get(**kwargs)
            obj_dict['workspace'] = _workspace
            cell = Cell.objects.get(**obj_dict)
            inital_data = cell.to_dict()
            form = CellForm(initial=inital_data)
            # 将经纬度设置为只读，不可修改的状态
            form.fields['lng'].widget.attrs['readonly'] = True
            form.fields['lat'].widget.attrs['readonly'] = True
            result['form'] = form.as_form()
        else:
            # 空白表单
            result['form'] = CellForm(initial=kwargs).as_form()
        return result

    def new_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        form = CellForm(request.POST)
        if form.is_valid():
            # 格式化经纬度
            _point = mymap.Point(form.cleaned_data['lng'], form.cleaned_data['lat'])
            _workspace = WorkSpace.objects.get(**kwargs)
            _site = None
            try:
                _site = Site.objects.get(workspace=_workspace, lng=_point.lng, lat=_point.lat)
            except Site.DoesNotExist:
                site_name = get_site_name(form.cleaned_data['cell_name'])
                _site = Site(
                    workspace=_workspace,
                    site_name=site_name,
                    site_type=form.cleaned_data['cell_type'],
                    lng=_point.lng,
                    lat=_point.lat,
                    is_auto_created=True,
                )
                _site.save()
                _workspace.save()
            finally:
                cell = form.save(commit=False)
                cell.workspace = _workspace
                cell.site = _site
                cell.save()
                _workspace.save()
        else:
            for key, value in form.errors.items():
                result['errmsg'].append('{}:{}'.format(key, value))
        return result

    def edit_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        # 在request.POST中, data数据是修改前的原数据
        data = request.POST.get('data')
        # data 是json格式数据
        data = json.loads(data)
        unique_cols = Cell.get_unique_fields()
        obj_dict = {key: value for key, value in data.items() if key in unique_cols}
        _workspace = WorkSpace.objects.get(**kwargs)
        obj_dict['workspace'] = _workspace
        # 数据库数据
        _cell = Cell.objects.get(**obj_dict)
        inital_data = _cell.to_dict()
        # 格式化新数据
        record = copy(request.POST)
        # 修改为可编辑状态
        record._mutable = True
        # 格式化数据
        lng = request.POST.get('lng')
        lat = request.POST.get('lat')
        _point = mymap.Point(lng, lat)
        record['lng'] = _point.lng
        record['lat'] = _point.lat
        form = CellForm(instance=_cell, initial=inital_data, data=record)
        if form.has_changed():
            if form.is_valid():
                form.save()
                _workspace.save()
            else:
                for key, value in form.errors.items():
                    result['errmsg'].append('{}:{}'.format(key, value))
        else:
            result['errmsg'].append('未作修改')
        return result

    def delete_object(self, request, **kwargs):
        # 删除 单项或多项数据
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        # data 储存了网页显示的一行或多行数据的全部字段 json格式
        data = request.POST.get('data')
        data = json.loads(data)
        # count存储删除的数量
        count = 0
        # 根据unique_fields 进行查找
        unique_cols = Cell.get_unique_fields()
        # 遍历每一行要删除的数据
        for obj_dict in data:
            # 查找条件
            obj_dict = {key: value for key, value in obj_dict.items() if key in unique_cols}
            # workspace限制
            obj_dict['workspace'] = _workspace
            # 查找数据并删除
            obj = Cell.objects.get(**obj_dict)
            obj.delete()
            count += 1
        result['count'] = count
        _workspace.save()
        return result

    def clear(self, request, **kwargs):
        # 清空
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        objects = Cell.objects.filter(workspace=_workspace)
        result['count'] = objects.delete()
        _workspace.save()
        return result

    def get_template(self, request, **kwargs):
        # 下载模板
        return {
            'errmsg': [],
            'fields': Cell.get_upload_fields(),
        }

    def upload(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        # 获取文件并读取内容
        file = request.FILES.get('file')
        df = myfuncs.read_csv(file)
        # 检查文件头信息  missing_cols 存储缺少的列
        missing_cols = []
        fields = Cell.get_upload_fields()
        cols = {field['verbose_name']: field['name'] for field in fields}
        for col in cols.keys():
            if col not in df.columns:
                missing_cols.append(col)
        if missing_cols:
            result['errmsg'].append('导入文件缺少 "{}" 列'.format('、'.join(missing_cols)))
        else:
            # 检查完毕, 表头正常  只需要模板列, 并将列头重命名为内部名
            df = df[cols.keys()]
            df = df.rename(columns=cols)
            # 存储cell
            cells = []
            # df.to_dict(orient='records') 将DataFrame转化成字典的列表
            for _index, record in enumerate(df.to_dict(orient='records'), start=1):
                cell_form = CellForm(data=record)
                if cell_form.is_valid():
                    # 格式化经纬度
                    point = mymap.Point(record['lng'], record['lat'])
                    _site = None
                    try:
                        # 查找已存在的站址数据
                        _site = Site.objects.get(workspace=_workspace, lng=point.lng, lat=point.lat)
                    except Site.DoesNotExist:
                        # 如果不存在则需要新建
                        site_name = get_site_name(record['cell_name'])
                        _site = Site(
                            workspace=_workspace,
                            site_type=cell_form.cleaned_data['cell_type'],
                            site_name=site_name,
                            lng=point.lng,
                            lat=point.lat,
                            is_auto_created=True,
                        )
                        _site.save()
                    finally:
                        cell = cell_form.save(commit=False)
                        cell.workspace = _workspace
                        cell.site = _site
                        cells.append(cell)
                else:
                    for key, value in cell_form.errors.items():
                        result['errmsg'].append('{}:{}'.format(key, value))
            if not result['errmsg']:
                # 只有完全不窜在errmsg, 才进行批量的存储到数据库的操作 bulk_create()
                from django.db.utils import IntegrityError
                try:
                    Cell.objects.bulk_create(cells)
                    _workspace.save()
                except IntegrityError as e:
                    # 存在冲突数据
                    result['errmsg'].append(str(e))
        return result


def get_site_name(cell_name):
    import re
    # 从cell_name 转化成site_name
    # 匹配开始位置的字母/数字/_-
    remove_chars_head = '^[A-Za-z0-9_-]+'
    # 匹配结束位置的字母/数字/_-
    remove_chars_end = '[A-Za-z0-9_-]+$'
    # re.sub(pattern, repl, string, count=0, flags=0) pattern: 正则中的模式字符串。repl: 替换的字符串，也可为一个函数。
    # string: 要被查找替换的原始字符串。count: 模式匹配后替换的最大次数，默认0 表示替换所有的匹配
    site_name = re.sub(remove_chars_head, '', cell_name)
    site_name = re.sub(remove_chars_end, '', site_name)
    site_name += '_auto'
    return site_name


class SiteListView(MyView):

    def get(self, request, **kwargs):
        _workspace = WorkSpace.objects.get(**kwargs)
        context = {
            'class_type': '站址',
            'name_field': 'site_name',
            'workspace': _workspace,
        }
        return render(request, 'appnpo/site_list.html', context=context)

    def query(self, request, **kwargs):
        result = {
            'errmsg': [],
            'data': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        queryset = Site.objects.filter(workspace=_workspace)
        for obj in queryset:
            result['data'].append(
                obj.to_query()
            )
        return result

    def get_form(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        # data 存在与否标志着是新建实例还是修改现有实例
        data = request.POST.get('data')
        if data:
            # 获取实例并通过实例初始化form数据
            data = json.loads(data)
            unique_cols = Site.get_unique_fields()
            obj_dict = {key: value for key, value in data.items() if key in unique_cols}
            _workspace = WorkSpace.objects.get(**kwargs)
            obj_dict['workspace'] = _workspace
            obj = Site.objects.get(**obj_dict)
            result['form'] = SiteForm(instance=obj).as_form(),
        else:
            result['form'] = SiteForm(initial=kwargs).as_form()
        return result

    def new_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        form = SiteForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            # 格式化经纬度精度
            _point = mymap.Point(obj.lng, obj.lat)
            obj.lng = _point.lng
            obj.lat = _point.lat
            _workspace = WorkSpace.objects.get(**kwargs)
            obj.workspace = _workspace
            obj.save()
            _workspace.save()
        else:
            for key, value in form.errors.items():
                result['errmsg'].append('{}:{}'.format(key, value))
        return result

    def delete_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        # data 储存了网页显示的一行或多行数据的全部字段 json格式
        data = request.POST.get('data')
        data = json.loads(data)
        # count存储删除的数量
        count = 0
        # 根据unique_fields 进行查找
        unique_cols = Site.get_unique_fields()
        # 遍历每一行要删除的数据
        for obj_dict in data:
            # 查找条件
            obj_dict = {key: value for key, value in obj_dict.items() if key in unique_cols}
            # workspace限制
            obj_dict['workspace'] = _workspace
            # 查找数据并删除
            obj = Site.objects.get(**obj_dict)
            obj.delete()
            count += 1
            _workspace.save()
        result['count'] = count
        return result

    def clear(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        objects = Site.objects.filter(workspace=_workspace)
        result['count'] = objects.delete()
        _workspace.save()
        return result

    def edit_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        # 在request.POST中, data数据是修改前的原数据
        data = request.POST.get('data')
        # data 是json格式数据
        data = json.loads(data)
        unique_cols = Site.get_unique_fields()
        obj_dict = {key: value for key, value in data.items() if key in unique_cols}
        _workspace = WorkSpace.objects.get(**kwargs)
        obj_dict['workspace'] = _workspace
        obj = Site.objects.get(**obj_dict)
        record = copy(request.POST)
        # 修改为可编辑状态
        record._mutable = True
        # 格式化数据
        lng = request.POST.get('lng')
        lat = request.POST.get('lat')
        _point = mymap.Point(lng, lat)
        record['lng'] = _point.lng
        record['lat'] = _point.lat
        form = SiteForm(instance=obj, data=record)
        if form.has_changed():
            if form.is_valid():
                form.save()
                _workspace.save()
            else:
                for key, value in form.errors.items():
                    result['errmsg'].append('{}:{}'.format(key, value))
        else:
            result['errmsg'].append('未作修改')
        return result

    def get_template(self, request, **kwargs):
        return {
            'errmsg': [],
            'fields': Site.get_upload_fields(),
        }

    def upload(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        # 获取文件并读取内容
        file = request.FILES.get('file')
        df = myfuncs.read_csv(file)
        # 检查文件头信息  missing_cols 存储缺少的列
        missing_cols = []
        fields = Site.get_upload_fields()
        cols = {field['verbose_name']: field['name'] for field in fields}
        for col in cols.keys():
            if col not in df.columns:
                missing_cols.append(col)
        if missing_cols:
            result['errmsg'].append('导入文件缺少 "{}" 列'.format('、'.join(missing_cols)))
        else:
            # 检查完毕, 表头正常  只需要模板列, 并将列头重命名为内部名
            df = df[cols.keys()]
            df = df.rename(columns=cols)
            # object_list 保存验证正常的 实例
            object_list = []
            # df.to_dict(orient='records') 将DataFrame转化成字典的列表
            for _index, record in enumerate(df.to_dict(orient='records'), start=1):
                # 格式化 record lng 和 lat
                try:
                    _point = mymap.Point(record['lng'], record['lat'])
                except ValueError as e:
                    result['errmsg'].append(str(e))
                else:
                    record['lng'] = _point.lng
                    record['lat'] = _point.lat
                    # 需要对site_type数据进行处理
                    form = SiteForm(data=record)
                    if form.is_valid():
                        # form.save(commit=False) 保存为Scene对象 但是不存储到数据库
                        obj = form.save(commit=False)
                        obj.workspace = _workspace
                        object_list.append(obj)
                    else:
                        for key in form.errors.keys():
                            # 存在错误的情况, 将错误加入到errmsg
                            result['errmsg'].append('文件第{}行存在错误: {}:{}'.format(_index, key, form.errors[key]))
            if not result['errmsg']:
                # 只有完全不存在errmsg, 才进行批量的存储到数据库的操作
                # 获取当前最大的id值
                sites_exist = Site.objects.all()
                maxid_exist = sites_exist.aggregate(models.Max('id'))['id__max']
                maxid_exist = maxid_exist if maxid_exist else 0
                # 给新增的scene添加id
                id_new = maxid_exist + 1
                siteid_list = []
                for site in object_list:
                    site.id = id_new
                    siteid_list.append(site.id)
                    id_new += 1
                from django.db.utils import IntegrityError
                try:
                    Site.objects.bulk_create(object_list)
                    _workspace.save()
                except IntegrityError:
                    # 存在重合站址
                    not_unique = []
                    # 对object_list 按照lng和lat进行排序
                    sorted_sites = sorted(object_list, key=lambda x: (x.lng, x.lat), reverse=False)
                    # 存储对比的临时数据
                    _lng = 0
                    _lat = 0
                    _obj_1 = None
                    for _obj in sorted_sites:
                        if _obj.lng == _lng and _obj.lat == _lat:
                            not_unique.append((_obj_1, _obj))
                        else:
                            _lng = _obj.lng
                            _lat = _obj.lat
                            _obj_1 = _obj
                    if not_unique:
                        result['errmsg'].append('存在{}对重合站址'.format(len(not_unique)))
                        for _item in not_unique:
                            result['errmsg'].append('{},{},{}和{},{},{}为重合站址'
                                                    .format(_item[0].site_name, _item[0].lng, _item[0].lat,
                                                            _item[1].site_name, _item[1].lng, _item[1].lat))
        return result


class SceneListView(MyView):

    def get(self, request, **kwargs):
        _workspace = WorkSpace.objects.get(**kwargs)
        context = {
            # 必须要有 class_type
            'class_type': '场景',
            'name_field': 'scene_name',
            'workspace': _workspace,
        }
        return render(request, 'appnpo/scene_list.html', context=context)

    def query(self, request, **kwargs):
        result = {
            'errmsg': [],
            'data': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        scenes = Scene.objects.filter(workspace=_workspace)
        for scene in scenes:
            result['data'].append(
                scene.to_query()
            )
        return result

    def get_form(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        # data 存在与否标志着是新建实例还是修改现有实例
        data = request.POST.get('data')
        if data:
            # 获取实例并通过实例初始化form数据
            data = json.loads(data)
            unique_cols = Scene.get_unique_fields()
            obj_dict = {key: value for key, value in data.items() if key in unique_cols}
            _workspace = WorkSpace.objects.get(**kwargs)
            obj_dict['workspace'] = _workspace
            obj = Scene.objects.get(**obj_dict)
            result['form'] = SceneForm(instance=obj).as_form(),
        else:
            # 新增情况，不需要初始化
            result['form'] = SceneForm().as_form()
        return result

    def new_object(self, request, **kwargs):
        # {[114.553593,38.106179];[114.554685,38.10751];[114.560549,38.105811];[114.560239,38.104365];[114.553593,38.106179];[114.553593,38.106179]}
        result = {
            'errmsg': [],
        }
        # 不要在request.POST上直接编辑  先copy一份
        record = copy(request.POST)
        # 修改为可编辑状态
        record._mutable = True
        # 将region字符串 转化成Region对象
        region = mymap.Region(fmt_str=record['region'])
        # 储存的是格式化后的json字符串
        record['region'] = region.to_json()
        form = SceneForm(record)
        if form.is_valid():
            obj = form.save(commit=False)
            _workspace = WorkSpace.objects.get(**kwargs)
            obj.workspace = _workspace
            obj.save()
            _workspace.save()
        else:
            for key, value in form.errors.items():
                result['errmsg'].append('{}:{}'.format(key, value))
        return result

    def edit_object(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        # 在request.POST中, data数据是修改前的原数据
        data = request.POST.get('data')
        # data 是json格式数据
        data = json.loads(data)
        unique_cols = Scene.get_unique_fields()
        obj_dict = {key: value for key, value in data.items() if key in unique_cols}
        _workspace = WorkSpace.objects.get(**kwargs)
        obj_dict['workspace'] = _workspace
        obj = Scene.objects.get(**obj_dict)
        record = copy(request.POST)
        # 修改为可编辑状态
        record._mutable = True
        # 将region字符串 转化成Region对象
        region = mymap.Region(fmt_str=record['region'])
        # 储存的是格式化后的json字符串
        record['region'] = region.to_json()
        # 更新kwargs
        record['workspace'] = _workspace
        # scene_dict['region'] = mymapinfo.to_region(scene_dict['region'])
        form = SceneForm(instance=obj, data=record)
        # 判断是否有修改, 如果有修改 可以 获取 form.changed_data
        if form.has_changed():
            if form.is_valid():
                obj = form.save(commit=False)
                obj.workspace = _workspace
                obj.save()
                _workspace.save()
            else:
                for key, value in form.errors.items():
                    result['errmsg'].append('{}:{}'.format(key, value))
        else:
            result['errmsg'].append('未作修改')
        return result

    def get_template(self, request, **kwargs):
        return {
            'errmsg': [],
            'fields': Scene.get_upload_fields(),
        }

    def upload(self, request, **kwargs):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(**kwargs)
        # 获取文件并读取内容
        file = request.FILES.get('file')
        df = myfuncs.read_csv(file)
        # 检查文件头信息  missing_cols 存储缺少的列
        missing_cols = []
        fields = Scene.get_upload_fields()
        cols = {field['verbose_name']: field['name'] for field in fields}
        for col in cols.keys():
            if col not in df.columns:
                missing_cols.append(col)
        if missing_cols:
            result['errmsg'].append('导入文件缺少 "{}" 列'.format('、'.join(missing_cols)))
        else:
            # 检查完毕, 表头正常  只需要模板列, 并将列头重命名为内部名
            df = df[cols.keys()]
            df = df.rename(columns=cols)
            # object_list 保存验证正常的 实例
            object_list = []
            # df.to_dict(orient='records') 将DataFrame转化成字典的列表
            for _index, record in enumerate(df.to_dict(orient='records'), start=1):
                # 将region字符串 转化成Region对象
                region = mymap.Region(fmt_str=record['region'])
                # 储存的是格式化后的json字符串
                record['region'] = region.to_json()
                form = SceneForm(data=record)
                if form.is_valid():
                    # form.save(commit=False) 保存为Scene对象 但是不存储到数据库
                    obj = form.save(commit=False)
                    obj.workspace = _workspace
                    object_list.append(obj)
                else:
                    for key in form.errors.keys():
                        # 存在错误的情况, 将错误加入到errmsg
                        result['errmsg'].append('文件第{}行存在错误: {}:{}'.format(_index, key, form.errors[key]))
            if not result['errmsg']:
                # 只有完全不存在errmsg, 才进行批量的存储到数据库的操作
                # 获取当前最大的id值
                scenes_exist = Scene.objects.all()
                maxid_exist = scenes_exist.aggregate(models.Max('id'))['id__max']
                maxid_exist = maxid_exist if maxid_exist else 1
                # 给新增的scene添加id
                id_new = maxid_exist + 1
                sceneid_list = []
                for scene in object_list:
                    scene.id = id_new
                    sceneid_list.append(scene.id)
                    id_new += 1
                Scene.objects.bulk_create(object_list)
                _workspace.save()
                # scene_models.check_scenes.delay(sceneid_list)
        return result

    def clear(self, request, workspace_name):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        objects = Scene.objects.filter(workspace=_workspace)
        result['count'] = objects.delete()
        _workspace.save()
        return result

    def delete_object(self, request, workspace_name):
        result = {
            'errmsg': [],
        }
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        # data 储存了网页显示的一行或多行数据的全部字段 json格式
        data = request.POST.get('data')
        data = json.loads(data)
        # count存储删除的数量
        count = 0
        # 根据unique_fields 进行查找
        unique_cols = Scene.get_unique_fields()
        # 遍历每一行要删除的数据
        for obj_dict in data:
            # 查找条件
            obj_dict = {key: value for key, value in obj_dict.items() if key in unique_cols}
            obj_dict['workspace'] = _workspace
            # 查找数据并删除
            obj = Scene.objects.get(**obj_dict)
            obj.delete()
            count += 1
        result['count'] = count
        _workspace.save()
        return result


class SceneView(MyView):

    def get(self, request, workspace_name, scene_name):
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        _scene = Scene.objects.get(workspace=_workspace, scene_name=scene_name)
        indoor_sites = _scene.indoorsiteinscene_set.all()
        indoor_sites_count = indoor_sites.count()
        indoor_cells_count = 0
        for obj in indoor_sites:
            indoor_cells_count += obj.site.cell_set.all().count()
        outdoor_sites = _scene.outdoorsitenearbyscene_set.all()
        outdoor_sites_count = outdoor_sites.count()
        cover_cells_count = 0
        for obj in outdoor_sites:
            cover_cells_count += obj.outdoorcellcoverscene_set.all().count()
        context = {
            'workspace': _workspace,
            'scene': _scene,
            'indoor_sites_count': indoor_sites_count,
            'indoor_cells_count': indoor_cells_count,
            'outdoor_sites_count': outdoor_sites_count,
            'cover_cells_count': cover_cells_count,
        }
        return render(request, 'appnpo/scene.html', context=context)

    def get_map_data(self, request, workspace_name, scene_name):
        result = {
            'errmsg': [],
            'data': {},
        }
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        _scene = Scene.objects.get(workspace=_workspace, scene_name=scene_name)
        _region = mymap.Region(_scene.region)
        result['data']['region'] = _scene.region
        result['data']['center'] = _region.get_center().to_json()
        outdoor_sites_nearby = _scene.outdoorsitenearbyscene_set.all()
        json_outdoor_sites_nearby = []
        json_outdoor_cells_nearby = []
        for obj in outdoor_sites_nearby:
            json_outdoor_sites_nearby.append({
                'lng': obj.site.lng,
                'lat': obj.site.lat,
                'site_name': obj.site.site_name,
            })
            cells = obj.site.cell_set.all()
            cover_cells = obj.outdoorcellcoverscene_set.all()
            cover_cells = [i.cell for i in cover_cells]
            for cell in cells:
                is_cover = False
                if cell in cover_cells:
                    is_cover = True
                json_outdoor_cells_nearby.append({
                    'lng': obj.site.lng,
                    'lat': obj.site.lat,
                    'azimuth': cell.azimuth,
                    'is_cover': is_cover,
                })
        result['data']['sites_nearby'] = json_outdoor_sites_nearby
        result['data']['cells_nearby'] = json_outdoor_cells_nearby
        return result


class SceneMapView(MyView):

    def get(self, request, workspace_name, scene_name):
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        _scene = Scene.objects.get(workspace=_workspace, scene_name=scene_name)
        indoor_sites_count = _scene.indoorsiteinscene_set.all().count()
        indoor_cells_count = 0
        for obj in indoor_sites_count:
            indoor_cells_count += obj.site.cell_set.all().count()
        outdoor_sites_count = _scene.outdoorsitenearbyscene_set.all().count()
        cover_cells_count = 0
        for obj in outdoor_sites_count:
            cover_cells_count += obj.outdoorcellcoverscene_set.all().count()
        context = {
            'workspace': _workspace,
            'scene': _scene,
            'indoor_sites_count': indoor_sites_count,
            'indoor_cells_count': indoor_cells_count,
            'outdoor_sites_count': outdoor_sites_count,
            'cover_cells_count': cover_cells_count,
        }
        return render(request, 'appnpo/scene_map.html', context=context)

    def get_map_data(self, request, workspace_name, scene_name):
        result = {
            'errmsg': [],
            'data': {},
        }
        _workspace = WorkSpace.objects.get(workspace_name=workspace_name)
        _scene = Scene.objects.get(workspace=_workspace, scene_name=scene_name)
        _region = mymap.Region(_scene.region)
        result['data']['region'] = _scene.region
        result['data']['center'] = _region.get_center().to_json()
        outdoor_sites_nearby = _scene.outdoorsitenearbyscene_set.all()
        json_outdoor_sites_nearby = []
        json_outdoor_cells_nearby = []
        for obj in outdoor_sites_nearby:
            json_outdoor_sites_nearby.append({
                'lng': obj.site.lng,
                'lat': obj.site.lat,
                'site_name': obj.site.site_name,
            })
            cells = obj.site.cell_set.all()
            cover_cells = obj.outdoorcellcoverscene_set.all()
            cover_cells = [i.cell for i in cover_cells]
            for cell in cells:
                is_cover = False
                if cell in cover_cells:
                    is_cover = True
                json_outdoor_cells_nearby.append({
                    'lng': obj.site.lng,
                    'lat': obj.site.lat,
                    'azimuth': cell.azimuth,
                    'is_cover': is_cover,
                })
        result['data']['sites_nearby'] = json_outdoor_sites_nearby
        result['data']['cells_nearby'] = json_outdoor_cells_nearby
        return result
