from django.http import JsonResponse
from django.views import View


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

    @staticmethod
    def post_type_not_allowed(request, *args, **kwargs):
        return {'errmsg': ['post_type error', ]}
