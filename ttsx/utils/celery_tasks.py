# 对json数据进行有时效性的加密
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from django.core.mail import send_mail
#引入Celery类
from celery import Celery

# 创建celery对象，通过broker指定存储队列的数据库(redis)
app = Celery('celery_tasks', broker='redis://127.0.0.1:6379/4')

# 将函数设置成celery的任务
@app.task
def send_active_mail(user_email, user_id):
    # 对用户编号进行加密
    user_dirt = {'user_id': user.id}
    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    str1 = serializer.dump(user_dirt).decode()

    # 需要指定激活账号的编号
    mail_body = '<a href="http://127.0.0.1:8888/user/active/%s"></a>' % str1
    # 内容个如果为html，则第二个参数留空，再设置html_message参数
    send_mail('用户激活', '', settings.EMAIL_FROM, [user.email], html_message=mail_body)


