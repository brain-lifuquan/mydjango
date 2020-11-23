import json
from datetime import datetime
from django.contrib import auth
# from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import render, redirect
from django.http import JsonResponse
from . import models, forms


class MyView(View):
    def post(self, request, *args, **kwargs):
        respon = {'errmsg': []}
        post_type = request.POST.get('post_type')
        post_type = post_type.split('****')
        for pos in post_type:
            handler = getattr(self, pos, self.post_type_not_allowed)
            result = handler(request, *args, **kwargs)
            if result['errmsg']:
                respon['errmsg'] += result['errmsg']
            else:
                respon.update(result)
        if respon['errmsg']:
            respon['msg'] = 'err'
        else:
            respon['msg'] = 'success'
        return JsonResponse(respon)

    def post_type_not_allowed(self, request,  *args, **kwargs):
        return {'errmsg': ['post_type error', ]}


class AppView(View):

    # @classmethod
    # def as_view(cls, **initkwargs):
    #     view = super(AppView, cls).as_view(**initkwargs)
    #     return login_required(view)

    def post(self, request, *args, **kwargs):
        respon = {'errmsg': []}
        post_type = request.POST.get('post_type')
        post_type = post_type.split('****')
        for pos in post_type:
            handler = getattr(self, pos, self.post_type_not_allowed)
            result = handler(request, *args, **kwargs)
            if result['errmsg']:
                respon['errmsg'] += result['errmsg']
            else:
                respon.update(result)
        if respon['errmsg']:
            respon['msg'] = 'err'
        else:
            respon['msg'] = 'success'
        return JsonResponse(respon)

    def post_type_not_allowed(self, request,  *args, **kwargs):
        return {'errmsg': ['post_type error', ]}


class ObjListView(AppView):

    def get(self, request, form):
        model = form._meta.model
        context = {
            'modelname': model._meta.verbose_name,
            'fields': model.get_listview_fields()
        }
        obj_list = model.objects.all()
        context['obj_list'] = [obj.values_to_listview_dict() for obj in obj_list]
        return render(request, 'appipark2/objlist.html', context=context)

    def get_model_form_info(self, request, form):
        result = {'errmsg': []}
        model = form._meta.model
        objname = request.POST.get('objname')
        if not objname:
            result['form'] = form().as_ul()
        else:
            obj = model.objects.filter(name=objname)[0]
            result['form'] = form(instance=obj).as_ul()
        return result

    def add_obj(self, request, form):
        result = {'errmsg': []}
        obj_form = form(request.POST)
        if obj_form.errors:
            result['errmsg'].append(obj_form.errors)
        else:
            obj_form.save()
        return result

    def delete_obj(self, request, form):
        result = {'errmsg': []}
        objname = request.POST.get('objname')
        model = form._meta.model
        model.objects.filter(name=objname).delete()
        return result

    def edit_obj(self, request, form):
        result = {'errmsg': []}
        objname = request.POST.get('objname')
        model = form._meta.model
        obj = model.objects.filter(name=objname)[0]
        obj_form = form(request.POST, instance=obj)
        if obj_form.errors:
            result['errmsg'].append(obj_form.errors)
        else:
            obj_form.save()
        return result


class RoutListView(AppView):

    def get(self, request):
        context = {}
        obj_list = models.Route.objects.all()
        station_list = models.Station.objects.all().order_by('route_id', 'orderid')
        dict_objs = []
        for obj in obj_list:
            dict_obj = {
                'name': obj.name,
                'type': obj.get_type_display(),
                'runningtime': obj.runningtime,
                'vehicle': obj.vehicle.name,
            }
            stations = station_list.filter(route_id=obj.id)
            if stations:
                dict_obj['station_start'], dict_obj['station_end'] = stations[0], stations[len(stations)-1]
            else:
                dict_obj['station_start'], dict_obj['station_end'] = '', ''
            dict_objs.append(dict_obj)
        context['obj_list'] = dict_objs
        return render(request, 'appipark2/route_list.html', context=context)

    def get_route_form_info(self, request):
        result = {
            'errmsg': [],
            'form': forms.RouteForm().as_ul(),
        }
        return result

    def add_route(self, request):
        result = {'errmsg': []}
        route_form = forms.RouteForm(request.POST)
        if route_form.errors:
            result['errmsg'].append(route_form.errors)
        else:
            route_form.save()
        return result

    def delete_route(self, request):
        result = {'errmsg': []}
        objname = request.POST.get('objname')
        models.Route.objects.filter(name=objname).delete()
        return result


