import cfscrape
import requests
from colorama import Fore, Style
from lxml import etree
import os
from utils.mysqlite_util import DownloadFileDB
from utils.xunrennvshen_download import download_image_header

if __name__ == '__main__':
    # 设置开始的页数 第一页从1开始
    start_index = "2"
    pic_start_index = 0  #初始值0
    pic_start_page = 2   #初始值是2
    yearInt = 0
    db_title = ""
    download_fail_list = []
    if not os.path.exists("../../file/hitxhot"):
        os.makedirs("../../file/hitxhot")
    a_name = os.path.abspath("../../file/hitxhot")
    print(f'总路径：{a_name}')
    db = DownloadFileDB()
    scraper = cfscrape.create_scraper()
    # scraper.verify = False
    custom_headers = {
        "Accept-Language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": 'Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141',
        "sec-ch-ua-mobile": '?0',
        "priority":"u=0, i",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "sec-fetch-dest":"document",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": '1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Cookie":"showed_adscarat_shuffle_box=1; _ga=GA1.1.48770455.1766460258; ck_theme=light; clicked_cpt_437=1; clicked_cpt_453=1; clicked_cpt_482=1; clicked_cpt_477=1; clicked_cpt_473=1; clicked_cpt_449=1; clicked_cpc_137=1; cf_clearance=MyVeuv_VKQt.ljnMEGgA9hwcnMq6ftyVqDTdFXTxRG8-1766472851-1.2.1.1-zXV9C0iCBCsyTEqj1YjmERKryMlxXMG0nn0wigq3vLClFt8WT_Ngbr6Dou57PhdcBsLYU_ey1pshBflIjqg3GL2sd7HWQQ.G6rvj5cdYKm83ZRTM1V66SC7RPIqJYHQdQW8lKcM.YmiUXSaycaQ21Mdo4HIVTLrMMGSRjnsxEjBZLMcJ1W7OlpeEogOyrZcaec.a4iJwYyFw6TpkSOiZ1uas5bKyPDk7VmImzQQbAWE; clicked_modal=1; pv_punch_pc=%7B%22count%22%3A17%2C%22expiry%22%3A1766546657%7D; _ga_F0JXM9DQXX=GS2.1.s1766472852$o3$g1$t1766472880$j32$l0$h0"
    }

    url = "https://www.hitxhot.org/?page="
    base_url = "https://www.hitxhot.org"
    pic_base_url = "https://img.xchina.io/photos2/"
    content_url = url + start_index
    print(content_url)
    # 1. 获取原始字节数据（不要先转text）
    page_text = requests.get(url=content_url, headers=custom_headers).text
    parser = etree.HTMLParser(encoding="utf-8")
    tree = etree.HTML(page_text, parser=parser)
    pic_detail_url_list = tree.xpath('//div[@class="VMUVXRX KMGJFDUMW"]//a/@href')
    pic_detail_url_list = list(dict.fromkeys(pic_detail_url_list))
    print(pic_detail_url_list )
    for detail_index, detail_param in enumerate(pic_detail_url_list):
        # 1. 跳过指定索引前的条目（原逻辑保留）
        if detail_index < pic_start_index:
            continue
        print(f"{Fore.YELLOW}pic_start_index:{pic_start_index}{Style.RESET_ALL}")
        # 2. 构造详情页URL并解析页面
        detail_url = base_url + detail_param
        detail_page_text = requests.get(url=detail_url, headers=custom_headers).text
        detail_tree = etree.HTML(detail_page_text, parser=parser)

        # 3. 解析标题、总页数（原逻辑保留）
        pic_url_list = detail_tree.xpath('//div[@class="VKSUBTSWA contentme"]//a//img/@src')
        title_list = detail_tree.xpath('//article[@class="BRBOVJR"]//h1/text()')
        total_page = str(title_list[0]).split("/")[1]
        title = str(title_list[0]).split("|")[0].replace("Hit-x-Hot:", "").strip()
        db_title = f"{title}"
        save_file_path = os.path.join(a_name, db_title)

        # ========== 关键调整1：提前判断是否已下载，优先跳过 ==========
        exact_result = db.get_by_title_custom(title=db_title, table_name="hitxhot")
        print(f"精确匹配结果：{exact_result}")
        if exact_result:
            print(f"{Fore.YELLOW}目录{save_file_path}已下载过了，跳过下载{Style.RESET_ALL}")
            continue  # 直接跳过当前条目的所有后续逻辑（包括下载、创建文件夹）

        # ========== 关键调整2：仅当未下载时，才创建文件夹 ==========
        if not os.path.exists(save_file_path):
            os.makedirs(save_file_path)
            print(f"创建保存路径：{save_file_path}")

        # 4. 打印基础信息（原逻辑保留）
        print(pic_url_list)
        print(f"{title}   {total_page}")
        print(detail_url)

        # 5. 下载第一页图片（原逻辑保留）
        show_page = 1
        if pic_start_page == 2:
            for index, img_url in enumerate(pic_url_list):
                file_name = f"{show_page}_{index}"
                imgUrl = str(img_url).replace("i2.wp.com/", "")
                fileSize = download_image_header(imgUrl, file_name, save_file_path, custom_headers)
                if fileSize == "失败":
                    fileSize2 = download_image_header(imgUrl, file_name, save_file_path, custom_headers)
                    print(f"第{index + 1}张图片{fileSize2}下载完成，")
                    if fileSize2 == "失败":
                        my_map = {
                            "url": imgUrl,
                            "title": db_title
                        }
                        download_fail_list.append(my_map)
                        print(download_fail_list)
                else:
                    print(f"第{index + 1}张图片{fileSize}下载完成")
        # ========== 关键调整3：多页下载逻辑归整，且已被跳过逻辑覆盖 ==========
        # 循环处理所有分页（原代码只处理了第二页，优化为循环更通用）
        max_page = int(total_page)
        if max_page > 1:
            for show_page in range(pic_start_page, max_page + 1):
                page_url = f"{detail_url}?page={show_page}"
                print(page_url+"    "+str(total_page))
                detail_page_text = requests.get(url=page_url, headers=custom_headers).text
                detail_tree = etree.HTML(detail_page_text, parser=parser)
                pic_url_list = detail_tree.xpath('//div[@class="VKSUBTSWA contentme"]//a//img/@src')
                print(pic_url_list)
                for index, img_url in enumerate(pic_url_list):
                    file_name = f"{show_page}_{index}"
                    imgUrl = str(img_url).replace("i2.wp.com/", "")
                    fileSize = download_image_header(imgUrl, file_name, save_file_path, custom_headers)
                    if fileSize == "失败":
                        fileSize2 = download_image_header(imgUrl, file_name, save_file_path, custom_headers)
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
        print(f"第{pic_start_index}页的第{detail_index}条{db_title}下载完成")
        new_id = db.insert_custom(title=db_title, table_name="hitxhot")
        print(f"新增记录成功，id：{new_id}")
        if pic_start_page != 2:
           print(download_fail_list)
           exit(0)
    print(download_fail_list)




