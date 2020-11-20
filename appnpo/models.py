from django import forms
from django.db import models
from app.models import MyModel, MyModelForm
from app.utils import mymap


class WorkSpace(MyModel):
    WORKSPACE_TYPE_CHOICES = [
        ('场景分析', '场景分析'),
    ]

    workspace_name = models.CharField(verbose_name='工作空间名称', max_length=40, unique=True)
    workspace_type = models.CharField(
        verbose_name='工作空间类型', max_length=20, choices=WORKSPACE_TYPE_CHOICES, default='场景分析')
    time_create = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    time_lastmodify = models.DateTimeField(verbose_name='最后操作时间', auto_now=True)
    time_lastcheck = models.DateTimeField(verbose_name='最后计算时间', null=True)
    status = models.CharField(verbose_name='状态', max_length=20)

    class Meta:
        verbose_name = '工作空间'


class WorkSpaceForm(MyModelForm):
    class Meta:
        model = WorkSpace
        fields = ['workspace_name', 'workspace_type']


class WorkSpaceEditForm(MyModelForm):
    class Meta:
        model = WorkSpace
        fields = ['workspace_name', 'workspace_type']
        # 设置workspace_type 为 readonly
        widgets = {'workspace_type': forms.TextInput(attrs={'readonly': True})}


TYPES = {
    'display': ['宏站', '室分', '未知'],
    'inner': ['outdoor', 'indoor', 'unknown'],
}


def get_type_display(_type):
    _index = TYPES['inner'].index(_type)
    _type = TYPES['display'][_index]
    return _type


class Cell(MyModel):
    workspace = models.ForeignKey('WorkSpace', on_delete=models.CASCADE)
    # cell所在站址
    site = models.ForeignKey('Site', on_delete=models.CASCADE)
    # 小区ID
    cell_id = models.CharField(verbose_name='小区号', max_length=20)
    cell_name = models.CharField(verbose_name='小区名', max_length=100)
    cell_type = models.CharField(verbose_name='小区类型', max_length=40)
    azimuth = models.IntegerField(verbose_name='方向角')

    exclude_fields = ['workspace', 'site']

    @classmethod
    def get_upload_fields(cls):
        result = super().get_upload_fields()
        result.append({
            'name': 'lng',
            'verbose_name': '经度',
        })
        result.append({
            'name': 'lat',
            'verbose_name': '纬度',
        })
        return result

    def to_query(self):
        return {
            'cell_id': self.cell_id,
            'cell_name': self.cell_name,
            'cell_type': get_type_display(self.cell_type),
            'azimuth': self.azimuth,
            'site_name': self.site.site_name,
            'lng': self.site.lng,
            'lat': self.site.lat,
        }

    def to_dict(self):
        return {
            'cell_id': self.cell_id,
            'cell_name': self.cell_name,
            'cell_type': self.cell_type,
            'azimuth': self.azimuth,
            'site_name': self.site.site_name,
            'lng': self.site.lng,
            'lat': self.site.lat,
        }

    class Meta:
        verbose_name = '小区信息'
        # 同一小区 有可能打几个方向
        unique_together = [
            ['workspace', 'cell_name', 'azimuth', 'site'],
            ['workspace', 'cell_id', 'azimuth', 'site'],
        ]


class CellForm(MyModelForm):
    from app.forms.fields import TypeChoiceField
    cell_type = TypeChoiceField(types=TYPES, label='小区类型')
    lng = forms.FloatField(label='经度')
    lat = forms.FloatField(label='纬度')

    class Meta:
        model = Cell
        exclude = Cell.exclude_fields


class Site(MyModel):
    workspace = models.ForeignKey('WorkSpace', on_delete=models.CASCADE)
    site_name = models.CharField(verbose_name='站址名称', max_length=100, null=False)
    site_type = models.CharField(verbose_name='站址类型', max_length=20, null=False)
    lng = models.FloatField(verbose_name='经度')
    lat = models.FloatField(verbose_name='纬度')
    is_auto_created = models.BooleanField(verbose_name='是否自动创建', default=False)

    exclude_fields = ['workspace', 'is_auto_created']

    def to_query(self):
        is_auto_created = '否'
        if self.is_auto_created:
            is_auto_created = '是'
        return {
            'site_name': self.site_name,
            'site_type': get_type_display(self.site_type),
            'lng': self.lng,
            'lat': self.lat,
            'is_auto_created': is_auto_created,
        }

    def __str__(self):
        return '{}:{}'.format(self.site_name, self.site_type)

    class Meta:
        verbose_name = '站址信息'
        unique_together = [['lng', 'lat', 'workspace']]


