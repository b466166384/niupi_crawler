import cfscrape
import requests
from colorama import Fore, Style
from lxml import etree
import os

from utils.common_utils import clean_windows_folder_name
from utils.mysqlite_util import DownloadFileDB
from utils.xunrennvshen_download import download_image_header, download_image_header_noname

if __name__ == '__main__':
    start_index = "10" #初始值是1
    pic_start_index = 6  #初始值是0
    pic_start_page = 0   #初始值是0  需要-2
    db_title = ""
    download_fail_list = []
    if not os.path.exists("../../file/jrants"):
        os.makedirs("../../file/jrants")
    a_name = os.path.abspath('../../file/jrants')
    print(f'总路径：{a_name}')
    db = DownloadFileDB()
    scraper = cfscrape.create_scraper()
    # scraper.verify = False
    custom_headers = {
        "Accept-Language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="144", "Chromium";v="144", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": '?0',
        "priority":"u=0, i",
        "referer":"https://jrants.com/",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "sec-fetch-dest":"document",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": '1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/143.0.0.1 Safari/537.37"
    }
    url = "https://jrants.com/category/korean/bimilstory/page/"
    content_url = url + start_index
    print(content_url)
    # 1. 获取原始字节数据（不要先转text）
    page_text = requests.get(url=content_url, headers=custom_headers).text
    parser = etree.HTMLParser(encoding="utf-8")
    tree = etree.HTML(page_text, parser=parser)
    pic_detail_url_list = tree.xpath('//article//div[@class="post-image"]//a/@href')
    pic_detail_url_list = list(dict.fromkeys(pic_detail_url_list))
    print(pic_detail_url_list )
    for detail_index, detail_param in enumerate(pic_detail_url_list):
        # 1. 跳过指定索引前的条目（原逻辑保留）
        if detail_index < pic_start_index:
            continue
        print(f"{Fore.YELLOW}pic_start_index:{detail_index}总{len(pic_detail_url_list)}{Style.RESET_ALL}")
        # 2. 构造详情页URL并解析页面
        detail_page_text = requests.get(url=detail_param, headers=custom_headers).text
        detail_tree = etree.HTML(detail_page_text, parser=parser)

        # 3. 解析标题、总页数（原逻辑保留）
        pic_url_list = detail_tree.xpath('//div[@class="entry-content"]//img/@src')
        print(pic_url_list)
        page_url_list = detail_tree.xpath('//a[@class="post-page-numbers"]/@href')
        if page_url_list:
            page_url_list = list(dict.fromkeys(page_url_list))
        title_list = detail_tree.xpath('//h1[@class="entry-title"]/text()')
        if title_list:
            org_title = str(title_list[0]).strip()
        else:
            org_title = f"{start_index}页{pic_start_index}条"
        title = clean_windows_folder_name(org_title)
        print(f"{title}")
        db_title = f"{title}"
        save_file_path = os.path.join(a_name, db_title)
        # ========== 关键调整1：提前判断是否已下载，优先跳过 ==========
        exact_result = db.get_by_title_custom(title=db_title, table_name="jrants")
        print(f"精确匹配结果：{exact_result}")
        if exact_result:
            print(f"{Fore.YELLOW}目录{save_file_path}已下载过了，跳过下载{Style.RESET_ALL}")
            continue  # 直接跳过当前条目的所有后续逻辑（包括下载、创建文件夹）

        # ========== 关键调整2：仅当未下载时，才创建文件夹 ==========
        if not os.path.exists(save_file_path):
            os.makedirs(save_file_path)
            print(f"创建保存路径：{save_file_path}")
        # 5. 下载第一页图片（原逻辑保留）
        show_page = 1
        if pic_start_page == 0:
            for index, img_url in enumerate(pic_url_list):
                imgUrl = str(img_url).replace("https:///", "https://")
                fileSize = download_image_header_noname(imgUrl, save_file_path, custom_headers)
                if fileSize == "失败":
                    fileSize2 = download_image_header_noname(imgUrl, save_file_path, custom_headers)
                    print(f"第{index + 1}张图片{fileSize2}下载完成，")
                    if fileSize2 == "失败":
                        my_map = {
                            "url": imgUrl,
                            "title": db_title
                        }
                        download_fail_list.append(my_map)
                        print(f"download_fail_list：{download_fail_list}")
                else:
                    print(f"第{index + 1}张图片{fileSize}下载完成")
        # ========== 关键调整3：多页下载逻辑归整，且已被跳过逻辑覆盖 ==========
        # 循环处理所有分页（原代码只处理了第二页，优化为循环更通用）
        max_page = len(page_url_list)
        print(f"{max_page}  {page_url_list}")
        if max_page >= 1:
            for page_index, page_param in enumerate(page_url_list):
                if page_index < pic_start_page:
                    continue
                page_url = f"{page_param}"
                print(f"{page_param}  {len(page_url_list)}")
                detail_page_text = requests.get(url=page_url, headers=custom_headers).text
                detail_tree = etree.HTML(detail_page_text, parser=parser)
                pic_url_list = detail_tree.xpath('//div[@class="entry-content"]//img/@src')
                print(pic_url_list)
                for index, img_url in enumerate(pic_url_list):
                    imgUrl = str(img_url).replace("https:///", "https://")
                    fileSize = download_image_header_noname(imgUrl, save_file_path, custom_headers)
                    if fileSize == "失败":
                        fileSize2 = download_image_header_noname(imgUrl,  save_file_path, custom_headers)
                        print(f"第{index + 1}张图片{fileSize2}下载完成，")
                        if fileSize2 == "失败":
                            my_map = {
                                "url": imgUrl,
                                "title": db_title
                            }
                            download_fail_list.append(my_map)
                    else:
                        print(f"第{index + 1}张图片{fileSize}下载完成")

        # 6. 下载完成后插入数据库（原逻辑保留）
        print(f"第{start_index}页的第{detail_index}条{db_title}下载完成")
        new_id = db.insert_custom(title=db_title, table_name="jrants")
        print(f"新增记录成功，id：{new_id}")
        if pic_start_page != 0:
           print(download_fail_list)
           exit(0)
    print(download_fail_list)




