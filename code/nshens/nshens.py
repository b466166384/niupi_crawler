import random
import re

import cfscrape
import requests
from colorama import Fore, Style
from lxml import etree
import os
from playwright.sync_api import sync_playwright
from urllib.parse import unquote
from playwright.sync_api import Page  # 用于类型提示

import time


from utils.common_utils import convert_page_index_to_num, convert_page_index_to_num_size, clean_windows_folder_name
from utils.mysqlite_util import DownloadFileDB
from utils.xunrennvshen_download import download_image, download_image_header_noname

if __name__ == '__main__':
    start_index = 2 #初始值是1
    page_num = 20
    pic_start_index = 0  #初始值是0
    pic_start_page = 1   #初始值是1
    download_fail_list = []
    if not os.path.exists("../../file/nshens"):
        os.makedirs("../../file/nshens")
    a_name = os.path.abspath('../../file/nshens')
    print(f'总路径：{a_name}')
    db = DownloadFileDB()
    scraper = cfscrape.create_scraper()
    # scraper.verify = False
    custom_headers = {
        "Accept-Language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="144", "Chromium";v="144", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": '?0',
        "priority":"u=0, i",
        "referer":"https://nshens.com/",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "sec-fetch-dest":"document",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": '1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/143.0.0.1 Safari/537.37"
    }
    # https://buondua.com/tag/private-photoshoot-12486
    # https://buondua.com/tag/xr-uncensored-11790
    # https://buondua.com/tag/jvid-11832
    url = "https://nshens.com/web/tag/%E9%9C%B2%E7%82%B9/"
    base_url = "https://nshens.com"
    content_url = url + str(start_index)
    print(content_url)
    # 使用Playwright访问页面
    with sync_playwright() as p:
        try:
            # 启动浏览器（无头模式，可改为False调试）
            browser = p.chromium.launch(
                headless=True,
                # 可选：添加浏览器参数，模拟真实环境
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
                ]
            )
            # # 创建页面并设置自定义请求头
            page = browser.new_page(
                extra_http_headers=custom_headers,
                # 自动携带Cookie（Playwright会自动处理抓包中的Cookie）
                bypass_csp=True  # 可选：绕过内容安全策略，避免请求被拦截
            )
            # 1. 先访问页面域名（确保localStorage作用域正确）
            page.goto(content_url, timeout=240000)  # 访问基础域名，初始化上下文
            # 5. 获取页面内容
            page_content = page.content()
            parser = etree.HTMLParser(encoding="utf-8")
            tree = etree.HTML(page_content, parser=parser)
            pic_detail_url_list = tree.xpath('//div[@class="row justify-start"]//div[@class="col"]/a/@href')
            pic_detail_url_list = list(dict.fromkeys(pic_detail_url_list))
            # pic_detail_url_list = ['/web/2026/02/27/free10021816unknown', '/web/2026/02/26/free10022131%E5%B9%B4%E5%B9%B4', '/web/2026/02/22/free10021054%E5%B9%B4%E5%B9%B4', '/web/2026/02/22/free10021814%E5%B8%8C%E5%90%BE', '/web/2026/02/22/free10021654%E5%B9%B4%E5%B9%B4', '/web/2026/02/22/free10021856unknown', '/web/2026/02/21/free10021098%E5%B9%B4%E5%B9%B4', '/web/2026/02/20/free10021096unknown', '/web/2026/02/19/free10021056unknown', '/web/2026/02/18/free10020957%E5%B9%B4%E5%B9%B4', '/web/2026/02/18/free10020956%E5%B9%B4%E5%B9%B4', '/web/2026/02/17/free10020808unknown']
            print(len(pic_detail_url_list))
            print(pic_detail_url_list)
            for detail_index, detail_param in enumerate(pic_detail_url_list):
                if detail_index < pic_start_index:
                    continue
                print(f"{Fore.YELLOW}pic_start_index:{detail_index}总{len(pic_detail_url_list)}{Style.RESET_ALL}")
                page.goto(base_url+detail_param, timeout=240000)
                detail_page_text = page.content()
                # print(detail_page_text)
                detail_tree = etree.HTML(detail_page_text, parser=parser)
                detail_info = detail_tree.xpath('//h3/text()')[0]
                title = detail_info
                detail_title = clean_windows_folder_name(title)
                exact_result = db.get_by_title_custom(title=detail_title, table_name="nshens")
                print(f"精确匹配结果：{exact_result}")
                if exact_result:
                    print(f"{Fore.YELLOW}目录{detail_title}已下载过了，跳过下载{Style.RESET_ALL}")
                    continue  # 直接跳过当前条目的所有后续逻辑（包括下载、创建文件夹）
                save_file_path = os.path.join(a_name, detail_title)
                if not os.path.exists(save_file_path):
                    os.makedirs(save_file_path)
                    print(f"创建保存路径：{save_file_path}")
                nav_div = detail_tree.xpath('//div[@class="item"]/text()')
                cleaned_data = []
                for item in nav_div:
                    # 提取字符串中的数字部分
                    match = re.search(r'\d+', item)
                    if match:
                        cleaned_data.append(match.group())
                detail_total = cleaned_data[len(cleaned_data) - 1]
                print(f"{Fore.GREEN}{detail_title}  detail_total:共{detail_total}页{Style.RESET_ALL}")
                prefix = '/web/photo?url='
                for page_index in range(pic_start_page, int(detail_total) + 1):
                    if page_index == 1:
                        pic_url_list = detail_tree.xpath('//div[@class="v-sheet theme--light main-article"]//div//a/@href')
                        print(pic_url_list)
                        for index in range(0, 5):
                            # img_name = convert_page_index_to_num_size(f"{page_index}_{index}", 20)
                            img_url = pic_url_list[index]
                            if img_url.startswith(prefix):
                                encoded_url = img_url[len(prefix):]
                            else:
                                # 如果前缀不匹配，可以根据需求选择报错或直接使用原字符串
                                encoded_url = img_url
                                # 2. URL 解码 (将 %3A, %2F 等转换回 :, /)
                            real_url = unquote(encoded_url)
                            if "https://" not in url:
                                continue
                            fileSize = download_image_header_noname(real_url, save_file_path,custom_headers)
                            # time.sleep(random.uniform(2, 5))
                            if fileSize == "失败":
                                fileSize2 = download_image_header_noname(real_url, save_file_path,custom_headers)
                                if fileSize2 == "失败":
                                    my_map = {
                                        "url": real_url,
                                        "title": detail_title
                                    }
                                    download_fail_list.append(my_map)
                                    print(f"download_fail_list：{download_fail_list}")
                            else:
                                print(f"第{index + 1}张图片{fileSize}下载完成")
                        print(
                            f"{Fore.BLUE}第{detail_index}个的第{page_index}页{detail_title}下载完成共{detail_total}页{Style.RESET_ALL}")
                    else:
                        time.sleep(random.uniform(5, 10))
                        print(f"{Fore.RED}第{page_index}页开始下载{Style.RESET_ALL}")
                        # detail_page2_text = requests.get(url=base_url + detail_param + '?page=' + str(page_index),
                        #                                  headers=custom_headers).text
                        # detail_tree2 = etree.HTML(detail_page2_text, parser=parser)
                        page.goto(base_url + detail_param+"/"+str(page_index), timeout=240000)
                        detail_page_text = page.content()
                        # print(detail_page_text)
                        detail_tree = etree.HTML(detail_page_text, parser=parser)
                        pic_url_list = detail_tree.xpath(
                            '//div[@class="v-sheet theme--light main-article"]//div//a/@href')
                        print(pic_url_list)
                        for index in range(0, 5):
                            # img_name = convert_page_index_to_num_size(f"{page_index}_{index}", 20)
                            img_url = pic_url_list[index]
                            if img_url.startswith(prefix):
                                encoded_url = img_url[len(prefix):]
                            else:
                                # 如果前缀不匹配，可以根据需求选择报错或直接使用原字符串
                                encoded_url = img_url
                                # 2. URL 解码 (将 %3A, %2F 等转换回 :, /)
                            real_url = unquote(encoded_url)
                            if "https://" not in url:
                                continue
                            fileSize = download_image_header_noname(real_url, save_file_path, custom_headers)
                            # time.sleep(random.uniform(2, 5))
                            if fileSize == "失败":
                                fileSize2 = download_image_header_noname(real_url, save_file_path, custom_headers)
                                if fileSize2 == "失败":
                                    my_map = {
                                        "url": real_url,
                                        "title": detail_title
                                    }
                                    download_fail_list.append(my_map)
                                    print(f"download_fail_list：{download_fail_list}")
                            else:
                                print(f"第{index + 1}张图片{fileSize}下载完成")
                        print(
                            f"{Fore.BLUE}第{detail_index}个的第{page_index}页{detail_title}下载完成共{detail_total}页{Style.RESET_ALL}")
                new_id = db.insert_custom(title=detail_title, table_name="nshens")
                print(f"新增记录成功，id：{new_id}")
                if pic_start_page == 1:
                    time.sleep(random.uniform(5, 10))
                else:
                    exit(0)
            print(download_fail_list)

        except Exception as e:
            print(f"操作失败：{str(e)}")
        finally:
            # 确保浏览器关闭
            if 'browser' in locals():
                browser.close()
            # 关闭数据库连接（如果需要）
            # db.close()






