class RouteEditView(AppView):
    def get(self, request, objname):
        return render(request, 'appipark2/route_edit.html')

    def get_route_fields(self, request, objname):
        result = {
            'errmsg': [],
            'route_fields': []
        }
        route = models.Route.objects.filter(name=objname)[0]
        for field in route._meta.fields:
            if field.name != 'id':
                result_fieid = {
                    'name': field.name,
                    'verbose_name': field.verbose_name,
                    'value': field.value_to_string(route)
                }
                if field.choices:
                    result_fieid['choices'] = field.choices
                result['route_fields'].append(result_fieid)
        return result

    def get_route_form_info(self, request, objname):
        result = {'errmsg': []}
        obj = models.Route.objects.filter(name=objname)[0]
        result['form'] = forms.RouteForm(instance=obj).as_ul()
        return result

    def get_stations(self, request, objname):
        result = {'errmsg': [], 'stations': []}
        route = models.Route.objects.filter(name=objname)[0]
        stations = models.Station.objects.filter(route_id=route.id).order_by('orderid')
        for station in stations:
            result['stations'].append({
                'name': station.name,
                'lng': station.lng,
                'lat': station.lat,
            })
        return result

    def get_route_polylines(self, request, objname):
        result = {'errmsg': [], 'polylines': []}
        route = models.Route.objects.filter(name=objname)[0]
        polylines = models.Polyline.objects.filter(route_id=route.id).order_by('orderid')
        for polyline in polylines:
            result['polylines'].append(polyline.points)
        return result

    def get_routepath(self, request, objname):
        result = {'errmsg': [], 'routepath': []}
        route = models.Route.objects.filter(name=objname)[0]
        path = models.RoutePath.objects.filter(route_id=route.id).order_by('orderid')
        for point in path:
            result['routepath'].append({
                'lng': point.lng,
                'lat': point.lat,
                'pathindex': point.pathindex,
            })
        return result

    def edit_route(self, request, objname):
        result = {'errmsg': []}
        print(request.POST)
        route = models.Route.objects.filter(name=objname)[0]
        route_form = forms.RouteForm(request.POST, instance=route)
        if route_form.errors:
            result['errmsg'].append(route_form.errors)
        else:
            models.Station.objects.filter(route_id=route.id).delete()
            models.RoutePath.objects.filter(route_id=route.id).delete()
            stations = json.loads(request.POST.get('stations'))
            for station in stations:
                models.Station(route=route, **station).save()
            routepath = json.loads(request.POST.get('routepath'))
            for point in routepath:
                models.RoutePath(
                    route=route,
                    orderid=point['orderid'],
                    lng=point['lng'],
                    lat=point['lat'],
                    pathindex=point['pathindex']
                ).save()
            route_form.save()
        return result


