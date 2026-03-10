import os
import re
import requests
import subprocess
import shutil
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

# 配置项
M3U8_URL = "https://media.knit.bid/play/43e63d8538cd6e15.m3u8"  # M3U8 文件地址
SAVE_DIR = "./downloads"  # 保存目录
MAX_THREADS = 10  # 并发下载线程数
FFMPEG_PATH = "ffmpeg"  # ffmpeg 可执行文件路径
MAX_RETRIES = 3  # 最大重试次数


def create_dir(path):
    """创建目录"""
    if not os.path.exists(path):
        os.makedirs(path)


def download_file_with_retry(url, save_path, headers=None, max_retries=MAX_RETRIES):
    """带重试机制的文件下载（最多重试max_retries次）"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=90)
            response.raise_for_status()  # 抛出 HTTP 错误
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB 分片写入
                    if chunk:
                        f.write(chunk)
            # print(f"下载成功 {url}（第{attempt}次尝试）")
            return True
        except Exception as e:
            # 删除可能存在的不完整文件
            if os.path.exists(save_path):
                os.remove(save_path)
            # 判断是否还有重试机会
            if attempt < max_retries:
                print(f"第{attempt}次下载失败 {url}：{str(e)}，将重试...")
            else:
                print(f"已达最大重试次数（{max_retries}次），下载失败 {url}：{str(e)}")
    return False


def parse_m3u8(m3u8_content, base_url):
    """解析 M3U8 内容，提取 TS 分片地址"""
    ts_urls = []
    # 匹配 TS 分片地址（支持相对路径和绝对路径）
    pattern = re.compile(r'^[^#].*?\.ts', re.MULTILINE)
    for line in pattern.findall(m3u8_content):
        # 拼接完整 URL（如果是相对路径）
        ts_url = urljoin(base_url, line.strip())
        ts_urls.append(ts_url)
    return ts_urls


# def merge_ts(ts_dir, output_path):
#     """用 ffmpeg 合并 TS 文件为 MP4"""
#     try:
#         # 获取所有 TS 文件并按名称排序（确保顺序正确）
#         ts_files = sorted([f for f in os.listdir(ts_dir) if f.endswith(".ts")])
#         if not ts_files:
#             print("没有找到 TS 分片文件，合并失败")
#             return False
#
#         # 创建 TS 文件列表文本（ffmpeg 需要按顺序读取）
#         ts_list_path = os.path.join(ts_dir, "ts_list.txt")
#         with open(ts_list_path, "w", encoding="utf-8") as f:
#             for ts_file in ts_files:
#                 f.write(f"file '{os.path.join(ts_dir, ts_file)}'\n")
#
#         # 调用 ffmpeg 合并（-c copy 表示直接复制流，不重新编码，速度快）
#         cmd = [
#             FFMPEG_PATH,
#             "-f", "concat",  # 按列表拼接
#             "-safe", "0",    # 允许绝对路径
#             "-i", ts_list_path,
#             "-c", "copy",    # 不重新编码
#             "-y",            # 覆盖已有文件
#             output_path
#         ]
#         # 执行命令并捕获输出（出错时会抛出异常）
#         result = subprocess.run(
#             cmd,
#             check=True,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )
#         print(f"合并成功，保存到：{output_path}")
#         return True
#     except subprocess.CalledProcessError as e:
#         print(f"FFmpeg 执行失败：{e.stderr}")  # 输出 FFmpeg 的错误信息
#         return False
#     except Exception as e:
#         print(f"合并失败：{str(e)}")
#         return False


def merge_ts(ts_dir, output_path):
    """用 ffmpeg 合并 TS 文件为 MP4"""
    try:
        # 获取所有 TS 文件并按名称排序（确保顺序正确）
        ts_files = sorted([f for f in os.listdir(ts_dir) if f.endswith(".ts")])
        if not ts_files:
            print("没有找到 TS 分片文件，合并失败")
            return False

        # 创建 TS 文件列表文本（ffmpeg 需要按顺序读取）
        ts_list_path = os.path.join(ts_dir, "ts_list.txt")
        with open(ts_list_path, "w", encoding="utf-8") as f:
            for ts_file in ts_files:
                f.write(f"file '{os.path.join(ts_dir, ts_file)}'\n")

        # 调用 ffmpeg 合并（-c copy 表示直接复制流，不重新编码，速度快）
        cmd = [
            FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", ts_list_path,
            "-c", "copy",
            "-y",
            output_path
        ]
        # 关键修改：stdout和stderr用subprocess.PIPE（二进制），不指定text=True
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE  # 二进制模式，不解码
        )
        # 如需打印日志，可手动指定编码解码（忽略错误）
        print(f"FFmpeg 输出：{result.stderr.decode('utf-8', errors='ignore')}")
        print(f"合并成功，保存到：{output_path}")
        return True
    except subprocess.CalledProcessError as e:
        # 错误信息同样用二进制解码，忽略错误
        error_msg = e.stderr.decode('utf-8', errors='ignore')
        print(f"FFmpeg 执行失败：{error_msg}")
        return False
    except Exception as e:
        print(f"合并失败：{str(e)}")
        return False

def download_m3u8(m3u8_url, save_dir, file_name,header):
    """下载 M3U8 视频主函数"""
    # 1. 创建保存目录
    ts_dir = os.path.join(save_dir, "ts_chunks")  # 存放 TS 分片
    create_dir(ts_dir)
    create_dir(save_dir)  # 确保最终视频保存目录存在

    # 2. 下载 M3U8 文件
    print(f"正在下载 M3U8 文件：{m3u8_url}")
    headers = header
    try:
        response = requests.get(m3u8_url, headers=headers, timeout=10)
        response.raise_for_status()
        m3u8_content = response.text
    except Exception as e:
        print(f"下载 M3U8 文件失败：{str(e)}")
        return

    # 3. 解析 M3U8，获取 TS 分片地址
    ts_urls = parse_m3u8(m3u8_content, m3u8_url)
    if not ts_urls:
        print("未找到 TS 分片地址")
        return

    print(f"发现 {len(ts_urls)} 个 TS 分片，开始下载（最多重试{MAX_RETRIES}次）...")

    # 4. 并发下载 TS 分片（带重试）
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        # 存储分片信息（用于后续重试）
        ts_info_list = [
            (ts_url, os.path.join(ts_dir, f"chunk_{i:04d}.ts"))
            for i, ts_url in enumerate(ts_urls)
        ]

        # 第一次批量下载
        for ts_url, ts_save_path in ts_info_list:
            futures.append(executor.submit(
                download_file_with_retry,
                ts_url,
                ts_save_path,
                headers
            ))

        # 收集失败的分片
        failed_ts = [
            (ts_info_list[i][0], ts_info_list[i][1])
            for i, future in enumerate(futures)
            if not future.result()
        ]

    # 5. 如果有失败的分片，单独再次重试（避免并发冲突）
    if failed_ts:
        print(f"存在 {len(failed_ts)} 个分片下载失败，开始单独重试...")
        for ts_url, ts_save_path in failed_ts:
            # 这里使用单线程重试，避免再次并发导致的问题
            download_file_with_retry(ts_url, ts_save_path, headers)

        # 最终检查仍失败的分片
        final_failed = [
            ts_url for ts_url, ts_save_path in failed_ts
            if not os.path.exists(ts_save_path)
        ]
        if final_failed:
            print(f"最终仍有 {len(final_failed)} 个分片失败，可能影响视频完整性：")
            for url in final_failed[:5]:  # 只打印前5个
                print(f"  - {url}")
        else:
            print("所有失败分片重试成功")

    # 6. 合并 TS 分片为 MP4
    output_file = os.path.join(save_dir, f"{file_name}.mp4")  # 最终视频文件
    merge_ts(ts_dir, output_file)

    # 7. 清理 TS 分片目录
    shutil.rmtree(ts_dir, ignore_errors=True)
    print("清理临时文件完成")


# 示例调用
