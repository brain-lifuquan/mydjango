"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from project import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # app
    path('', include('app.urls', namespace='app')),
    # npo
    path('npo/', include('appnpo.urls', namespace='npo')),
    # ipark
    path('ipark/', include('appipark.urls', namespace='ipark')),
    path('ipark1/', include('appipark1.urls', namespace='ipark1')),
    path('ipark2/', include('appipark2.urls', namespace='ipark2')),
    # 媒体文件
    re_path(r'media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
