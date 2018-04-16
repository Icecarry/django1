from django.conf.urls import url
from . import views

urlpatterns = [
    # url('^register$', views.register),
    # url('^register_user$', views.register_user),
    url('^register$', views.RegisterView.as_view()),
    url('^user_name$', views.user_name),
    url('^send_active_mail$', views.send_active_mail),
    url('^active/(.+)$', views.user_active),
]
