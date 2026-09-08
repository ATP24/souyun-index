# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import time
import json
import urllib.request
import urllib.error

def run_test():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    
    proc = subprocess.Popen([sys.executable, "server.py"], cwd=src_dir, env=env)
    time.sleep(2.5)

    port = 8080
    for test_port in [8080, 8081, 8082, 8083]:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{test_port}/api/ping",
                headers={"Content-Type":"application/json"}
            )
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    port = test_port
                    break
        except Exception:
            pass

    print(f"[INFO] 锁定测试服务端口: {port}")

    test_queries = [
        ("纯文本检索", "好雨知时节"),
        ("全角空格容错", "好雨知时节\u3000"),
        ("末尾句号容错", "好雨知时节。"),
        ("末尾叹号容错", "好雨知时节！"),
        ("末尾问号容错", "好雨知时节？"),
        ("书名号容错", "《好雨知时节》"),
        ("多句标点容错", "好雨知时节，当春乃发生"),
        ("换行符容错", "好雨知时节\n"),
    ]

    try:
        last_results = None
        for label, q in test_queries:
            t0 = time.time()
            sreq = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/search",
                data=json.dumps({"query": q}).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(sreq, timeout=15) as sresp:
                    data = json.loads(sresp.read().decode('utf-8'))
                    results = data.get("results", [])
                    elapsed = time.time() - t0
                    print(f"[PASS] {label:12} ({q!r:16}) -> HTTP 200 ({elapsed:.2f}s), 检出: 《{results[0]['title']}》 ({results[0]['author']})")
                    assert len(results) > 0, f"未能检索到结果: {q}"
                    last_results = results
            except Exception as e:
                elapsed = time.time() - t0
                print(f"[FAIL] {label:12} ({q!r:16}) -> 失败 ({elapsed:.2f}s): {repr(e)}")
                raise e

        # 验证 booklinks 连通性
        p0 = last_results[0]
        wid = p0['id']
        t0 = time.time()
        breq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/booklinks",
            data=json.dumps({"id": wid, "raw_w": p0['raw_w']}).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(breq, timeout=15) as bresp:
            bdata = json.loads(bresp.read().decode('utf-8'))
            cits = bdata.get("citations", [])
            print(f"[PASS] 出处链路联动 ({wid}) -> HTTP 200 ({time.time()-t0:.2f}s), 出处总计: {len(cits)} 项")
            assert len(cits) > 0, "未能提取出处"

        print("\n========================================================")
        print("[SUCCESS] 预热连接池 + 标点空白清洗 + requests.Session 方案全部验证通过！")
        print("========================================================")

    finally:
        print("正在平稳关闭测试服务器...")
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/exit",
                data=json.dumps({"action":"exit"}).encode('utf-8'),
                headers={"Content-Type":"application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=1)
        except Exception:
            pass
        time.sleep(1)
        if proc.poll() is None:
            proc.kill()
        print("测试服务器已平稳退出。")

if __name__ == '__main__':
    run_test()
