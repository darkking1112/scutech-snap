import socket
import argparse
import struct
import sys
import signal
import fcntl
import os

# 颜色定义，仅在打印时使用
CNRM  = "\x1B[0m"
CRED  = "\x1B[31m"
CGRN  = "\x1B[32m"
CYEL  = "\x1B[33m"
CBLU  = "\x1B[34m"
CMAG  = "\x1B[35m"
CCYN  = "\x1B[36m"
CRESET= "\033[0m"

# 解析结构时的格式：小端序，禁止对齐
# 与 struct msg_header_t 的成员排列一一对应
header_format = '<BQQQIQBQQ32sHQ4096s'
MSG_SIZE = struct.calcsize(header_format)

# 事件种类，用于判断消息类型（对应 nl_debug.h 中定义）
KIND_EVENT_GENERIC = 0
KIND_EVENT_BIO     = 1
KIND_EVENT_COW     = 2

# 用于标识 C 端中的事件类型
EVENT_DRIVER_DEINIT = 1
EVENT_DRIVER_ERROR  = 2

# 可以根据需要补齐全部事件定义，并在下方 event_text_desc 里添加描述

event_text_desc = [
    # (event_type, event_kind, description)
    (0, KIND_EVENT_GENERIC, "EVENT_DRIVER_INIT"),
    (1, KIND_EVENT_GENERIC, "EVENT_DRIVER_DEINIT"),
    (2, KIND_EVENT_GENERIC, "EVENT_DRIVER_ERROR"),
    (3, KIND_EVENT_GENERIC, "EVENT_SETUP_SNAPSHOT"),
    (4, KIND_EVENT_GENERIC, "EVENT_SETUP_UNVERIFIED_SNAP"),
    (5, KIND_EVENT_GENERIC, "EVENT_SETUP_UNVERIFIED_INC"),
    (6, KIND_EVENT_GENERIC, "EVENT_TRANSITION_INC"),
    (7, KIND_EVENT_GENERIC, "EVENT_TRANSITION_SNAP"),
    (8, KIND_EVENT_GENERIC, "EVENT_TRANSITION_DORMANT"),
    (9, KIND_EVENT_GENERIC, "EVENT_TRANSITION_ACTIVE"),
    (10, KIND_EVENT_GENERIC, "EVENT_TRACING_STARTED"),
    (11, KIND_EVENT_GENERIC, "EVENT_TRACING_FINISHED"),
    (12, KIND_EVENT_BIO, "EVENT_BIO_INCOMING_TRACING_MRF"),
    (13, KIND_EVENT_BIO, "EVENT_BIO_INCOMING_SNAP_MRF"),
    (14, KIND_EVENT_BIO, "EVENT_BIO_CALL_ORIG"),
    (15, KIND_EVENT_BIO, "EVENT_BIO_SNAP"),
    (16, KIND_EVENT_BIO, "EVENT_BIO_INC"),
    (17, KIND_EVENT_BIO, "EVENT_BIO_CLONED"),
    (18, KIND_EVENT_BIO, "EVENT_BIO_READ_COMPLETE"),
    (19, KIND_EVENT_BIO, "EVENT_BIO_QUEUED"),
    (20, KIND_EVENT_BIO, "EVENT_BIO_RELEASED"),
    (21, KIND_EVENT_BIO, "EVENT_BIO_HANDLE_READ_BASE"),
    (22, KIND_EVENT_BIO, "EVENT_BIO_HANDLE_READ_COW"),
    (23, KIND_EVENT_BIO, "EVENT_BIO_HANDLE_READ_DONE"),
    (24, KIND_EVENT_BIO, "EVENT_BIO_HANDLE_WRITE"),
    (25, KIND_EVENT_BIO, "EVENT_BIO_HANDLE_WRITE_DONE"),
    (26, KIND_EVENT_BIO, "EVENT_BIO_FREE"),
    (27, KIND_EVENT_COW, "EVENT_COW_READ_MAPPING"),
    (28, KIND_EVENT_COW, "EVENT_COW_WRITE_MAPPING"),
    (29, KIND_EVENT_COW, "EVENT_COW_READ_DATA"),
    (30, KIND_EVENT_COW, "EVENT_COW_WRITE_DATA"),
]

