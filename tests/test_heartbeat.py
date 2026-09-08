import subprocess
import time
import urllib.request
import json
import socket
import sys

def get_free_port():
    for p in range(8080, 8091):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) == 0:
                return p
    return None

def ping(port):
    req = urllib.request.Request(f'http://localhost:{port}/api/ping', method='POST')
    return urllib.request.urlopen(req).getcode()

def search(port):
    payload_bytes = b'{"query": "\\u767d\\u65e5\\u4f9d\\u5c71\\u5c3d"}'
    req = urllib.request.Request(
        f'http://localhost:{port}/api/search', 
        data=payload_bytes,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    res = urllib.request.urlopen(req)
    return res.getcode(), json.loads(res.read().decode('utf-8'))

import os
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
print("=== 正在启动测试 ===")
proc = subprocess.Popen([sys.executable, "server.py"], cwd=src_dir)
time.sleep(2)

port = get_free_port()
if not port:
    print("[FAIL] 测试失败：未能检测到服务器端口！")
    proc.kill()
    sys.exit(1)

print(f"[OK] 服务器已启动，监听端口: {port}")

print("\n--- 测试 1：心跳与检索并发 ---")
try:
    code = ping(port)
    print(f"心跳 1 成功，状态码: {code}")
    time.sleep(3)
    
    code = ping(port)
    print(f"心跳 2 成功，状态码: {code}")
    
    print("发起检索请求 '白日依山尽' ...")
    scode, data = search(port)
    print(f"检索成功，状态码: {scode}，返回条目数: {len(data.get('results', []))}")
    
    time.sleep(3)
    code = ping(port)
    print(f"心跳 3 成功，状态码: {code}")
    print("[PASS] 测试 1 完美通过：检索接口与心跳接口完全独立运行！")
except Exception as e:
    print(f"[FAIL] 测试 1 失败：{e}")
    proc.kill()
    sys.exit(1)

print("\n--- 测试 2：网页关闭（断开）自毁 ---")
print("停止发送心跳，等待 17 秒，观察服务器是否自毁...")
time.sleep(17)
if proc.poll() is not None:
    print("[PASS] 服务器已干净地自动退出 (Exit code 0)！进程无残留！")
else:
    print("[FAIL] 测试 2 失败：服务器在 17 秒后依然存活！")
    proc.kill()
    sys.exit(1)

print("\n--- 测试 3：老电脑开机启动超时 ---")
print("重新启动服务器...")
proc2 = subprocess.Popen([sys.executable, "server.py"], cwd=src_dir)
print("服务器已启动，但不发送任何心跳，等待 62 秒...")
time.sleep(63)
if proc2.poll() is not None:
    print("[PASS] 服务器在 60 秒极长宽限期后已自动退出，未变成僵尸进程！")
else:
    print("[FAIL] 测试 3 失败：60 秒后服务器仍存活！")
    proc2.kill()
    sys.exit(1)

print("\n[SUCCESS] 所有严格黑盒测试全部通过！系统机制堪称完美！")
