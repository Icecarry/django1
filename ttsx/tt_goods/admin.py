from django.contrib import admin

from .models import GoodsCategory, IndexCategoryGoodsBanner, IndexGoodsBanner, IndexPromotionBanner, Goods

from utils import celery_tasks

from django.core.cache import cache
# from utils import gen_html

# Register your models here.
class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 当数据修改时，重新生成首页
        celery_tasks.gen_index.delay()
        # 删除首页的数据缓存
        cache.delete('index_data')

    def delete_model(self, request, obj):
        # 逻辑删除
        obj.isDelete = True
        obj.save()

        # 物理删除
        obj.delete()

        super().delete_model(request, obj)
        # 当数据删除时，需要重新生成首页
        celery_tasks.gen_index.delay()


class GoodsCategoryAdmin(BaseAdmin):
    list_display = ['id', 'name', 'logo']


class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    list_display = ['id', 'sku', 'index']

    # def save_model(self, request, obj, form, change):
    #     super().save_model(request,obj,form, change)
    #     # 当数据修改时，重新生成首页
    #
    # def delete_model(self, request, obj):
    #     # 逻辑删除
    #     obj.isDelete = True
    #     obj.save()
    #
    #     # 物理删除
    #     obj.delete()
    #
    #     super().delete_model(request, obj)
    #     # 当数据删除时，需要重新生成首页
    #     gen_html.gen_index()


class IndexGoodsBannerAdmin(BaseAdmin):
    list_display = ['id', 'sku', 'index']


class IndexPromotionBannerAdmin(BaseAdmin):
    list_display = ['id', 'name', 'url', 'index']


admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(IndexCategoryGoodsBanner, IndexCategoryGoodsBannerAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(Goods)
