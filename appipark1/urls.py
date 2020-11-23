from django.urls import path

from . import views

# 定义url命名空间
app_name = 'ipark1'

urlpatterns = [
    # 主页
    path('', views.index, name='index'),

    # 登录页
    path('login/', views.Login.as_view(), name='login'),

    # 注销
    path('logout/', views.logout, name='logout'),

    # 实时监控
    path('fr/monitor/', views.frindex, name='monitor'),
    # 黑名单
    path('fr/blacklist/', views.BlacklistView.as_view(), name='blacklist'),
    # 黑名单抓拍记录
    path('fr/blacklist/record', views.RecordView.as_view(), name='record'),
    # 黑名单标签
    path('fr/blacklist/tag/', views.TagView.as_view(), name='tag'),
    # 设备管理
    path('fr/equipment/', views.EquipmentView.as_view(), name='equipment'),

    #  抓拍照片上传
    path('zhuapai/', views.zhuapai, name='zhuapai'),
]
