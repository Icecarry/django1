import re

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from utils import celery_tasks
from .models import User, AreaInfo, Address

# django提供的用户验证功能
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from utils.views import LoginRequiredViewMixin, LoginRequiredView

# Create your views here.
# 1.定义视图，显示注册页面
# 2.定义视图，接收表单数据，完成用户的添加操作

# def register(request):
#     return render(request, 'register.html')
#
#
# def register_user(request):
#     return HttpResponse('ok')


class RegisterView(LoginRequiredView, View):
    def get(self, request):
        context = {
            'title': '注册',
        }
        return render(request, 'register.html', context)

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
        user = User.objects.create_user(user_name, email, pwd)
        # 这里用户创建后默认是激活状态，但实际需要用户手动激活，所以取消激活
        user.is_active = False
        user.save()

        # 5.提示：请到邮箱中激活
        celery_tasks.send_active_mail.delay(user.email, user.id)

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
    user = User.objects.get(pk=9)
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
        print('---------------%s' % user_id)
    except:
        return HttpResponse('地址无效')
    # 2.根据编号查询用户对象
    user = User.objects.get(pk=user_id)
    # 3.修改is_active属性为True
    user.is_active = True
    user.save()
    # 4.提示：转到登录页
    return redirect('/user/login')


class LoginView(View):
    # 登陆
    def get(self, request):
        # 从cookies中读取用户名，并显示在界面中
        username = request.COOKIES.get('username', '')
        context = {
            'username': username,
            'title': '登录'
        }

        return render(request, 'login.html', context)

    def post(self, request):
        # 1.接收
        dict1 = request.POST
        username = dict1.get('username')
        pwd = dict1.get('pwd')
        remember = dict1.get('remember')

        # 2.验证完整性
        if not all([username, pwd]):
            return render(request, 'login.html')

        # 3.验证正确性,查询用户名与密码对应的用户是否存在
        # 如果用户名密码正确则返回user对象, 否则返回None
        user = authenticate(username=username, password=pwd)

        # 判断用户是否正确
        if user is None:
            return render(request, 'login.html', {'msg': '用户名密码错误'})

        # 加逻辑1:-----状态保持
        # 1.配置session
        # 2.login
        login(request, user)

        # 加逻辑3:如果有来源页面，则转到那个页面，如果没有，则转到首页
        login_url = request.GET.get('next', '/')
        response = redirect(login_url)

        # 加逻辑2:----记住用户名，存储到cookies中
        if remember is None:
            response.delete_cookie('username')
        else:
            response.set_cookie('username', username, expires=60*60*24*7)

        # 用户名密码正确返回首页
        return response


def user_logout(request):
    logout(request)
    return redirect('/user/login')


@login_required
def info(request):
    # 判断用户是否登陆，登陆显示信息，未登录转到登陆页
    # if not request.user.is_authenticated():
    #     return redirect('/user/login')

    context = {
        'title': '个人信息',
    }

    return render(request, 'user_center_info.html', context)


@login_required
def order(request):
    context = {
        'title': '全部订单'
    }

    return render(request, 'user_center_order.html', context)


# @login_required
# def site(request):
class SiteView(LoginRequiredViewMixin, View):
    def get(self, request):
        # 获取用户
        user = request.user
        # 查找当前用户的所有收货地址
        addr_list = user.address_set.all()

        context = {
            'title': '收货地址',
            'addr_list': addr_list,
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        # 接收数据
        dict1 = request.POST
        receiver_name = dict1.get('receiver_name')
        province_id = dict1.get('province')
        city_id = dict1.get('city')
        district_id = dict1.get('district')
        detail_addr = dict1.get('detail_addr')
        zip_code = dict1.get('zip_code')
        receiver_mobile = dict1.get('receiver_mobile')
        # 创建对象
        addr = Address()
        addr.receiver_name = receiver_name
        addr.province_id = province_id
        addr.city_id = city_id
        addr.district_id = district_id
        addr.detail_addr = detail_addr
        addr.zip_code = zip_code
        addr.receiver_mobile = receiver_mobile
        addr.user_id = request.user.id
        # 保存
        addr.save()
        return redirect('/user/site')


def area(request):
    # 接收请求地址的编号，查询这个请求地址编号为父级的地区
    pid = request.GET.get('pid')
    print(pid)
    if pid is None:
        # 查询省信息
        area_list = AreaInfo.objects.filter(aParent__isnull=True)
    else:
        # 如果pid是省的编号则查询市的编号，如果pid是市的编号则查询区的编号
        area_list = AreaInfo.objects.filter(aParent_id=pid)

    # 重新整理结构为{'id':***, 'title': ***}
    list1 = []
    for a in area_list:
        list1.append({'id': a.id, 'title': a.atitle})

    # print(list1[1])
    # 返回的格式为{'list1: [{},{},{},...]}
    return JsonResponse({'list1': list1})

