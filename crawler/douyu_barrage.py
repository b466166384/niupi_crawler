import asyncio
import struct
import time
import sys
import ssl
import re
from colorama import Fore, Style, init

init(autoreset=True)
# cmd窗口启用方式 python crawler/douyu_barrage.py 房间号
# Fix Windows console encoding and disable buffering
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
else:
    sys.stdout.reconfigure(line_buffering=True)

RECONNECT_DELAY = 3
KEEPALIVE_INTERVAL = 40
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv


def create_ssl_context():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers('ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-GCM-SHA384')
    return ctx


def pack_message(content, msg_type=689):
    body = content.encode('utf-8') + b'\x00'
    total = 12 + len(body)
    length_field = total - 4
    return struct.pack('<II', length_field, length_field) + struct.pack('<I', msg_type) + body


def parse_binary_packets(data):
    offset = 0
    while offset + 12 <= len(data):
        pkt_len = struct.unpack('<I', data[offset:offset + 4])[0]
        total = 4 + pkt_len
        if offset + total > len(data):
            break
        msg_type = struct.unpack('<I', data[offset + 8:offset + 12])[0]
        body = data[offset + 12:offset + total]
        if body and body[-1] == 0:
            body = body[:-1]
        yield msg_type, body.decode('utf-8', errors='ignore')
        offset += total


def parse_kv(data_str):
    result = {}
    for pair in data_str.split('/'):
        idx = pair.find('@=')
        if idx != -1:
            result[pair[:idx]] = pair[idx + 2:]
    return result


def ts():
    return time.strftime('%H:%M:%S')


def handle_message(msg):
    mtype = msg.get('type', '')

    if mtype == 'chatmsg':
        name = msg.get('nn', '未知用户')
        text = msg.get('txt', '')
        level = int(msg.get('level', '1'))
        if level >= 80:
            color = Fore.MAGENTA
        elif level >= 40:
            color = Fore.YELLOW
        elif level >= 20:
            color = Fore.GREEN
        elif level >= 10:
            color = Fore.CYAN
        else:
            color = Fore.WHITE
        if not text:
            return
        print(f"[{Fore.BLUE}{ts()}{Style.RESET_ALL}] [{color}{name}{Style.RESET_ALL}]: {text}")

    elif mtype == 'dgb':
        name = msg.get('nn', '未知用户')
        gift = msg.get('giftName', '')
        hits = msg.get('hits', '1')
        print(f"[{Fore.BLUE}{ts()}{Style.RESET_ALL}] [{Fore.YELLOW}{name}{Style.RESET_ALL}] "
              f"赠送了 {Fore.MAGENTA}{gift}x{hits}{Style.RESET_ALL}")

    elif mtype == 'uenter':
        return

    elif mtype == 'spbc':
        name = msg.get('nn', '未知用户')
        text = msg.get('txt', '')
        print(f"[{Fore.BLUE}{ts()}{Style.RESET_ALL}] {Fore.RED}★ {name}{Style.RESET_ALL}: "
              f"{Fore.YELLOW}{text}{Style.RESET_ALL}")

    elif mtype == 'ssd':
        name = msg.get('nn', '未知用户')
        print(f"[{Fore.BLUE}{ts()}{Style.RESET_ALL}] {Fore.RED}★ {name} 上了套餐{Style.RESET_ALL}")

    elif mtype == 'onlinegift':
        name = msg.get('nn', '未知用户')
        gift = msg.get('giftName', '')
        print(f"[{Fore.BLUE}{ts()}{Style.RESET_ALL}] [{Fore.GREEN}{name}{Style.RESET_ALL}] "
              f"拾取了 {Fore.CYAN}{gift}{Style.RESET_ALL}")


async def keepalive_task(ws):
    while True:
        await asyncio.sleep(KEEPALIVE_INTERVAL)
        try:
            tick = int(time.time())
            await ws.send(pack_message(f"type@=mrkl/tick@={tick}/"))
        except Exception:
            break