def event2str(msg_type):
    for etype, _, desc in event_text_desc:
        if etype == msg_type:
            return desc
    return "UNKNOWN_EVENT"

def event_kind(msg_type):
    for etype, kind, _ in event_text_desc:
        if etype == msg_type:
            return kind
    return KIND_EVENT_GENERIC

def usage():
    print("scutech-snap driver debugging utility (Python version)")
    print(" -s <sector> : starting sector filter")
    print(" -e <sector> : ending sector filter")
    print(" -m <bio/cow/all> : mute output")
    print(" -c : disable coloring")
    print(" -r : show read only bio requests")
    print(" -w : show write only bio requests")
    print(" -h : this help message")

last_seq_num   = 0
seq_num_errors = 0
packets_lost   = 0
sock_fd        = None
proxy_fd       = None

def signal_handler(signum, frame):
    global seq_num_errors, packets_lost, sock_fd
    print(CRESET + "\nScanning done.")
    print(f"Sequence number errors: {seq_num_errors}")
    print(f"Packets lost: {packets_lost}")
    if sock_fd:
        sock_fd.close()
    sys.exit(0)

# netlink 消息头格式
NLMSG_HDRLEN = 16  # sizeof(struct nlmsghdr)
nlmsghdr_fmt = '<IHHII'  # struct nlmsghdr 的格式

def recv_netlink_msg(sock):
    """接收并解析 netlink 消息"""
    try:
        data = sock.recv(MSG_SIZE + NLMSG_HDRLEN)  # 需要加上头部长度
    except BlockingIOError:
        return None
    except OSError:
        return None

    if len(data) < NLMSG_HDRLEN:
        return None

    # 先解析 netlink 消息头
    nlh = struct.unpack(nlmsghdr_fmt, data[:NLMSG_HDRLEN])
    nl_len, nl_type, nl_flags, nl_seq, nl_pid = nlh

    if nl_len < NLMSG_HDRLEN or len(data) < nl_len:
        return None

    # 获取实际的消息数据(跳过netlink头)
    payload = data[NLMSG_HDRLEN:nl_len]
    return payload

