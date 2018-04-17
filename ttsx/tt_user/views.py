import re

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View

from .models import User

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from utils import celery_tasks
from django.core.mail import send_mail

# Create your views here.
# 1.定义视图，显示注册页面
# 2.定义视图，接收表单数据，完成用户的添加操作

# def register(request):
#     return render(request, 'register.html')
#
#
# def register_user(request):
#     return HttpResponse('ok')

class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 1.接收所有请求的数据
        dict1 = request.POST
        user_name = dict1.get('user_name')
        pwd = dict1.get('pwd')
        cpwd = dict1.get('cpwd')
        email = dict1.get('email')
        allow = dict1.get('allow')
        # 是否接受协议：对于checkbox如果选中则提交，如果不选中则不提交，此时值为None
        if allow == None:
            return render(request, 'register.html')
        # 2.验证数据的完整性
        # all([])　迭代列表，表中的字段如果有一个为False,则返回False
        if not all([user_name, pwd, cpwd, email]):
            return render(request, 'register.html')

        # 3.验证数据的正确性
        #   邮箱格式是否正确
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html')
        # 密码是否一致
        if cpwd != pwd:
            return render(request, 'register.html')

        # 用户名是否存在
        if User.objects.filter(username=user_name).count() >= 1:
            return render(request, 'register.html')

        # 4.保存用户对象
        usr = User.objects.create_user(user_name, email, pwd)
        # 这里用户创建后默认是激活状态，但实际需要用户手动激活，所以取消激活
        usr.is_active = False
        usr.save()


        # 5.提示：请到邮箱中激活
        return HttpResponse('请到邮箱中激活')


# 扩展：验证用户名是否存在(ajax)
# 1.写js，做ajax请求
# 2.定义视图，查询用户名，判断是否存在
def user_name(request):
    # 接受用户名
    uname = request.GET.get('uname')
    # 查询是否存在
    result = User.objects.filter(username=uname).count()
    # 使用JsonResponse
    return JsonResponse({'result': result})


# 1.发邮件
# 2.定义激活视图
# 发邮件
# 如果想发邮件，必须要有smtp服务器
# 1.配置邮件服务器（见参考文件）
# 2.写代码，发邮件
def send_active_mail(request):
    # pk是主键的意思
    # 查找邮箱
    user = User.objects.get(pk=7)
    # # 对用户编号进行加密
    # user_dirt = {'user_id': user.id}
    # serializer = Serializer(settings.SECRET_KEY, expires_in=5)
    # str1 = serializer.dump(user_dirt).decode()
    #
    # # 需要指定激活账号的编号
    # mail_body = '<a href="http://127.0.0.1:8888/user/active/%s">点击激活</a>' %str1
    # # 内容个如果为html，则第二个参数留空，再设置html_message参数
    # send_mail('用户激活', '', settings.EMAIL_FROM, [user.email], html_message=mail_body)

    # delay()将celery的任务加到队列中
    celery_tasks.send_active_mail.delay(user.email, user.id)

    # 提示
    return HttpResponse('请到邮箱中激活')


def user_active(request, user_str):
    # 1.从地址中接收用户编号
    # 解密
    serializer = Serializer(settings.SECRET_KEY)
    # 如果超过规定时间则抛出异常
    try:
        user_dict = serializer.loads(user_str)
        user_id = user_dict.get('user_id')
        print('---------------%s' %user_id)
    except:
        return HttpResponse('地址无效')
    # 2.根据编号查询用户对象
    user = User.objects.get(pk=user_id)
    # 3.修改is_active属性为True
    user.is_active = True
    user.save()
    # 4.提示：转到登录页
    return redirect('/user/login')
