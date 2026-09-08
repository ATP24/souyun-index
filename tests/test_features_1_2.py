# -*- coding: utf-8 -*-
"""
自动化测试：验证功能 1（原典上下文语境）与功能 2（历代名家汇评集释）
"""
import sys
import os
import subprocess
import time
import json
import urllib.request
import urllib.error

def get_free_port():
    import socket
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_test():
    print("=== 开始启动测试服务器 ===")
    src_dir = r"D:\AI\agy\搜韵网收录诗文出处循证系统\src"
    
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    
    proc = subprocess.Popen([sys.executable, "server.py"], cwd=src_dir, env=env)
    time.sleep(2.5)

    port = 8080
    for test_port in [8080, 8081, 8082, 8083]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{test_port}/api/heartbeat", data=json.dumps({"client_id":"test"}).encode('utf-8'), headers={"Content-Type":"application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    port = test_port
                    break
        except Exception:
            pass

    print(f"[INFO] 锁定测试服务端口: {port}")

    try:
        # 1. 测试功能 2：检索《登鹳雀楼》，验证是否返回 comments (历代名家汇评)
        print("\n--- 测试功能 2：验证历代名家汇评数据提取 ---")
        search_payload = {"query": "登鹳雀楼"}
        sreq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/search",
            data=json.dumps(search_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(sreq, timeout=12) as sresp:
            sdata = json.loads(sresp.read().decode('utf-8'))
            results = sdata.get("results", [])
            assert len(results) > 0, "未能检索到诗文结果"
            
            p0 = results[0]
            print(f"检出首篇: {p0.get('author')} 《{p0.get('title')}》")
            comments = p0.get("comments", [])
            print(f"名家汇评收录数: {len(comments)} 家")
            assert len(comments) > 0, "comments 数组为空，未提取到名家汇评"
            
            sample_c = comments[0]
            print(f"[PASS] 首条汇评书目: 《{sample_c.get('book')}》, 内容: {sample_c.get('content')[:40]}...")
            assert "book" in sample_c and "content" in sample_c, "汇评字段结构不完整"

        # 2. 测试功能 1：提取《登鹳雀楼》底层出处，验证是否包含 previous_text 与 later_text
        print("\n--- 测试功能 1：验证古籍引文原典前后文语境提取 ---")
        wid = p0.get("id")
        raw_w = p0.get("raw_w")
        breq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/booklinks",
            data=json.dumps({"id": wid, "raw_w": raw_w}).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(breq, timeout=12) as bresp:
            bdata = json.loads(bresp.read().decode('utf-8'))
            cits = bdata.get("citations", [])
            assert len(cits) > 0, "未能获取到出处列表"
            print(f"成功获取出处总数: {len(cits)} 项")
            
            context_cits = [c for c in cits if c.get("has_context")]
            print(f"具备原典前后文语境的出处数: {len(context_cits)} 项")
            assert len(context_cits) > 0, "未能提取到任何包含原典前后文语境的出处"
            
            sample_ctx = context_cits[0]
            print(f"[PASS] 出处 《{sample_ctx.get('book')}》 语境验证成功:")
            print(f"   前文(Previous): {sample_ctx.get('previous_text')[:35]}...")
            print(f"   命中(Matched):  {sample_ctx.get('matched_text')[:35]}...")
            print(f"   后文(Later):    {sample_ctx.get('later_text')[:35]}...")
            
            assert "has_context" in sample_ctx
            assert "previous_text" in sample_ctx
            assert "matched_text" in sample_ctx
            assert "later_text" in sample_ctx

        print("\n==============================================")
        print("[SUCCESS] 功能 1 与功能 2 后台及接口数据验证 100% 通过！")
        print("==============================================")

    finally:
        print("正在关闭测试服务器...")
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/exit", data=json.dumps({"action":"exit"}).encode('utf-8'), headers={"Content-Type":"application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=1)
        except Exception:
            pass
        time.sleep(1)
        if proc.poll() is None:
            proc.kill()
        print("测试服务器已平稳退出。")

if __name__ == '__main__':
    run_test()
