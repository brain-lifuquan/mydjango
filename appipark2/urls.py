from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views, forms

# 定义url命名空间
app_name = 'ipark2'

urlpatterns = [
    # index页
    # path('', login_required(views.index), name='index'),
    path('', views.index, name='index'),
    # 登录页
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', login_required(views.logout), name='logout'),
    # 班车线路
    path('routelist/', views.RoutListView.as_view(), name='route'),
    path('route/edit/<str:objname>/', views.RouteEditView.as_view()),
    path('route/<objname>/', views.RouteView.as_view()),
    # 车辆
    path('vehiclelist/', views.ObjListView.as_view(), {'form': forms.VehicleForm}, name='vehicle'),
    # 设备
    path('equipmentlist/', views.ObjListView.as_view(), {'form': forms.EquipmentForm}, name='equipment'),
    # 上报location
    path('location/report/', views.location_report),
    path('location/record/', views.LocationRecordListView.as_view(), name='location'),
]
