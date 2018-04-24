from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^(\d+)$', views.detail),
    url(r'^list(\d+)$', views.goods_list),
    url(r'^search/$', views.MySearchView.as_view()),
]
