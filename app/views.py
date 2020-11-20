import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View


def index(request):
    return render(request, 'app/index.html')


class MyView(View):

    def post(self, request, *args, **kwargs):
        respon = {
            'code': 0,
            'errmsg': [],
        }
        if request.content_type == 'application/json':
            # 对于json格式的request 请求内容存储在request.body 而不是 request.POST
            body = json.loads(request.body)
            # request.POST 默认是不可修改的  _mutable 为 False
            _mutable = request.POST._mutable
            request.POST._mutable = True
            # 将body的内容更新到request.POST 以便后续使用
            request.POST.update(body)
            request.POST._mutable = _mutable
        # 从POST中获取 post_type信息--- 一个post_type字符串列表
        post_types = request.POST.getlist('post_type')
        if not post_types:
            # 如果 post_type列表为空
            respon['errmsg'].append('need post_type')
        temp_results = []
        for post_type in post_types:
            # 在View实例中 查找 名为 post_type 的方法
            handler = getattr(self, post_type, None)
            if handler:
                result = handler(request, *args, **kwargs)
            else:
                # 如果不存在,返回错误
                result = {
                    'errmsg': [
                        'post_type错误: {0} 不存在'.format(post_type)
                    ],
                }
            from django.http import HttpResponse
            if isinstance(result, HttpResponse):
                return result
            if result['errmsg']:
                # 如果存在errmsg 仅将errmsg加入到respon中
                respon['errmsg'].extend(result['errmsg'])
            else:
                # 如果此post_type没有错误,将result暂存在temp_results
                temp_results.append(result)
        # 如果respon存在errmsg 则仅返回errmsg code > 0 并等于errmsg的数量
        # 否则将所有结果合并入respon并返回JsonResponse
        if respon['errmsg']:
            respon['code'] = len(respon['errmsg'])
        else:
            for result in temp_results:
                respon.update(result)
        return JsonResponse(respon)
