import json

from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django_redis import get_redis_connection
from haystack.generic_views import SearchView

from .models import *


# Create your views here.


def index(request):
    # 首先从缓存中读取数据,如果未度取到,则进行mysql查询，然后再将数据存入cache中
    context = cache.get('index_data')
    if context is None:
        print('----------------no cache')
        # 查询数据，在模板中展示
        # 1.查询所有的分类
        category_list = GoodsCategory.objects.filter(isDelete=False)
        # 2.查询首页推荐商品
        index_goods_banner_list = IndexGoodsBanner.objects.all().order_by('index')
        # 3.查询首页广告
        index_promotion_list = IndexPromotionBanner.objects.all().order_by('index')
        # 4.遍历分类，查询每个分类的标题推荐、图片推荐
        for category in category_list:
            # 查询指定分类的标题推荐
            category.title_list = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by(
                'index')
            # 查询指定这个分类的图片推荐
            category.image_list = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by(
                'index')
        context = {
            'title': '首页',
            'category_list': category_list,
            'index_goods_banner_list': index_goods_banner_list,
            'index_promotion_list': index_promotion_list,
        }

        cache.set('index_data', context)

    # 计算购物车总数量
    context['total_count'] = get_cart_total(request)

    response = render(request, 'index.html', context)
    # # 响应体
    # html_str = response.content.decode()
    # # 打开文件
    # with open(os.path.join(settings.BASE_DIR, 'static/index.html'), 'w') as html_index:
    #     html_index.write(html_str)
    return response


def detail(request, sku_id):
    # 根据商品编号查询商品详情
    try:
        sku = GoodsSKU.objects.get(pk=sku_id)
    except:
        return Http404

    # 查询所有分类信息
    category_list = GoodsCategory.objects.filter(isDelete=False)

    # 查询当前商品所在分类,最新的两个商品
    # 根据当前商品找到对应的分类对象
    category_curr = sku.category
    # 查找指定分类的所有商品
    new_list = category_curr.goodssku_set.all().order_by('-id')[0:2]

    # 最近浏览,判断用户是否登录
    if request.user.is_authenticated():
        browser_key = 'browser%d' % request.user.id
        # 创建redis服务器的连接,默认使用settings中-->cache中的配置
        redis_client = get_redis_connection()
        # 如果当前商品已存在，则删除
        redis_client.lrem(browser_key, 0, sku_id)
        # 记录商品的编号
        redis_client.lpush(browser_key, sku_id)
        # 如果总个数超过5个，则从最右边删除一个
        if redis_client.llen(browser_key) > 5:
            redis_client.rpop(browser_key)

    # 查询陈列数据
    # 1.根据sku找spu
    spu = sku.goods
    # 根据spu找所有的sku
    sku_list = spu.goodssku_set.all()

    context = {
        'title': '商品详情页介绍',
        'sku': sku,
        'category_list': category_list,
        'new_list': new_list,
        'sku_list': sku_list,
    }

    # 计算购物车总数量
    context['total_count'] = get_cart_total(request)

    return render(request, 'detail.html', context)


def goods_list(request, category_id):
    # 查询当前的分类对象
    try:
        category = GoodsCategory.objects.get(pk=category_id)
    except:
        return Http404

    # 所有分类信息
    category_list = GoodsCategory.objects.filter(isDelete=False)

    # 本分类的商品推荐
    # new_list = GoodsSKU.objects.filter(category_id=category_id).order_by('-id')[0:2]
    new_list = category.goodssku_set.order_by('-id')[0:2]

    # 接收排序规则
    sort_str = '-id'  # 默认根据编号,最新
    sort = request.GET.get('sort', '1')
    if sort == '2':
        sort_str = 'price'  # 价格
    elif sort == '4':
        sort_str = '-price'  # 最贵
    elif sort == '3':
        sort_str = 'sales'  # 根据销量排序
    else:
        sort = '1'

    # 本分类的商品列表(分页)
    sku_list = GoodsSKU.objects.filter(category_id=category_id).order_by(sort_str)
    # 对商品列表进行分页
    paginator = Paginator(sku_list, 1)

    # 获取总页数
    num_pages = paginator.num_pages

    # 接收分页的页码
    pindex = request.GET.get('pindex', '1')

    # 验证页码的有效性
    try:
        pindex = int(pindex)
    except:
        pindex = 1
    if pindex <= 1:
        pindex = 1
    if pindex >= num_pages:
        pindex = num_pages

    # 获取第n页的数据
    page = paginator.page(pindex)

    # 已当前页码为准,构造页码列表
    # 如果当前页码不足5个，则显示所有页码
    # if num_pages <= 5:
    #     plist = range(1, num_pages + 1)
    # elif pindex <= 2:  # 如果当前页码小于等于２
    #     plist = range(1, 6)
    # elif pindex >= num_pages - 1:
    #     plist = range(num_pages - 4, num_pages + 1)
    # else:
    #     plist = range(pindex - 2, pindex + 3)
    plist = get_page_list(num_pages, pindex)
    context = {
        'title': '商品列表页面',
        'category_list': category_list,
        'new_list': new_list,
        'page': page,
        'category': category,
        'plist': plist,
        'sort': sort,
    }

    # 计算购物车总数量
    context['total_count'] = get_cart_total(request)

    return render(request, 'list.html', context)


class MySearchView(SearchView):
    """My custom search view."""

    # 自定义向模板中传递的上下文
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # 运行完视图,会向模板中传递分页对象，当前页对象
        paginator = context['paginator']
        page = context['page_obj']
        # do something
        context['plist'] = get_page_list(paginator.num_pages, page.number)

        # 向模板中传递分类信息
        context['category_list'] = GoodsCategory.objects.filter(isDelete=False)

        # 计算购物车总数量
        context['total_count'] = get_cart_total(self.request)
        context['title'] = ''
        return context


def get_page_list(num_pages, pindex):
    if num_pages <= 5:
        plist = range(1, num_pages + 1)
    elif pindex <= 2:  # 如果当前页码小于等于２
        plist = range(1, 6)
    elif pindex >= num_pages - 1:
        plist = range(num_pages - 4, num_pages + 1)
    else:
        plist = range(pindex - 2, pindex + 3)
    return plist


def get_cart_total(request):
    '''查询购物车中的数据'''
    total_count = 0
    # 判断用户是否登录
    if request.user.is_authenticated():
        # 如果登录则从redis中读取数据
        # 连接redis
        redis_client = get_redis_connection()
        # 构造键
        key = 'cart%d' % request.user.id
        # 获取所有数量
        count_list = redis_client.hvals(key)
        # 遍历相加
        if count_list:
            for count in count_list:
                total_count += int(count)

    else:
        # 如果未登录则从cookie中读取数据
        # 读取cookie
        cart_str = request.COOKIES.get('cart')
        if cart_str is not None:
            # 将字符串转换成字典
            cart_dict = json.loads(cart_str)
            # 遍历相加
            for k, v in cart_dict.items():
                total_count += v

    return total_count
