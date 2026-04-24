import os
import sys
from colorama import Fore, Style
from lxml import etree


sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from DownloadFileDB import DownloadFileDB
from ImageDownloader import download_image
import time
from playwright.sync_api import sync_playwright

def get_page_with_playwright(url, headers, scroll_count=3):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.set_extra_http_headers(headers)
        
        page.goto(url, wait_until='networkidle', timeout=60000)
        
        page.wait_for_timeout(2000)
        
        for i in range(scroll_count):
            page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
            page.wait_for_timeout(2000)
            print(f"已滚动第 {i+1} 次")
        
        content = page.content()
        browser.close()
        return content

if __name__ == '__main__':
    page = 0 #初始值0
    detail_page = 0 #初始值0
    pic_start_index = 0 #初始值0
    download_fail_list = []
    headers = {
        "Accept": "text/html, application/xhtml+xml, application/xml;q=0.9, image/webp, image/apng, application/json, text/plain; q=0.8",
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        "Referer": "https://tw.8se.me/",
    }
    url = f'https://www.pornpics.com/zh/japanese/'
    if not os.path.exists("./downloadFile/pornpics"):
        os.makedirs("./downloadFile/pornpics")
    a_name = os.path.abspath('./downloadFile/pornpics')
    print(a_name)
    db = DownloadFileDB()
    parser = etree.HTMLParser(encoding="utf-8")
    page_text = get_page_with_playwright(url, headers,page)
    tree = etree.HTML(page_text, parser=parser)
    detail_list = []
    items = tree.xpath('//ul[@class="wookmark-initialised"]//li')
    for item in items:
        # 检查li标签class是否包含r2-frame
        li_class = item.get('class', '')
        if 'r2-frame' in li_class:
            continue
        # 获取链接
        link = item.xpath('.//a/@href')
        if link:
            detail_list.append(link[0])
    print(f"第{page}页,共{len(detail_list)}条数据",f"{detail_list}")
    for detail_index, detail_url in enumerate(detail_list):
        exact_result = db.get_by_url_custom(url=detail_url, table_name="pornpics")
        if exact_result:
            print(f"{Fore.GREEN}已存在:{detail_url}{Style.RESET_ALL}")
            continue
        if detail_index < detail_page:
            continue
        detail_page_text = get_page_with_playwright(detail_url, headers, scroll_count=0)
        detail_tree = etree.HTML(detail_page_text, parser=parser)
        detail_pic_list = detail_tree.xpath('//ul[@class="wookmark-initialised"]//li//a/@href')
        detail_title = detail_tree.xpath('//div[@class="title-section filters gallery"]/h1/text()')[0]
        save_file_path = os.path.join(a_name, detail_title)
        print(f'第{page}滚动的{detail_index}条数据{detail_title}共{len(detail_pic_list)}张图片')
        for pic_index, pic_url in enumerate(detail_pic_list):
            fileSize = download_image(pic_url, save_file_path, headers)
            if fileSize == "失败":
                download_fail_list.append({"title": detail_title, "pic": pic_url})
                print(f"{Fore.RED}下载失败:{download_fail_list}{Style.RESET_ALL}")
                continue
            print(pic_url, fileSize)
        print(f'{Fore.YELLOW}第{page}页的第{detail_index}条{detail_title}下载完毕{Style.RESET_ALL}')
        new_id = db.insert_url_custom(title=detail_title, url=detail_url, table_name="pornpics")
        print(f"{Fore.GREEN}新增记录成功，id：{new_id}{Style.RESET_ALL}")
        if pic_start_index != 0:
            print(f"第{page}页所有数据下载完毕，下载失败{download_fail_list}")
            exit(0)
        time.sleep(30)
    exit(0)
