import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from downloader import downloader

# 测试参数
img_url = "https://tw.8se.me/photoShow.html?id=PXAeRv3h073BuoSgSjeCikY3YmxKZ1cwSWNubkhIVFF4bm1DcGlOSHVwOTFWSllKUk9LNnJGcktRSFE9"
save_dir = "./test_images"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 确保保存目录存在
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 执行下载
result = downloader(img_url, save_dir, headers)
print(f"下载结果: {result}")