class SiteForm(MyModelForm):
    from app.forms.fields import TypeChoiceField
    site_type = TypeChoiceField(types=TYPES, label='站址类型')

    class Meta:
        model = Site
        exclude = Site.exclude_fields


class Scene(MyModel):
    workspace = models.ForeignKey('WorkSpace', on_delete=models.CASCADE)
    scene_id = models.CharField(verbose_name='场景编号', max_length=40, null=False)
    scene_name = models.CharField(verbose_name='场景名称', max_length=100, null=False)
    scene_type = models.CharField(verbose_name='场景类型', max_length=20, null=False)
    region = models.TextField(verbose_name='场景范围')

    exclude_fields = ['workspace']

    def to_query(self):
        center = mymap.Region(self.region).get_center()
        return {
            'scene_id': self.scene_id,
            'scene_name': self.scene_name,
            'region': self.region,
            'scene_type': self.scene_type,
            'center': {
                'lng': center.lng,
                'lat': center.lat,
            },
        }

    class Meta:
        verbose_name = '场景信息'
        unique_together = [['scene_id', 'workspace']]


class SceneForm(MyModelForm):
    class Meta:
        model = Scene
        exclude = Scene.exclude_fields


class IndoorSiteInScene(MyModel):
    workspace = models.ForeignKey('WorkSpace', on_delete=models.CASCADE)
    site = models.ForeignKey('Site', on_delete=models.CASCADE)
    scene = models.ForeignKey('Scene', on_delete=models.CASCADE)


def get_indoor_sites_in_scene(_scene, queryset_sites):
    result = []
    _workspace = _scene.workspace
    _region = mymap.Region(_scene.region)
    queryset_sites = queryset_sites.filter(site_type="indoor")
    for _site in queryset_sites:
        _point = mymap.Point(_site.lng, _site.lat)
        if _point.in_region(_region):
            result.append(IndoorSiteInScene(
                workspace=_workspace,
                site=_site,
                scene=_scene,
            ))
    return result


def get_indoor_sites_in_scenes(scenes, queryset_sites):
    result = []
    for _scene in scenes:
        result_for_scene = get_indoor_sites_in_scene(_scene, queryset_sites)
        if result_for_scene:
            result.extend(result_for_scene)
    return result


# SceneNearbySite 的条件限制
DISTANCE_NEAR = 3000


class OutdoorSiteNearbyScene(MyModel):
    workspace = models.ForeignKey('WorkSpace', on_delete=models.CASCADE)
    site = models.ForeignKey('Site', on_delete=models.CASCADE)
    scene = models.ForeignKey('Scene', on_delete=models.CASCADE)
    distance_to_center = models.FloatField(verbose_name='与场景中心距离')
    distance_to_border_far = models.FloatField(verbose_name='与场景边界最远距离')
    distance_to_border_near = models.FloatField(verbose_name='与场景边界最近距离')
    in_scene = models.BooleanField(verbose_name='是否在场景内')
    # 外部站点在主覆盖站点中的排序， 一般最多3个，
    cover_order = models.IntegerField(verbose_name='主覆盖站点', default=0)
    azimuth = models.IntegerField(verbose_name='主覆盖方向', default=0)


class OutdoorCellCoverScene(MyModel):
    site = models.ForeignKey('OutdoorSiteNearbyScene', on_delete=models.CASCADE)
    cell = models.ForeignKey('Cell', on_delete=models.CASCADE)


