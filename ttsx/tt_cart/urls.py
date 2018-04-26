from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^add$', views.add),
    url(r'^$', views.index),
    url(r'^edit$', views.edit),
    url(r'^delete$', views.cart_delete),
]