def main():
    global last_seq_num, seq_num_errors, packets_lost
    global sock_fd, proxy_fd

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-s", type=int, default=0, help="starting sector")
    parser.add_argument("-e", type=int, default=(1 << 64) - 1, help="ending sector")
    parser.add_argument("-m", type=str, default=None, help="mute [all|cow|bio]")
    parser.add_argument("-c", action='store_true', help="disable coloring")
    parser.add_argument("-r", action='store_true', help="read only filtering")
    parser.add_argument("-w", action='store_true', help="write only filtering")
    parser.add_argument("-h", action='store_true', help="help")

    args, _ = parser.parse_known_args()

    if args.h:
        usage()
        return -1

    sector_start = args.s
    sector_end   = args.e
    mute_all     = False
    mute_bio     = False
    mute_cow     = False
    coloring     = not args.c
    read_only    = args.r
    write_only   = args.w

    if args.m == "all":
        mute_all = True
        print("Output muted")
    elif args.m == "cow":
        mute_cow = True
        print("COW events muted")
    elif args.m == "bio":
        mute_bio = True
        print("BIO events muted")

    if read_only and write_only:
        print("Invalid filter combination")
        return -1

    if sector_end < sector_start:
        print("Sector range is invalid")
        return -1
    else:
        if sector_end == (1 << 64) - 1:
            print(f"Filtering sector range: {sector_start} - max")
        else:
            print(f"Filtering sector range: {sector_start} - {sector_end}")

    # 创建 netlink 套接字
    try:
        sock_fd = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_USERSOCK)
    except OSError:
        print("Error while creating netlink socket")
        return -1

    # 创建 UDP 套接字用来转发
    try:
        proxy_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    except OSError:
        print("Error while creating proxy socket")
        return -1

    # 设置目标服务地址
    CLIENT_ADDR = "172.25.2.113"
    CLIENT_PORT = 20794
    server_addr = (CLIENT_ADDR, CLIENT_PORT)

    # 绑定 netlink
    try:
        sock_fd.bind((os.getpid(), 1))  # (pid, groups)
    except OSError as e:
        print("Couldn't bind the socket:", e)
        return -1

    # 非阻塞模式
    flags = fcntl.fcntl(sock_fd, fcntl.F_GETFL)
    fcntl.fcntl(sock_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    # 设置接收缓冲区
    rcvbuf = 500 * 1024 * 1024
    try:
        sock_fd.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    except OSError:
        print("Couldn't update socket rx buf")

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        payload = recv_netlink_msg(sock_fd)
        if not payload:
            continue

        if len(payload) < MSG_SIZE:
            continue

        # 解析消息
        unpacked = struct.unpack(header_format, payload)
        msg_type      = unpacked[0]
        seq_num       = unpacked[1]
        timestamp     = unpacked[2]
        bio_id        = unpacked[3]
        bio_size      = unpacked[4]
        bio_sector    = unpacked[5]
        bio_flags     = unpacked[6]
        bio_priv1     = unpacked[7]
        bio_priv2     = unpacked[8]
        source_func   = unpacked[9].decode('utf-8', errors='replace').rstrip('\0')
        source_line   = unpacked[10]
        data_size     = unpacked[11]
        raw_data      = unpacked[12][:data_size] if data_size > 0 else b""

        # 转发消息到远端
        try:
            proxy_fd.sendto(payload, server_addr)
        except OSError:
            print("Unable to send message")
            return -1

        # mute 判断
        if mute_all:
            continue
        if event_kind(msg_type) == KIND_EVENT_COW and mute_cow:
            continue
        if event_kind(msg_type) == KIND_EVENT_BIO and mute_bio:
            continue
        if (event_kind(msg_type) == KIND_EVENT_BIO and bio_id != 0 and
           (bio_sector < sector_start or bio_sector > sector_end)):
            continue

        # 读写过滤
        is_write = (bio_flags & 0x01) != 0
        if is_write and read_only:
            continue
        if (not is_write) and write_only:
            continue

        # 缺失序列计数
        if seq_num != 0 and last_seq_num != 0 and seq_num != last_seq_num + 1:
            packets_lost += (seq_num - last_seq_num - 1)
            if coloring:
                print(CRED, end='')
            print(f"DATA DROPPED: last seq_num: {last_seq_num}, seq_num received: {seq_num}")
            if coloring:
                print(CRESET, end='')
            seq_num_errors += 1

        last_seq_num = seq_num

        # 打印
        if coloring:
            if event_kind(msg_type) == KIND_EVENT_GENERIC:
                if msg_type == EVENT_DRIVER_ERROR:
                    print(CRED, end='')
                else:
                    print(CYEL, end='')
            elif event_kind(msg_type) == KIND_EVENT_BIO:
                print(CCYN, end='')
            elif event_kind(msg_type) == KIND_EVENT_COW:
                print(CMAG, end='')

        print(f"[{seq_num:6d}] [{timestamp:7d}] {event2str(msg_type):>32s} [{msg_type:2d}] "
              f"{source_func:>32s}(), line {source_line:4d}", end='')

        if bio_id != 0:
            print(f", bio ID: {bio_id:16x}, R/W: {'W' if is_write else 'R'}, "
                  f"sector: {bio_sector}, size: {bio_size}", end='')

        print(f", priv1: {bio_priv1}, priv2: {bio_priv2}")

        if coloring:
            print(CRESET, end='')
        sys.stdout.flush()

        # 如果是驱动卸载事件，重置序列号并退出
        if msg_type == EVENT_DRIVER_DEINIT:
            last_seq_num = 0
            break

    return 0

if __name__ == "__main__":
    sys.exit(main())
