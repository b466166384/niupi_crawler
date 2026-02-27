import os
import re

import time
import cfscrape
import requests
from lxml import etree
import urllib3
from colorama import Fore, Back, Style, init
from pyasn1_modules.rfc5280 import common_name

from utils.common_utils import convert_page_index_to_num

# 禁用不安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 1. 首先处理图片URL，补充协议头
# 从标签提取的src是相对路径：//img.xsnvshen.co/album/22359/45149/000.jpg
def fix_image_url(relative_url):
    # 补充https协议头，否则请求会失败
    if relative_url.startswith('//'):
        return f'https:{relative_url}'
    elif relative_url.startswith('/'):
        return f'https://img.xsnvshen.co{relative_url}'
    return relative_url


# 2. 构建完整的请求头（关键：完全模拟浏览器）
HEADERS = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    # 替换为你浏览器中的最新Cookie（必须从当前会话获取）
    "Cookie": "__vtins__=...; __51uvsct__=...; __51vcke__=...",  # 从浏览器复制完整Cookie
    "Host": "img.xsnvshen.co",
    # 防盗链关键：Referer必须是图片所在的具体页面URL
    "Referer": "https://www.xsnvshen.co/album/hd/10813.html",  # 替换为实际图片所在页面URL
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-site"
}


# 3. 下载图片的核心函数
def download_image(img_src, save_dir):
    # 修复URL
    img_url = fix_image_url(img_src)
    # print(f"处理后的图片URL: {img_url}")
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        # 发送请求
        response = requests.get(
            url=img_url,
            headers=HEADERS,
            timeout=60,
            verify=False  # 绕过SSL验证（部分服务器证书配置问题）
        )

        # 检查响应状态
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return "失败"

        # 检查是否为图片类型
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"返回内容不是图片，类型: {content_type}")
            return "失败"

        # 获取文件名并保存
        img_name = os.path.basename(img_url)
        save_path = os.path.join(save_dir, img_name)

        with open(save_path, 'wb') as f:
            f.write(response.content)
        fileSize = f"{len(response.content) / 1024:.2f}KB"
        # print(f"图片保存成功: {save_path} (大小: {len(response.content) / 1024:.2f}KB)")
        return fileSize

    except Exception as e:
        print(f"{Fore.YELLOW}下载失败: {str(e)}{Style.RESET_ALL}")
        return "失败"

def download_image_header(img_src, index,save_dir,header):
    # 修复URL
    img_url = fix_image_url(img_src)
    # print(f"处理后的图片URL: {img_url}")
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        # 发送请求
        response = requests.get(
            url=img_url,
            headers=header,
            timeout=60,
            verify=False  # 绕过SSL验证（部分服务器证书配置问题）
        )

        # 检查响应状态
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return "失败"

        # 检查是否为图片类型
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"返回内容不是图片，类型: {content_type}")
            return "失败"

        # 获取文件名并保存
        img_name = convert_page_index_to_num(index)
        save_path = os.path.join(save_dir, str(img_name)+".jpg")

        with open(save_path, 'wb') as f:
            f.write(response.content)
        fileSize = f"{len(response.content) / 1024:.2f}KB"
        # print(f"图片保存成功: {save_path} (大小: {len(response.content) / 1024:.2f}KB)")
        return fileSize

    except Exception as e:
        print(f"{Fore.YELLOW}下载失败: {str(e)}{Style.RESET_ALL}")
        return "失败"


def download_image_header_noname(img_src,save_dir,header):
    # 修复URL
    img_url = fix_image_url(img_src)
    # print(f"处理后的图片URL: {img_url}")
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        # 发送请求
        response = requests.get(
            url=img_url,
            headers=header,
            timeout=60,
            verify=False  # 绕过SSL验证（部分服务器证书配置问题）
        )

        # 检查响应状态
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return "失败"

        # 检查是否为图片类型
        # content_type = response.headers.get('Content-Type', '')
        # if not content_type.startswith('image/'):
        #     print(f"返回内容不是图片，类型: {content_type}")
        #     return "失败"

        # 获取文件名并保存
        img_name = os.path.basename(img_url).lower()
        if img_name.endswith('.gif'):
            print(f"{Fore.BLUE}跳过GIF图片（文件名）: {img_url}{Style.RESET_ALL}")
            return "gif跳过"
        save_path = os.path.join(save_dir, img_name)

        with open(save_path, 'wb') as f:
            f.write(response.content)
        fileSize = f"{len(response.content) / 1024:.2f}KB"
        # print(f"图片保存成功: {save_path} (大小: {len(response.content) / 1024:.2f}KB)")
        return fileSize

    except Exception as e:
        print(f"{Fore.YELLOW}下载失败: {str(e)}{Style.RESET_ALL}")
        return "失败"


