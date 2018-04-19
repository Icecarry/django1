from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FdfsStorage(Storage):
    def save(self, name, content, max_length=None):
        try:
            # 根据配置文件，设置fdfs客户端,通过这个对象上传对象到fdfs
            # client = Fdfs_client(conf_path=settings.FDFS_CLIENT)
            client = Fdfs_client(conf_path=settings.FDFS_CLIENT)

            # 调用方法上传文件
            result = client.upload_by_buffer(content.read())
            # 判断是否上传成功
            if result.get('Status') == 'Upload successed.':
                # 上传成功返回图片地址
                return result.get('Remote file_id')
            else:
                # 失败返回空字符串
                return ''
        except:
            return ''

        # {'Local file name': '/home/python/Desktop/squid_girl_ika_musume-HD.jpg', 'Group name': 'group1', 'Uploaded size': '253.00KB', 'Status': 'Upload successed.', 'Storage IP': '192.168.196.130', 'Remote file_id': 'group1/M00/00/00/wKjEglrYX5GAWE7RAAP319ZrSIc101.jpg'}

    def url(self, name):
        return settings.FDFS_URL + name
