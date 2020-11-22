from django.urls import path

from . import views

app_name = 'ipark'

urlpatterns = [
    # index
    path('', views.index, name='index'),

    # 素材管理
    path('material/list/<str:material_type>/', views.MaterialListView.as_view(), name='material_list'),
    path('material/<str:material_name>/', views.view_material, name='material_view'),

    # 节目分辨率
    path('program/scale_type/', views.ScaleTypeView.as_view(), name='scale_type'),

    # 节目管理
    path('program/list/', views.ProgramListView.as_view(), name='program_list'),
    path('program/new/<str:program_name>/<str:scale_type>/', views.ProgramNewView.as_view(), name='program_new'),
    path('program/<str:program_name>/', views.view_program, name='program_view'),
    path('program/edit/<str:program_name>/', views.ProgramEditView.as_view(), name='program_edit'),

    # 设备管理
    path('equipment/list/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/programs/<str:equipment_name>/', views.EquipmentProgramListView.as_view(), name='equipment_program_list'),

    # 查询信息
    path('query/', views.QueryView.as_view(), name='query'),
]