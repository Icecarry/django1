from django.views.generic import View
from django.contrib.auth.decorators import login_required


# 自定义as_view类
class LoginRequiredView(View):
    @classmethod
    def as_view(cls, **initkwargs):
        view_fun = super().as_view(**initkwargs)
        return login_required(view_fun)


# 自定义ad_view混合类
class LoginRequiredViewMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view_fun = super().as_view(**initkwargs)
        return login_required(view_fun)
