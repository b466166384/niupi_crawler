import os
import time
import cfscrape
import requests
import random
import urllib3  # 导入urllib3用于禁用警告
from colorama import Fore, Style
from fake_useragent import UserAgent  # 需要安装：pip install fake-useragent

# 核心修复：禁用InsecureRequestWarning警告（关键！）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def download_image(img_src, save_dir, img_name):
    # 1. 初始化配置
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Referer': img_src.rsplit('/', 2)[0] + '/',
        'Accept': 'image/webp,image/png,image/jpeg,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',  # 禁用br压缩，减少SSL握手问题
        'Connection': 'keep-alive'
    }

    # 2. 创建scraper（增加重试）
    scraper = cfscrape.create_scraper(delay=random.uniform(2,8 ))
    save_path = os.path.join(save_dir, str(img_name)+'.jpg')

    # 确保保存目录存在
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # print(f"{Fore.BLUE}正在处理: {img_src}{Style.RESET_ALL}")

    # 4. 重试机制：最多重试3次
    max_retries = 3
    for retry in range(max_retries):
        try:
            # 核心修复1：忽略SSL验证（解决SSLEOFError）
            response = scraper.get(
                img_src,
                headers=headers,
                allow_redirects=True,
                timeout=30,
                verify=False,  # 关闭SSL证书验证（关键！）
                stream=True  # 流式下载，减少内存占用
            )

            # 检查响应状态
            if response.status_code != 200:
                print(f"{Fore.RED}[重试{retry + 1}] 请求失败，状态码: {response.status_code}{Style.RESET_ALL}")
                time.sleep(2 ** retry)  # 指数退避延迟
                continue

            # 检查是否为图片
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                # 核心修复2：尝试降级为HTTP（HTTPS失败时）
                if img_src.startswith('https'):
                    img_src_http = img_src.replace('https://', 'http://')
                    print(f"{Fore.YELLOW}HTTPS失败，尝试HTTP: {img_src_http}{Style.RESET_ALL}")
                    response = scraper.get(
                        img_src_http,
                        headers=headers,
                        allow_redirects=True,
                        timeout=30,
                        verify=False
                    )
                    if response.status_code != 200 or not response.headers.get('Content-Type', '').startswith('image/'):
                        print(f"{Fore.RED}HTTP降级也失败{Style.RESET_ALL}")
                        continue
                else:
                    print(f"{Fore.YELLOW}返回非图片内容，类型: {content_type}{Style.RESET_ALL}")
                    continue

            # 5. 保存图片（流式写入）
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # 计算文件大小
            file_size = os.path.getsize(save_path) / 1024
            file_size_str = f"{file_size:.2f}KB"
            # print(f"{Fore.GREEN}保存成功: {save_path} (大小: {file_size_str}){Style.RESET_ALL}")
            return file_size_str

        # 核心修复3：修正cfscrape异常类（只捕获存在的异常）
        except cfscrape.CloudflareCaptchaError as e:
            print(f"{Fore.RED}[重试{retry + 1}] Cloudflare验证码失败: {str(e)}{Style.RESET_ALL}")
            time.sleep(5)
        except requests.exceptions.SSLError as e:
            print(f"{Fore.RED}[重试{retry + 1}] SSL连接错误: {str(e)}{Style.RESET_ALL}")
            # SSL错误时尝试HTTP降级
            if img_src.startswith('https') and retry == 0:
                img_src = img_src.replace('https://', 'http://')
                print(f"{Fore.YELLOW}切换为HTTP重试: {img_src}{Style.RESET_ALL}")
            time.sleep(2 ** retry)
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[重试{retry + 1}] 请求异常: {str(e)}{Style.RESET_ALL}")
            time.sleep(2 ** retry)
        except Exception as e:
            print(f"{Fore.RED}[重试{retry + 1}] 未知错误: {str(e)}{Style.RESET_ALL}")
            time.sleep(2 ** retry)

    # 所有重试失败
    print(f"{Fore.RED}所有重试失败，放弃下载: {img_src}{Style.RESET_ALL}")
    return "失败"