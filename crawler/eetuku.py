import requests
import os
import sys
from colorama import Fore, Style
from lxml import etree

sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from DownloadFileDB import DownloadFileDB
from ImageDownloader import download_image
import time

def process_detail_page(detail_url, base_url, headers, a_name, pic_start_index, download_fail_list):
    parser = etree.HTMLParser(encoding="utf-8")
    detail_url = base_url + detail_url
    detail_page_text = requests.get(url=detail_url, headers=headers).text
    detail_tree = etree.HTML(detail_page_text, parser=parser)
    detail_title = detail_tree.xpath('//div[@class="inside-article"]//h1[@class="entry-title"]/text()')[0]
    file_date = detail_tree.xpath('//div[@class="entry-meta"]//time[@class="entry-date published"]/text()')[0]
    detail_title = f"{detail_title} ({file_date})"
    pic_list = detail_tree.xpath('//div[@class="inside-article"]//img/@data-src')
    pic_list = [pic for pic in pic_list if '260x390' not in pic]
    print(f"标题:{detail_title},详情页:{detail_url},共{len(pic_list)}张图片")
    save_file_path = os.path.join(a_name, detail_title)
    for pic_index, pic in enumerate(pic_list):
        if pic_index < pic_start_index:
            continue
        fileSize = download_image(pic, save_file_path, headers)
        if fileSize == "失败":
            download_fail_list.append({"title": detail_title, "pic": pic})
            print(f"{Fore.RED}下载失败:{download_fail_list}{Style.RESET_ALL}")
            continue
        print(pic, fileSize)


if __name__ == '__main__':
    page = 4 #初始值1
    detail_page = 0 #初始值0
    pic_start_index = 0 #初始值0
    download_fail_list = []
    headers = {
        "Accept": "text/html, application/xhtml+xml, application/xml;q=0.9, image/webp, image/apng, application/json, text/plain; q=0.8",
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        "Referer": "https://www.eetuku.com/category/hanguo",
    }
    base_url = "https://www.eetuku.com/"
    url = f'https://www.eetuku.com/category/hanguo/page/{page}'
    if not os.path.exists("./downloadFile/eetuku"):
        os.makedirs("./downloadFile/eetuku")
    a_name = os.path.abspath('./downloadFile/eetuku')
    print(a_name)
    db = DownloadFileDB()
    # pic_list = ['https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216331.webp', 'https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216332.webp', 'https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216333.webp', 'https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216334.webp', 'https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216335.webp', 'https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216336.webp', 'https://i5.ggcos.com/amazonlove/wp-content/uploads/2026/04/04/31505041216337.webp']
    page_text = requests.get(url=url, headers=headers).text
    parser = etree.HTMLParser(encoding="utf-8")
    tree = etree.HTML(page_text, parser=parser)
    detail_list = tree.xpath('//article//div[@class="post-image"]//a/@href')
    print(f"第{page}页,共{len(detail_list)}条数据",f"{detail_list}")
    for detail_index, detail_url in enumerate(detail_list):
        if detail_index < detail_page:
            continue
        detail_url = base_url + detail_url
        detail_page_text = requests.get(url=detail_url, headers=headers).text
        detail_tree = etree.HTML(detail_page_text, parser=parser)
        detail_title = detail_tree.xpath('//div[@class="inside-article"]//h1[@class="entry-title"]/text()')[0]
        file_date = detail_tree.xpath('//div[@class="entry-meta"]//time[@class="entry-date published"]/text()')[0]
        detail_title = f"{detail_title} ({file_date})"
        exact_result = db.get_by_title_custom(title=detail_title, table_name="eetuku")
        print(f"精确匹配结果：{exact_result}")
        if exact_result:
            print(f"{Fore.GREEN}目录{detail_title}已下载过了，跳过下载{Style.RESET_ALL}")
            continue
        pic_list = detail_tree.xpath('//div[@class="inside-article"]//img/@data-src')
        pic_list = [pic for pic in pic_list if '260x390' not in pic]
        print(f"标题:{detail_title},详情页:{detail_url},共{len(pic_list)}张图片")
        save_file_path = os.path.join(a_name, detail_title)
        for pic_index, pic in enumerate(pic_list):
            if pic_index < pic_start_index:
                continue
            print(f"第{pic_index}张图片:")
            fileSize = download_image(pic, save_file_path, headers)
            if fileSize == "失败":
                download_fail_list.append({"title": detail_title, "pic": pic})
                print(f"{Fore.RED}下载失败:{download_fail_list}{Style.RESET_ALL}")
                continue
            print(pic, fileSize)
        page_links = detail_tree.xpath('//div[@class="page-links"]')
        if page_links:
            print(f"发现分页标签，跳过该详情页")
            page_links = detail_tree.xpath('//div[@class="page-links"]//a/@href')
            for page_link in page_links:
                process_detail_page(page_link, base_url, headers, a_name, pic_start_index, download_fail_list)
        print(f'{Fore.YELLOW}第{page}页的第{detail_index}条{detail_title}下载完毕{Style.RESET_ALL}')
        new_id = db.insert_custom(title=detail_title, table_name="eetuku")
        print(f"{Fore.GREEN}新增记录成功，id：{new_id}{Style.RESET_ALL}")
        if pic_start_index != 0:
            print(f"第{page}页所有数据下载完毕，下载失败{download_fail_list}")
            exit(0)
        time.sleep(30)
    print(f"第{page}页所有数据下载完毕，下载失败{download_fail_list}")
    exit(0)
