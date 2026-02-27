import requests
from colorama import Fore, Style
from lxml import etree
import re
import os

from utils.mysqlite_util import DownloadFileDB
from utils.xunrennvshen_download import download_image
# 110页开始是2023年数据
# Press the green button in the gutter to run the script.


if __name__ == '__main__':
    start_index = "1"
    # 设置从当前页面第几条数据开始
    pic_start_index = 0
    yearInt = 0
    db_title = ""
    download_fail_list = []
    if not os.path.exists("../../file/美女图集"):
        os.makedirs("../../file/美女图集")
    a_name = os.path.abspath('../../file/美女图集')
    print(f'总路径：{a_name}')
    db = DownloadFileDB()
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        "Referer": "https://www.xsnvshen.co/",
        "Connection": "close",
        "cookie":"__vtins__JNmoBsk0I91IZLwU=%7B%22sid%22%3A%20%2255f4d8ca-4d36-56b5-bfee-59bd64e24b88%22%2C%20%22vd%22%3A%201%2C%20%22stt%22%3A%200%2C%20%22dr%22%3A%200%2C%20%22expires%22%3A%201760578782682%2C%20%22ct%22%3A%201760576982682%7D; __51uvsct__JNmoBsk0I91IZLwU=1; __51vcke__JNmoBsk0I91IZLwU=2fa8de4c-5f2f-5320-9a63-e7e5bbf15345; __51vuft__JNmoBsk0I91IZLwU=1760576982685; jpx=2; gcha_sf=1760577006; __vtins__JNmlfXHHIrHMZgLq=%7B%22sid%22%3A%20%22a91e98ec-da07-596f-89b2-4ab8f7d3d01e%22%2C%20%22vd%22%3A%201%2C%20%22stt%22%3A%200%2C%20%22dr%22%3A%200%2C%20%22expires%22%3A%201760578809428%2C%20%22ct%22%3A%201760577009428%7D; __51uvsct__JNmlfXHHIrHMZgLq=1; __51vcke__JNmlfXHHIrHMZgLq=1648fc20-71c2-5b0f-b756-ef835b039bb0; __51vuft__JNmlfXHHIrHMZgLq=1760577009430"
    }
    FULL_HEADERS = {
        "sec-ch-ua": 'Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141',
        "sec-ch-ua-mobile": '?0',
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": '1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    }
    url = "https://www.xsnvshen.co/album/hd/?p="
    baseUrl = "https://www.xsnvshen.co"
    page_text = requests.get(url=url+start_index, headers=headers).text
    #print(page_text)
    parser = etree.HTMLParser(encoding="utf-8")
    tree = etree.HTML(page_text, parser=parser)
    page_num_div = tree.xpath('//div[@id="pageNum"]//a/@data-page')
    # 将字符串转换为整数
    int_list = [int(num) for num in page_num_div]
    # 获取最大值
    max_num = max(int_list)
    print("最大页数-->"+str(max_num))
    pic_content = tree.xpath('//ul[@class="picpos_6_1 layout camWholeBoxUl"]//li/a/@href')
    print("图片详情url-->" + str(pic_content))
    for detail_index, detail_param in enumerate(pic_content):
        if pic_start_index != 0:
            if detail_index <pic_start_index :
                continue
        print("---------------------------------------------------------------------------------------------------------------------------------")
        detail_url = baseUrl+detail_param
        print(f'{Fore.MAGENTA}第{detail_index}角标{detail_url}开始下载{Style.RESET_ALL}')
        detail_page_text = requests.get(url=detail_url, headers=headers).text
        # print(page_text)
        detail_parser = etree.HTMLParser(encoding="utf-8")
        detail_tree = etree.HTML(detail_page_text, parser=detail_parser)
        title = detail_tree.xpath('//div[@class="swp-tit layout"]//h1/a')[0].text
        print("写真名称->"+title)
        pattern = r'\b\d{4}\b'
        # 查找匹配的年份
        match = re.search(pattern, title)
        if match:
            year = match.group()  # 获取匹配到的年份字符串
            yearInt = int(year)
            print(f"提取到的年份：{year}")  # 输出：提取到的年份：2025
        time_div = detail_tree.xpath('//em[@id="time"]//span')[0].text
        # 使用正则表达式提取数字
        # \d+ 匹配一个或多个数字
        match = re.search(r'\d+', time_div)
        pic_num = match.group()
        # print("一共多少张->"+pic_num)
        pic_url = detail_tree.xpath('//img[@id="bigImg"]/@src')[0]
        # print(pic_url)
        base_pic_url = pic_url.split('000.jpg')[0]
        pic_list = []
        for i in range(int(pic_num)):
            formatted_i = f"{i:03d}"  # 关键：03d 表示至少3位，不足补0
            u = f"{base_pic_url}{formatted_i}.jpg"
            pic_list.append(u)
        print(pic_list)
        db_title = f"{title}【{pic_num}】"
        # 创建图片保存目录
        save_file_path = os.path.join(a_name, db_title)
        exact_result = db.get_by_title_and_year(title=db_title, year=yearInt)
        print(f"精确匹配结果：{exact_result}")
        if exact_result:
            print(f"{Fore.YELLOW}目录{save_file_path}已下载过了，跳过下载{Style.RESET_ALL}")
            continue

        # if os.path.exists(save_file_path):
        #     print(f"{Fore.YELLOW}目录{save_file_path}已下载过了，跳过下载{Style.RESET_ALL}")
        #     continue
        if not os.path.exists(save_file_path):
            os.makedirs(save_file_path)
        # print("保存路径->"+save_file_path)
        # 下载图片
        for index, img_url in enumerate(pic_list):
            fileSize = download_image(img_url, save_file_path)
            if fileSize == "失败":
                fileSize2 = download_image(img_url, save_file_path)
                print(f"第{index + 1}张图片{fileSize2}下载完成，一共{pic_num}张")
                if fileSize2 =="失败":
                    my_map = {
                        "url": 'https:'+img_url,
                        "title": db_title
                    }
                    download_fail_list.append(my_map)
            else:
                print(f"第{index + 1}张图片{fileSize}下载完成，一共{pic_num}张")
        print(f'第{start_index}页的第{detail_index}角标{detail_param}下载完毕，{title}')
        new_id = db.insert(title=db_title, year=yearInt)
        print(f"新增记录成功，id：{new_id}")
    print(f"{Fore.GREEN}第{start_index}页内容全部下载完成{Style.RESET_ALL}")
    print(download_fail_list)