def get_sites_nearby_scene(_scene, queryset_sites):
    result = []
    _workspace = _scene.workspace
    _region = mymap.Region(_scene.region)
    _center = _region.get_center()
    queryset_sites = queryset_sites.filter(site_type='outdoor')
    for _site in queryset_sites:
        _point = mymap.Point(_site.lng, _site.lat)
        # 宏站按距离进行判断
        delta_lng = abs(_point.lng - _center.lng)
        delta_lat = abs(_point.lat - _center.lat)
        if delta_lng > 0.13 or delta_lat > 0.1:
            # 0.13/0.1 大约代表 22公里左右的限制
            continue
        else:
            # 得到的时包含最小距离和最大距离的tuple
            dis_boder = _point.distance(_region)
            if dis_boder[0] < DISTANCE_NEAR:
                dis_center = _point.distance(_center)
                is_in = _point.in_region(_region)
                result.append(OutdoorSiteNearbyScene(
                    workspace=_workspace,
                    scene=_scene,
                    site=_site,
                    distance_to_center=dis_center,
                    distance_to_border_near=dis_boder[0],
                    distance_to_border_far=dis_boder[1],
                    in_scene=is_in,
                ))
    return result


def get_sites_nearby_scenes(scenes, queryset_sites):
    result = []
    for _scene in scenes:
        result_for_scene = get_sites_nearby_scene(_scene, queryset_sites)
        if result_for_scene:
            get_scene_cover_sites(_scene, result_for_scene)
            result.extend(result_for_scene)
    return result


def get_cells_cover_scenes(scenes, queryset_sites_nearby_scene):
    result = []
    for _scene in scenes:
        sites_nearby_scene = queryset_sites_nearby_scene.filter(scene=_scene)
        result_for_scene = get_cells_cover_scene(scene=_scene, sites_nearby_scene=sites_nearby_scene)
        if result_for_scene:
            result.extend(result_for_scene)
    return result


def get_scene_cover_sites(scene, sites_nearby_scene):
    _sites_nearby_scene = []
    for item in sites_nearby_scene:
        if not item.in_scene:
            _sites_nearby_scene.append(item)
    if len(_sites_nearby_scene) == 1:
        _sites_nearby_scene[0].cover_order = 1
    else:
        region = mymap.Region(scene.region)
        center = region.get_center()
        ordered_sites_near_reg = sorted(_sites_nearby_scene, key=lambda e: e.distance_to_border_near)
        # 以最近的站点的方向为基准方向
        site1 = ordered_sites_near_reg[0].site
        ordered_sites_near_reg[0].cover_order = 1
        p1 = mymap.Point(site1.lng, site1.lat)
        ordered_sites_near_reg[0].azimuth = int(p1.azimuth(center))
        azimuth1 = center.azimuth(p1)
        azimuth2 = 0
        i = 1
        while i < len(ordered_sites_near_reg):
            # 计算当前的站址 和 中心点 角度
            _site = ordered_sites_near_reg[i].site
            _p = mymap.Point(_site.lng, _site.lat)
            _azimuth = center.azimuth(_p)
            if abs(_azimuth - azimuth1) < 90:
                i += 1
                continue
            azimuth2 = _azimuth
            ordered_sites_near_reg[i].cover_order = 2
            ordered_sites_near_reg[i].azimuth = int(_p.azimuth(center))
            break
        i += 1
        while i < len(ordered_sites_near_reg):
            _site = ordered_sites_near_reg[i].site
            _p = mymap.Point(_site.lng, _site.lat)
            _azimuth = center.azimuth(_p)
            if abs(_azimuth - azimuth1) < 90 or abs(_azimuth - azimuth2) < 90:
                i += 1
                continue
            ordered_sites_near_reg[i].cover_order = 3
            ordered_sites_near_reg[i].azimuth = int(_p.azimuth(center))
            break


def get_cells_cover_scene(scene, sites_nearby_scene):
    result = []
    for obj in sites_nearby_scene:
        if obj.in_scene:
            cells = obj.site.cell_set.all()
            for _cell in cells:
                result.append(OutdoorCellCoverScene(
                    site=obj,
                    cell=_cell,
                ))
        elif obj.cover_order > 0:
            _site = obj.site
            cells = _site.cell_set.all()
            for _cell in cells:
                delta_azimuth = abs(_cell.azimuth - obj.azimuth)
                if delta_azimuth < 90:
                    result.append(OutdoorCellCoverScene(
                        site=obj,
                        cell=_cell,
                    ))
    return result