async def connect_and_listen(room_id):
    import websockets
    from websockets.exceptions import ConnectionClosed
    ssl_ctx = create_ssl_context()
    urls = (
        [f'wss://danmuproxy.douyu.com:{p}/' for p in [8506, 8505, 8502, 8504, 8501, 8508]] +
        [f'wss://wsproxy.douyu.com:{p}/' for p in [6671, 6672, 6673, 6674, 6675]]
    )

    connected = False
    for url in urls:
        try:
            if not connected:
                print(f"{Fore.CYAN}[{ts()}] 连接 {url}...{Style.RESET_ALL}")
            async with websockets.connect(url, max_size=2 ** 20, ssl=ssl_ctx, open_timeout=5,
                                           ping_interval=None, ping_timeout=None) as ws:
                if not connected:
                    print(f"{Fore.GREEN}[{ts()}] 连接成功! ({url}){Style.RESET_ALL}")
                connected = True

                await ws.send(pack_message(f"type@=loginreq/roomid@={room_id}/"))
                await ws.send(pack_message(f"type@=joingroup/rid@={room_id}/gid@=-9999/"))

                keepalive_fut = asyncio.ensure_future(keepalive_task(ws))

                try:
                    data = await asyncio.wait_for(ws.recv(), timeout=5)
                    for mt, body in parse_binary_packets(data):
                        if VERBOSE:
                            msg = parse_kv(body)
                            t = msg.get('type', '?')
                            print(f"[{ts()}] [{t}] {body[:200]}")
                except asyncio.TimeoutError:
                    pass
                print(f"{Fore.GREEN}[{ts()}] 已连接，开始接收弹幕{Style.RESET_ALL}")

                print("-" * 60)

                msg_count = 0
                try:
                    async for data in ws:
                        if isinstance(data, bytes):
                            for mt, body in parse_binary_packets(data):
                                if mt == 690 and body:
                                    msg = parse_kv(body)
                                    mtype = msg.get('type', '')
                                    if mtype == 'pingreq':
                                        tick = msg.get('tick', str(int(time.time())))
                                        await ws.send(pack_message(f"type@=pongreply/tick@={tick}/"))
                                    elif mtype in ('chatmsg', 'dgb', 'uenter', 'spbc', 'ssd', 'onlinegift'):
                                        handle_message(msg)
                                        if mtype == 'chatmsg':
                                            msg_count += 1
                                    elif VERBOSE:
                                        body_preview = body[:100].replace('\n', ' ')
                                        print(f"[{Fore.BLUE}{ts()}{Style.RESET_ALL}] {Fore.YELLOW}[{mtype}]{Style.RESET_ALL} {body_preview}")
                except ConnectionClosed:
                    print(f"\n{Fore.RED}[{ts()}] 连接已断开 (共接收 {msg_count} 条弹幕){Style.RESET_ALL}")
                finally:
                    keepalive_fut.cancel()
                break
        except Exception as e:
            if not connected:
                err = str(e)[:50]
                print(f"  {Fore.RED}失败: {err}{Style.RESET_ALL}")
            continue

    if not connected:
        raise ConnectionError("所有服务器均连接失败")


async def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print("用法: python douyu_barrage.py [room_id] [-v]")
        print("  room_id  直播间号或URL (默认 11222)")
        print("  -v       显示所有消息类型")
        return

    arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else "11222"
    m = re.search(r'(\d{4,10})', arg)
    room_id = m.group(1) if m else arg
    try:
        from dyproto.discovery import resolve_room_id
        resolved = resolve_room_id(room_id)
        if str(resolved) != str(room_id):
            print(f"[{ts()}] 房间 {room_id} -> 实际房间 {resolved}")
            room_id = str(resolved)
    except Exception:
        pass
    while True:
        try:
            await connect_and_listen(room_id)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"{Fore.RED}[{ts()}] 错误: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[{ts()}] {RECONNECT_DELAY}秒后重连...{Style.RESET_ALL}")
            await asyncio.sleep(RECONNECT_DELAY)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}已断开连接{Style.RESET_ALL}")
        sys.exit(0)
