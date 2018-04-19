from fdfs_client.client import Fdfs_client
from django.conf import settings

# 根据配置文件，设置fdfs客户端,通过这个对象上传对象到fdfs
# client = Fdfs_client(conf_path=settings.FDFS_CLIENT)
client = Fdfs_client(conf_path='/etc/fdfs/client.conf')

# 调用方法上传文件
result = client.upload_by_file('/home/python/Desktop/squid_girl_ika_musume-HD.jpg')

print(result)

# {'Local file name': '/home/python/Desktop/squid_girl_ika_musume-HD.jpg', 'Group name': 'group1', 'Uploaded size': '253.00KB', 'Status': 'Upload successed.', 'Storage IP': '192.168.196.130', 'Remote file_id': 'group1/M00/00/00/wKjEglrYX5GAWE7RAAP319ZrSIc101.jpg'}