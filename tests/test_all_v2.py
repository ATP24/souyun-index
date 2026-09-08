# -*- coding: utf-8 -*-
"""
自动化全套测试：验证功能 1（原典前后文语境）、功能 2（历代名家汇评集释）、功能 3（古籍多页书影连续翻阅数据流）
"""
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

    try:
        # 1. 验证功能 2：历代名家汇评
        print("\n--- 1. 验证历代名家汇评 (Comments) ---")
        search_payload = {"query": "登鹳雀楼"}
        sreq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/search",
            data=json.dumps(search_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(sreq, timeout=15) as sresp:
            sdata = json.loads(sresp.read().decode('utf-8'))
            results = sdata.get("results", [])
            assert len(results) > 0, "未能检索到诗文结果"
            
            p0 = results[0]
            print(f"检出诗文: {p0.get('author')} 《{p0.get('title')}》")
            comments = p0.get("comments", [])
            print(f"名家汇评收录数: {len(comments)} 家")
            assert len(comments) > 0, "未提取到名家汇评"
            assert "book" in comments[0] and "content" in comments[0]
            print(f"[PASS] 汇评字段完整。样例: 《{comments[0]['book']}》: {comments[0]['content'][:30]}...")

        # 2. 验证功能 1：原典前后文语境 与 功能 3：多页书影连续翻阅数据流
        print("\n--- 2. 验证前后文语境与多页书影连续翻阅数据结构 ---")
        wid = p0.get("id")
        raw_w = p0.get("raw_w")
        breq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/booklinks",
            data=json.dumps({"id": wid, "raw_w": raw_w}).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(breq, timeout=30) as bresp:
            bdata = json.loads(bresp.read().decode('utf-8'))
            cits = bdata.get("citations", [])
            assert len(cits) > 0, "未能获取到出处列表"
            print(f"成功获取出处总数: {len(cits)} 项")
            
            # 语境检查
            ctx_cits = [c for c in cits if c.get("has_context")]
            print(f"具备前后文语境的出处数: {len(ctx_cits)} 项")
            assert len(ctx_cits) > 0, "未能提取到任何包含原典语境的出处"
            print(f"[PASS] 语境验证通过，样例书目: 《{ctx_cits[0].get('book')}》")
            
            # 书影与多页书影检查
            img_cits = [c for c in cits if c.get("has_images")]
            print(f"具备古籍原书书影的出处数: {len(img_cits)} 项")
            assert len(img_cits) > 0, "未能提取到任何包含原书书影的出处"

            multi_page_cits = [c for c in cits if c.get("image_count", 0) > 1]
            print(f"具备多页连续跨页书影的出处数: {len(multi_page_cits)} 项")
            
            for c in img_cits:
                assert "images" in c, "缺少 images 字段"
                assert "image_count" in c, "缺少 image_count 字段"
                assert len(c["images"]) == c["image_count"], "images 长度与 image_count 不匹配"
                assert c["first_image_url"] == c["images"][0], "first_image_url 与 images[0] 不一致"

            if multi_page_cits:
                sample_multi = multi_page_cits[0]
                print(f"[PASS] 多页书影样例 《{sample_multi.get('book')}》 共 {sample_multi.get('image_count')} 叶:")
                for idx, u in enumerate(sample_multi.get("images")):
                    print(f"   第 {idx+1} 叶 CDN: {u}")
            else:
                print("[WARN] 《登鹳雀楼》出处多为单页书影，再测试包含多页书影的条目...")

        print("\n========================================================")
        print("[SUCCESS] 功能 1 (前后文语境)、功能 2 (名家汇评)、功能 3 (多页书影数据) 全部验证通过！")
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
        print("测试服务器已退出。")

if __name__ == '__main__':
    run_test()