def download_image_aimeizi(img_src, save_dir, header):
    img_url = fix_image_url(img_src)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        # 先发送 HEAD 请求获取文件大小（可选，用于校验）
        head_response = requests.head(img_url, headers=header, timeout=10, verify=False)
        expected_size = head_response.headers.get('Content-Length')  # 服务器声明的文件大小

        # 流式下载，确保完整写入
        with requests.get(
            img_url,
            headers=header,
            timeout=30,  # 增大超时时间（大图片需要更久）
            verify=False,
            stream=True  # 流式传输
        ) as response:
            response.raise_for_status()  # 自动抛出4xx/5xx错误

            # 检查图片类型
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                print(f"非图片类型: {content_type}")
                return "失败"

            # 提取文件名（优化扩展名匹配）
            img_name = os.path.basename(img_url)
            # pattern = re.compile(r'(\d+\.\w+)$')
            # match = pattern.search(img_name)
            # # 修改后：确保最终后缀为.avif，同时保留数字或原始名称主体
            # if match:
            #     # 匹配到数字时，用数字 + .avif（如 "157.avif"）
            #     final_name = f"{match.group(1)}.avif"
            # else:
                # 未匹配到数字时，取原始文件名的主体部分 + .avif
                # 例如 "image.jpg" → "image.avif"，"photo" → "photo.avif"
            name_without_ext = os.path.splitext(img_name)[0]  # 去除原始扩展名
            final_name = f"{name_without_ext}.avif"
            # 从 Content-Type 推断真实扩展名（避免扩展名错误）
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            # 替换错误的扩展名（如果能匹配到已知类型）
            for ctype, ext in ext_map.items():
                if content_type == ctype and not final_name.lower().endswith(ext):
                    final_name = os.path.splitext(final_name)[0] + ext
                    break

            save_path = os.path.join(save_dir, final_name)

            # 流式写入文件（避免内存占用过大，且确保完整）
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB分片
                    if chunk:  # 过滤空块
                        f.write(chunk)

            # 校验文件大小（如果服务器提供了Content-Length）
            if expected_size:
                actual_size = os.path.getsize(save_path)
                if int(expected_size) != actual_size:
                    print(f"文件不完整（预期: {expected_size}B，实际: {actual_size}B）")
                    os.remove(save_path)
                    return "失败"

            file_size = f"{actual_size / 1024:.2f}KB"
            print(f"下载成功: {save_path}（{file_size}）")
            return file_size

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {str(e)}")
        return "失败"
    except Exception as e:
        print(f"其他错误: {str(e)}")
        return "失败"


def download_image_hit(img_src, save_dir, header):
    img_url = fix_image_url(img_src)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        # 先发送 HEAD 请求获取文件大小（可选，用于校验）
        head_response = requests.head(img_url, headers=header, timeout=60, verify=False)
        expected_size = head_response.headers.get('Content-Length')  # 服务器声明的文件大小

        # 流式下载，确保完整写入
        with requests.get(
            img_url,
            headers=header,
            timeout=30,  # 增大超时时间（大图片需要更久）
            verify=False,
            stream=True  # 流式传输
        ) as response:
            response.raise_for_status()  # 自动抛出4xx/5xx错误

            # 检查图片类型
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                print(f"非图片类型: {content_type}")
                return "失败"

            # 提取文件名（优化扩展名匹配）
            img_name = os.path.basename(img_url)
            # pattern = re.compile(r'(\d+\.\w+)$')
            # match = pattern.search(img_name)
            # # 修改后：确保最终后缀为.avif，同时保留数字或原始名称主体
            # if match:
            #     # 匹配到数字时，用数字 + .avif（如 "157.avif"）
            #     final_name = f"{match.group(1)}.avif"
            # else:
                # 未匹配到数字时，取原始文件名的主体部分 + .avif
                # 例如 "image.jpg" → "image.avif"，"photo" → "photo.avif"
            name_without_ext = os.path.splitext(img_name)[0]  # 去除原始扩展名
            final_name = f"{name_without_ext}.avif"
            # 从 Content-Type 推断真实扩展名（避免扩展名错误）
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            # 替换错误的扩展名（如果能匹配到已知类型）
            for ctype, ext in ext_map.items():
                if content_type == ctype and not final_name.lower().endswith(ext):
                    final_name = os.path.splitext(final_name)[0] + ext
                    break

            save_path = os.path.join(save_dir, final_name)

            # 流式写入文件（避免内存占用过大，且确保完整）
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB分片
                    if chunk:  # 过滤空块
                        f.write(chunk)

            # 校验文件大小（如果服务器提供了Content-Length）
            if expected_size:
                actual_size = os.path.getsize(save_path)
                if int(expected_size) != actual_size:
                    print(f"文件不完整（预期: {expected_size}B，实际: {actual_size}B）")
                    os.remove(save_path)
                    return "失败"

            file_size = f"{actual_size / 1024:.2f}KB"
            print(f"下载成功: {save_path}（{file_size}）")
            return file_size

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {str(e)}")
        return "失败"
    except Exception as e:
        print(f"其他错误: {str(e)}")
        return "失败"


def download_image_xiaohuangshu(img_src, save_dir):
    scraper = cfscrape.create_scraper()
    print(img_src)
    try:
        # 发送请求（自动处理验证）
        response = scraper.get(img_src)
        # 等待验证完成（可选，增加容错）
        time.sleep(10)
        # 检查响应状态
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return "失败"

        # 检查是否为图片类型
        # content_type = response.headers.get('Content-Type', '')
        # if not content_type.startswith('image/'):
        #     print(f"返回内容不是图片，类型: {content_type}")
        #     return "失败"

        # 获取文件名并保存
        img_name = os.path.basename(img_src)
        save_path = os.path.join(save_dir, img_name)

        with open(save_path, 'wb') as f:
            f.write(response.content)
        fileSize = f"{len(response.content) / 1024:.2f}KB"
        # print(f"图片保存成功: {save_path} (大小: {len(response.content) / 1024:.2f}KB)")
        return fileSize

    except Exception as e:
        print(f"{Fore.YELLOW}下载失败: {str(e)}{Style.RESET_ALL}")
        return "失败"
