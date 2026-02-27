import os

import requests
from colorama import Fore, Style
from pymysql.constants.FLAG import NOT_NULL

from utils.mysqlite_util import DownloadFileDB
from playwright.sync_api import sync_playwright
from playwright.sync_api import Page  # 用于类型提示
from lxml import etree

from utils.video_download import download_m3u8
from utils.xunrennvshen_download import download_image_aimeizi

# 测试地址/article/30121/
def set_local_storage(page: Page, key: str, value: str):
    """向页面注入 localStorage 数据"""
    page.evaluate(f"localStorage.setItem('{key}', '{value}');")
    # 验证是否设置成功
    stored_value = page.evaluate(f"return localStorage.getItem('{key}');")
    if stored_value != value:
        raise Exception(f"设置 localStorage {key} 失败，实际值: {stored_value}")

def downloadPic(save_file_path:str,b_url:str,pic_list: list[str], download_fail_list: list[dict]) -> list[dict]:
    for index, img_url in enumerate(pic_list):
        print("下载地址："+b_url+img_url)
        fileSize = download_image_aimeizi(b_url+img_url, save_file_path,custom_headers)
        if fileSize == "失败":
            fileSize2 = download_image_aimeizi(b_url+img_url, save_file_path,custom_headers)
            print(f"第{index + 1}张图片{fileSize2}下载完成")
            if fileSize2 == "失败":
                fail_info = {
                    "url": b_url+img_url,
                    "title": save_file_path
                }
                download_fail_list.append(fail_info)
        else:
            print(f"第{index + 1}张图片{fileSize}下载完成")
    # 循环完成后返回失败列表
    return download_fail_list

if __name__ == '__main__':
    # 配置参数
    start_index = "10"  # 开始页数（第一页从0开始，这里根据实际情况调整）
    detail_start_index = 0 #jiaobiao
    pic_start_index = 1   # 从详情里的第几页开始
    # 创建保存目录
    save_dir = "../../file/爱妹子"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    abs_save_dir = os.path.abspath(save_dir)
    print(f'文件保存路径：{abs_save_dir}')

    # 初始化数据库
    db = DownloadFileDB()

    # 目标URL
    base_url = "https://xx.knit.bid"
    url = "https://xx.knit.bid/type/9/page/"
    target_url = f"{url}{start_index}/"
    print(f'目标页面URL：{target_url}')
    # 从抓包中提取的请求头（关键字段）
    custom_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Sec-Ch-Ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Referer": "https://xx.knit.bid/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }
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
            # 创建页面并设置自定义请求头
            page = browser.new_page(
                extra_http_headers=custom_headers,
                # 自动携带Cookie（Playwright会自动处理抓包中的Cookie）
                bypass_csp=True  # 可选：绕过内容安全策略，避免请求被拦截
            )
            # 1. 先访问页面域名（确保localStorage作用域正确）
            page.goto(target_url, timeout=240000)  # 访问基础域名，初始化上下文
            # 2. 设置localStorage（在目标页面加载前注入）
            page.evaluate("localStorage.setItem('agreed18', '1');")  # 写入同意状态
            print("已设置 localStorage.agreed18 = '1'")
            page.wait_for_timeout(1000)  # 1000毫秒 = 1秒
            page.goto(target_url, timeout=240000)  # 等待网络空闲（确保页面加载完成）

            # 4. 可选：等待关键元素出现，确认弹窗已被跳过
            # 例如：等待列表内容加载（根据实际页面调整选择器）
            # page.wait_for_selector("div.post-list", timeout=10000)  # 10秒超时
            # print("页面关键内容已加载，未检测到弹窗阻塞")

            # 5. 获取页面内容
            page_content = page.content()
            parser = etree.HTMLParser(encoding="utf-8")
            tree = etree.HTML(page_content, parser=parser)
            detail_link = tree.xpath('//div[@id="image-gallery"]//a[@class="imgbox imgbox-link"]/@href')
            title_list = tree.xpath('//div[@id="image-gallery"]//a[@class="imgbox imgbox-link"]/@title')
            print(detail_link)
            time_list = tree.xpath('//a[@class="post-like"]//time/text()')
            print(time_list)
            download_fail_list = []
            sliced_links = detail_link[detail_start_index:]
            for detail_index, detail_param in enumerate(sliced_links,start=detail_start_index):
                print(f"{Fore.YELLOW}开始第{detail_index}角标{detail_param}内容{Style.RESET_ALL}")
                detail_url = base_url + detail_param
                file_name = f'{time_list[detail_index]} {title_list[detail_index]}'
                pic_detail_url = ""
                # 创建图片保存目录
                save_file_path = os.path.join(abs_save_dir, file_name)
                if not os.path.exists(save_file_path):
                    os.makedirs(save_file_path)
                exact_result = db.get_by_title_custom(title=file_name, table_name="aimeizi")
                if exact_result:
                    print(f"{Fore.YELLOW}目录{file_name}已下载过了，跳过下载{Style.RESET_ALL}")
                    continue
                page.goto(detail_url, timeout=240000)
                detail_page_content = page.content()
                detail_tree = etree.HTML(detail_page_content, parser=parser)
                last_page_str = detail_tree.xpath(
                    '//ul[@class="pagination"]//li[not(contains(@class, "next-page"))]//a/@data-page')[-1]
                last_page = int(last_page_str)
                for i in range(pic_start_index, last_page + 1):
                    print(f'{Fore.GREEN}第{detail_index}开始{detail_param}，当前下载到{i}页，共{last_page}页{Style.RESET_ALL}')
                    if i == 1:
                        pic_detail_url = detail_url
                        video_list = detail_tree.xpath('//div[@class="wrapper"]//video//source/@src')
                        print(f'第{i}页视频有{len(video_list)}个')
                        if video_list is not None and len(video_list) > 0:
                            for k in range(len(video_list)):
                                download_m3u8(video_list[k], save_file_path, f'video{i}_{k}', custom_headers)
                    else:
                        pic_detail_url = f'{detail_url}page/{i}/'
                        # detail_page_text = requests.get(url=pic_detail_url, headers=custom_headers).text
                        # detail_parser = etree.HTMLParser(encoding="utf-8")
                        # detail_tree = etree.HTML(detail_page_text, parser=detail_parser)
                        page.goto(pic_detail_url, timeout=240000)
                        detail_page_content = page.content()
                        detail_tree = etree.HTML(detail_page_content, parser=parser)
                    pic_list = detail_tree.xpath('//div[@class="image-container"]//p[@class="item-image"]/img/@data-src')
                    print(f'第{i}页图片有{len(pic_list)}张')
                    if pic_list is not None and len(pic_list) > 0:
                        download_fail_list = downloadPic(save_file_path,base_url,pic_list, download_fail_list)
                if pic_start_index != 1:
                    pic_start_index =1
                new_id = db.insert_custom(title=file_name,table_name="aimeizi")
                print(f"新增记录成功，id：{new_id}")
                print(f"{Fore.GREEN}{file_name}内容全部下载完成{Style.RESET_ALL}")
                if len(download_fail_list) >= 1:
                    print(f"{Fore.RED}{download_fail_list}{Style.RESET_ALL}")

        except Exception as e:
            print(f"操作失败：{str(e)}")
        finally:
            # 确保浏览器关闭
            if 'browser' in locals():
                browser.close()
            # 关闭数据库连接（如果需要）
            # db.close()





