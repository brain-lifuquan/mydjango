from django.urls import path

from . import views


app_name = 'npo'

urlpatterns = [
    path('', views.index, name='index'),
    path('workspace/list/', views.WorkSpaceListView.as_view(), name='workspace_list'),
    path('<str:workspace_name>/', views.WorkSpaceView.as_view(), name='workspace'),
    path('<str:workspace_name>/scene/', views.SceneListView.as_view(), name='scene_list'),
    path('<str:workspace_name>/site/', views.SiteListView.as_view(), name='site_list'),
    path('<str:workspace_name>/cell/', views.CellListView.as_view(), name='cell_list'),
    # # 双参数的如果第一个参数和上面的重合一定要防在最下，不然识别会出问题， url是从上到下进行匹配的
    path('<str:workspace_name>/<str:scene_name>/', views.SceneView.as_view(), name='scene'),
    path('<str:workspace_name>/<str:scene_name>/map', views.SceneMapView.as_view(), name='scene_map'),
]
