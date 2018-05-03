import uuid

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django_redis import get_redis_connection

from tt_goods.models import GoodsSKU
from tt_user.models import Address
from .models import OrderInfo, OrderGoods
from django.db.models import F


# Create your views here.


@login_required
def index(request):
    sku_ids = request.GET.getlist('sku_id')
    if not sku_ids:
        return redirect('/cart/')

    sku_list = []
    for sku_id in sku_ids:
        try:
            sku = GoodsSKU.objects.get(pk=sku_id)
        except:
            return Http404()
        # 查询数量
        redis_client = get_redis_connection()
        key = 'cart%d' % request.user.id
        sku.cart_count = redis_client.hget(key, sku_id)
        # 加入列表
        sku_list.append(sku)

    # 商品编号字符串[1,2,3]==>'1,2,3'
    skuid_str = ','.join(sku_ids)

    # 查询收货地址
    addr_list = request.user.address_set.all()
    context = {
        'title': '提交订单',
        'addr_list': addr_list,
        'sku_list': sku_list,
        'skuid_str': skuid_str,
    }
    return render(request, 'place_order.html', context)


@login_required
@transaction.atomic  # 当前视图函数中支持事务
def handle(request):
    if request.method != 'POST':
        return Http404()
    # 接收数据
    dict1 = request.POST
    addr_id = dict1.get('addr_id')
    pay_style = dict1.get('pay_style')
    sku_ids = dict1.get('sku_ids')

    # 验证
    # 数据完整性
    if not all([addr_id, pay_style, sku_ids]):
        return JsonResponse({'result': '参数不完整'})
    # 支付方式只支持1,2
    if pay_style not in ['1', '2']:
        return JsonResponse({'result': '参数错误'})
    try:
        Address.objects.get(pk=addr_id, user_id=request.user.id)
    except:
        return JsonResponse({'result': '参数错误'})
    # 验证商品编号的有效性
    sku_ids = sku_ids.split(',')
    for sku_id in sku_ids:
        try:
            GoodsSKU.objects.get(pk=sku_id)
        except:
            return JsonResponse({'result': '参数错误'})

    # 处理
    # 开启事务
    sid = transaction.savepoint()
    # 1.创建订单对象
    order_info = OrderInfo()
    order_info.order_id = str(uuid.uuid1())
    order_info.user = request.user
    order_info.address_id = int(addr_id)
    order_info.total_count = 1
    order_info.total_amount = 0
    order_info.trans_cost = 10
    order_info.pay_method = int(pay_style)

    order_info.save()
    # 2.遍历商品对象, 逐个创建订单详细对象
    redis_client = get_redis_connection()
    key = 'cart%d' % request.user.id
    total_count = 0
    total_amount = 0
    for sku_id in sku_ids:
        # 获取购物车中的数量
        cart_count = int(redis_client.hget(key, sku_id))

        # # 查询当前商品
        # sku = GoodsSKU.objects.get(pk=sku_id)
        # # 如果库存不足购买量，则返回购物车页面
        # if sku.stock < cart_count:
        #     # 回滚事务
        #     transaction.savepoint_rollback(sid)
        #     return redirect('/cart/')
        # # 3.修改商品的库存, 销量
        # sku.stock -= cart_count
        # sku.sales += cart_count
        # sku.save()
        # 返回表中受影响的行数
        # update ... set ... where ... 乐观锁
        result_count = GoodsSKU.objects.filter(pk=sku_id, stock__gte=cart_count).\
            update(stock=F('stock')-cart_count, sales=F('sales')+cart_count)
        if result_count < 1:
            # 回滚事务
            transaction.savepoint_rollback(sid)
            return JsonResponse({'result': 'cart'})

        # 查询sku对象
        sku = GoodsSKU.objects.get(pk=sku_id)

        # 4.创建订单详细对象
        detail = OrderGoods()
        detail.order = order_info
        detail.sku = sku
        detail.count = cart_count
        detail.price = sku.price
        detail.save()
        # 1.2计算总数量、总金额
        total_count += cart_count
        total_amount += cart_count * sku.price
    # 1.3.修改总数量、总金额
    order_info.total_count = total_count
    order_info.total_amount = total_amount
    order_info.save()

    # 提交事务
    transaction.savepoint_commit(sid)

    # 5.将购物车中对应的商品删除
    for sku_id in sku_ids:
        redis_client.hdel(key, sku_id)

    return JsonResponse({'result': 'ok'})