class RouteView(AppView):
    def get(self, request, objname):
        return render(request, 'appipark2/route_view.html')

    def get_route_fields(self, request, objname):
        result = {
            'errmsg': [],
            'route_fields': []
        }
        route = models.Route.objects.filter(name=objname)[0]
        result['route_fields'].append({
            'verbose_name': '线路名称',
            'value': route.name,
        })
        result['route_fields'].append({
            'verbose_name': '线路类型',
            'value': models.Route.choice_routetype[route.type],
        })
        result['route_fields'].append({
            'verbose_name': '运行时间',
            'value': route.runningtime,
        })
        result['route_fields'].append({
            'verbose_name': '车牌号',
            'value': route.vehicle.name,
        })
        return result

    def get_route_form_info(self, request, objname):
        result = {'errmsg': []}
        obj = models.Route.objects.filter(name=objname)[0]
        result['form'] = forms.RouteForm(instance=obj).as_ul()
        return result

    def get_route_stations(self, request, objname):
        result = {'errmsg': [], 'stations': []}
        route = models.Route.objects.filter(name=objname)[0]
        stations = models.Station.objects.filter(route_id=route.id).order_by('orderid')
        for station in stations:
            result['stations'].append({
                'name': station.name,
                'lng': station.lng,
                'lat': station.lat,
            })
        return result

    def get_routepath(self, request, objname):
        result = {'errmsg': [], 'routepath': []}
        route = models.Route.objects.filter(name=objname)[0]
        path = models.RoutePath.objects.filter(route_id=route.id).order_by('orderid')
        for point in path:
            result['routepath'].append({
                'lng': point.lng,
                'lat': point.lat,
                'pathindex': point.pathindex,
            })
        return result

    def get_route_polylines(self, request, objname):
        result = {'errmsg': [], 'polylines': []}
        route = models.Route.objects.filter(name=objname)[0]
        polylines = models.Polyline.objects.filter(route_id=route.id).order_by('orderid')
        for polyline in polylines:
            result['polylines'].append(polyline.points)
        return result

    def get_vehicle_location(self, request, objname):
        result = {'errmsg': [], 'vehicle': {}, }
        route = models.Route.objects.filter(name=objname)[0]
        runningtime = route.runningtime
        runningtime = runningtime.split('-')
        runningtime = [int(''.join(str.split(':')))for str in runningtime]
        now_time = int(datetime.strftime(datetime.now(), '%H%M'))
        if runningtime[0] <= now_time <= runningtime[1]:
            result['vehicle']['onrunning'] = 1
        else:
            result['vehicle']['onrunning'] = 0
        vehicle = route.vehicle
        equipment = vehicle.location
        eid = equipment.eid
        path = models.RoutePath.objects.filter(route_id=route.id)
        stations = models.Station.objects.filter(route_id=route.id).order_by('orderid')
        record = models.LocationRecord.objects.filter(eid=eid).order_by('-time')
        if record:
            for point in path:
                if format(record[0].lng, '.4f') == format(point.lng, '.4f') and format(record[0].lat, '.4f') == format(point.lat, '.4f'):
                    pathindex = point.pathindex
                    result['vehicle']['stations'] = (stations[pathindex].name, stations[pathindex+1].name)
            result['vehicle']['lng'] = record[0].lng
            result['vehicle']['lat'] = record[0].lat
            result['vehicle']['locationtime'] = record[0].time
        return result


class LoginView(View):
    def get(self, request):
        return render(request, 'appipark2/login.html')

    def post(self, request):
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect('appipark:route')
        else:
            context = {'errmsg': '账号或密码错误,请重新输入!!!', }
            return render(request, 'appipark/login.html', context=context)


def index(request):
    return render(request, 'appipark2/index.html')


def logout(request):
    auth.logout(request)
    return redirect('ipark2:index')


class LocationRecordListView(AppView):

    def get(self, request):
        model = models.LocationRecord
        context = {
            'modelname': model._meta.verbose_name,
            'fields': model.get_listview_fields()
        }
        obj_list = model.objects.all()
        context['obj_list'] = [obj.values_to_listview_dict() for obj in obj_list]
        return render(request, 'appipark2/location_record_list.html', context=context)

    def add_obj(self, request, form):
        result = {'errmsg': []}
        obj_form = form(request.POST)
        if obj_form.errors:
            result['errmsg'].append(obj_form.errors)
        else:
            obj_form.save()
        return result

    def delete_obj(self, request, form):
        result = {'errmsg': []}
        objname = request.POST.get('objname')
        model = form._meta.model
        model.objects.filter(name=objname).delete()
        return result

    def edit_obj(self, request, form):
        result = {'errmsg': []}
        objname = request.POST.get('objname')
        model = form._meta.model
        obj = model.objects.filter(name=objname)[0]
        obj_form = form(request.POST, instance=obj)
        if obj_form.errors:
            result['errmsg'].append(obj_form.errors)
        else:
            obj_form.save()
        return result


@csrf_exempt
def location_report(request):
    # 格式{"eid": "", "lng": 114, "lat": 38}
    record = json.loads(request.body)
    eid = record['eid']
    lng = record['lng']
    lat = record['lat']
    last_record = models.LocationRecord.objects.filter(eid=eid).order_by('-time')
    # 只有定位信息发生变化才生成新记录
    if (not last_record) or (lng != last_record[0].lng) or (lat != last_record[0].lat):
        record = models.LocationRecord(**record).save()
    return JsonResponse({'msg': 'success'})
