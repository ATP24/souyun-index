import http.server
import socketserver
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
import json
import ssl
import sys
import os
import re
import hashlib
import socket
import webbrowser
import threading

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8')
ctx = ssl._create_unverified_context()
socketserver.TCPServer.allow_reuse_address = True

CACHE_SEARCH = {}
CACHE_BOOKLINKS = {}

def get_base_path():
    """获取程序运行时的根目录（兼容 PyInstaller 封包运行和原生运行）"""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

import time
last_ping_time = time.time()
browser_connected = False

def strip_punctuation(text):
    if not text: return ""
    text = text.strip()
    for char in ['《', '》', '〔', '〕', '[', ']', '(', ')', '<', '>']:
        text = text.replace(char, '')
    return text.strip()

def parse_book_metadata(book_raw):
    if not book_raw: return "未知典籍", "", ""
    parts = book_raw.split('-')
    b_title = strip_punctuation(parts[0])
    b_dyn = ""
    b_comp = ""
    if len(parts) >= 3:
        b_dyn = strip_punctuation(parts[1])
        b_comp = strip_punctuation(parts[2])
    elif len(parts) == 2:
        b_dyn = strip_punctuation(parts[1])
    return b_title, b_dyn, b_comp

def parse_froms_string(from_str):
    if not from_str: return "", ""
    from_str = from_str.strip()
    match = re.search(r'^(.*?)\s*(卷[一二三四五六七八九十百千万零上中下]+.*)$', from_str)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    else:
        return from_str, ""

def build_single_citation(poem_data, link=None, comment_book=None, source_type="BookLinks"):
    raw_title = poem_data.get('Title', {}).get('Content', '') if isinstance(poem_data.get('Title'), dict) else str(poem_data.get('Title', ''))
    poem_title = strip_punctuation(raw_title) or '未知诗题'
    poem_author = strip_punctuation(poem_data.get('Author', '未知'))
    poem_dynasty = strip_punctuation(poem_data.get('Dynasty', '未知'))
    
    b_title, b_dyn, b_comp, edition_name, vol, page_str = "", "", "", "", "", ""
    imgs = []
    first_image_url = ""
    book_raw = ""
    has_images = False
    
    if link:
        book_raw = link.get('Book', '')
        b_title, b_dyn, b_comp = parse_book_metadata(book_raw)
        imgs = link.get('PageImages') or []
        if imgs: 
            has_images = True
            first_image_url = imgs[0] # 底层提取高清原图 CDN 链接
        
        vol_id = link.get('VolumeId') or ''
        prev_text = link.get('PreviousText', '')
        
        if 'SBCK' in prev_text or 'SBCK' in vol_id:
            edition_name = "商务印书馆《四部丛刊》影印本"
        elif any('WYG' in img for img in imgs):
            m = re.search(r'WYG(\d+)', "".join(imgs))
            wy_num = f"第 {m.group(1)} 册" if m else ""
            edition_name = f"清文渊阁四库全书影印本 {wy_num}".strip()

        vol_raw = link.get('Volume') or ''
        vol = strip_punctuation(vol_raw.replace('〈', '').replace('〉', '')) if vol_raw else ''
        start_p, end_p = link.get('StartPage'), link.get('EndPage')
        if start_p:
            page_str = f"{start_p}-{end_p}" if (end_p and start_p != end_p) else str(start_p)
            
    elif comment_book:
        book_raw = comment_book
        parsed_title, parsed_vol = parse_froms_string(comment_book)
        b_title = strip_punctuation(parsed_title)
        vol = strip_punctuation(parsed_vol)
        edition_name = "" 
        
    compiler_str = ""
    if b_dyn and b_comp: compiler_str = f"[{b_dyn}]{b_comp}"
    elif b_comp: compiler_str = b_comp
    elif b_dyn: compiler_str = f"[{b_dyn}]"
        
    book_with_quotes = f"《{b_title}》" if b_title else ""
    
    # -------------------------------------------------------------
    # 智能打分：文献可靠度计算 (Reliability Scoring)
    # -------------------------------------------------------------
    score = 0
    is_bieji = False
    if poem_author and poem_author != '未知':
        if (b_comp and poem_author in b_comp) or (poem_author in b_title):
            is_bieji = True
            
    if is_bieji:
        score = 100 # 别集最高
    elif any(x in b_title for x in ['全唐', '全宋', '全汉', '全上古', '全明', '全清']):
        score = 80  # 权威总集
    elif any(x in b_title for x in ['诗纪', '诗话', '词话', '总龟', '古今图']):
        score = 50  # 选集/诗文评
    else:
        score = 40  # 其他一般古籍
        
    if has_images:
        score += 10 # 有影印扫描件加分
    if not edition_name and source_type == '文本底层录入来源':
        score -= 5  # 纯文本扣点分，低于带有版本信息的
        
    # -------------------------------------------------------------
    # 基础格式：[时代].[作者].《[篇名]》.载[编者(如有)].《[书名]》.[版本(如有)].[卷号(如有)].[页码(如有)]页.
    # -------------------------------------------------------------
    parts_basic = [poem_dynasty, poem_author, f"《{poem_title}》"]
    if b_title:
        zai_str = f"载{compiler_str}.{book_with_quotes}" if compiler_str else f"载{book_with_quotes}"
        parts_basic.append(zai_str)
    if edition_name: parts_basic.append(edition_name)
    if vol: parts_basic.append(vol)
    if page_str: parts_basic.append(f"{page_str}页")
    fmt_basic = ".".join(p for p in parts_basic if p) + "."
    
    # 国标格式 (GBT7714)
    fmt_gbt = f"[{poem_dynasty}] {poem_author}. {poem_title}[A]. 见: "
    if compiler_str: fmt_gbt += f"{compiler_str}(编). "
    vol_str = f": {vol}" if vol else ""
    fmt_gbt += f"{b_title}{vol_str}[M]. "
    if edition_name: fmt_gbt += f"{edition_name}. "
    if page_str: fmt_gbt += f"叶{page_str}."
    fmt_gbt = fmt_gbt.strip()
    if not fmt_gbt.endswith('.'): fmt_gbt += '.'
    
    # 学术格式
    fmt_academic = f"〔{poem_dynasty}〕{poem_author}：《{poem_title}》，载"
    if compiler_str: fmt_academic += f"{compiler_str}编："
    fmt_academic += book_with_quotes
    if vol: fmt_academic += vol
    if edition_name: fmt_academic += f"，{edition_name}"
    if page_str: fmt_academic += f"，第 {page_str} 叶"
    fmt_academic += "。"

    # MLA格式
    fmt_mla = f'{poem_author} ({poem_dynasty}). "{poem_title}." {b_title}'
    if b_comp: fmt_mla += f", edited by {b_comp}"
    if vol: fmt_mla += f", {vol}"
    if edition_name: fmt_mla += f", {edition_name}"
    if page_str: fmt_mla += f", pp. {page_str}"
    fmt_mla += "."
    
    unique_hash = hashlib.md5(f"{b_title}_{edition_name}_{vol}".encode('utf-8')).hexdigest()
    
    return {
        "source_type": source_type,
        "score": score,
        "has_images": has_images,
        "first_image_url": first_image_url,
        "basic": fmt_basic, "gbt7714": fmt_gbt, "academic": fmt_academic, "mla": fmt_mla,
        "book": b_title, "volume": vol or "无", "edition": edition_name or "无", "page": page_str,
        "raw_book": book_raw, "hash": unique_hash
    }

def translate_error(e):
    if isinstance(e, HTTPError):
        if e.code == 429: return "访问过快，已被搜韵网防DDoS系统限流，请稍后重试 (HTTP 429)"
        if e.code == 502: return "搜韵网官方服务器当前瘫痪 (502 Bad Gateway)"
        if e.code >= 500: return f"搜韵网官方接口内部错误 (HTTP {e.code})"
        return f"搜韵网接口异常 (HTTP {e.code})"
    elif isinstance(e, URLError) or isinstance(e, socket.timeout):
        return "无法连接到搜韵网，请检查您的网络连接或稍后重试。"
    elif isinstance(e, ValueError) and str(e) == "souyun_json_error":
        return "搜韵网返回了无效的数据格式，可能其官方接口正在维护。"
    elif isinstance(e, json.decoder.JSONDecodeError):
        return "搜韵网返回了无效的数据格式，可能其官方接口正在维护。"
    return str(e)

def send_json_error(handler, status, msg):
    try:
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": msg}, ensure_ascii=False).encode('utf-8'))
    except Exception: pass

class PoemCitationHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_GET(self):
        try:
            req_path = urlparse(self.path).path.rstrip('/')
            if req_path == '' or req_path == '/index.html':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                index_path = os.path.join(get_base_path(), 'index.html')
                if not os.path.exists(index_path):
                    self.send_error(404, "index.html not found")
                    return
                with open(index_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            super().do_GET()
        except Exception as e: 
            self.send_error(500, str(e))

    def do_POST(self):
        try:
            req_path = urlparse(self.path).path.rstrip('/')
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len).decode('utf-8')
            try:
                req_json = json.loads(post_body)
            except json.decoder.JSONDecodeError:
                req_json = {}
            
            if req_path == '/api/search':
                query_str = req_json.get('query', '').strip()
                if query_str in CACHE_SEARCH:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": CACHE_SEARCH[query_str]}, ensure_ascii=False).encode('utf-8'))
                    return
                
                search_url = "https://open.cnkgraph.com/api/Writing/Find"
                payload = {"key": query_str, "pageNo": 0}
                print(f"DEBUG: sending payload to Souyun: {payload}")
                sreq = urllib.request.Request(
                    search_url, data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'Mozilla/5.0'}
                )
                
                results = []
                try:
                    with urllib.request.urlopen(sreq, context=ctx, timeout=15) as sresp:
                        try:
                            data = json.loads(sresp.read().decode('utf-8'))
                        except json.decoder.JSONDecodeError:
                            raise ValueError("souyun_json_error")
                        
                        writings = data.get('Writings', [])[:10]
                        for w in writings:
                            wid = w['Id']
                            title = w.get('Title', {}).get('Content', '') if isinstance(w.get('Title'), dict) else str(w.get('Title', ''))
                            author = w.get('Author', '未知')
                            dynasty = w.get('Dynasty', '未知')
                            poem_type = w.get('Type', '诗')
                            
                            clauses = w.get('Clauses', [])
                            clause_texts = []
                            for c in clauses:
                                if isinstance(c, dict) and 'Content' in c:
                                    clause_texts.append(c['Content'].strip())
                                elif isinstance(c, str):
                                    clause_texts.append(c.strip())
                                    
                            results.append({
                                "id": wid, "title": strip_punctuation(title), "author": strip_punctuation(author),
                                "dynasty": strip_punctuation(dynasty), "type": poem_type, "clauses": clause_texts, "raw_w": w 
                            })
                            
                    CACHE_SEARCH[query_str] = results
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": results}, ensure_ascii=False).encode('utf-8'))
                    
                except HTTPError as e:
                    err_body = e.read().decode('utf-8') if hasattr(e, 'read') else ''
                    if e.code == 404:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(json.dumps({"results": []}, ensure_ascii=False).encode('utf-8'))
                        return
                    friendly_err = translate_error(e) + f" | DETAILS: {err_body} | SENT_Q: {query_str}"
                    send_json_error(self, 500, friendly_err)
                except Exception as e:
                    friendly_err = translate_error(e)
                    send_json_error(self, 500, friendly_err)
                
            elif req_path == '/api/booklinks':
                wid = req_json.get('id')
                raw_w = req_json.get('raw_w', {})
                poem_author = strip_punctuation(raw_w.get('Author', ''))
                
                if wid in CACHE_BOOKLINKS:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"citations": CACHE_BOOKLINKS[wid]}, ensure_ascii=False).encode('utf-8'))
                    return
                
                burl = f"https://open.cnkgraph.com/api/Writing/{wid}/BookLinks"
                breq = urllib.request.Request(burl, headers={'User-Agent': 'Mozilla/5.0'})
                links_data = []
                try:
                    with urllib.request.urlopen(breq, context=ctx, timeout=10) as bresp:
                        try:
                            bdata = json.loads(bresp.read().decode('utf-8'))
                        except json.decoder.JSONDecodeError:
                            raise ValueError("souyun_json_error")
                        links_data = bdata.get('Links') or []
                except HTTPError as e:
                    if e.code == 404: links_data = []
                    else:
                        import traceback; traceback.print_exc(); print('DEBUG EXCEPTION:', repr(e)); import traceback; traceback.print_exc(); send_json_error(self, 500, translate_error(e))
                        return
                except Exception as e:
                    import traceback; traceback.print_exc(); print('DEBUG EXCEPTION:', repr(e)); import traceback; traceback.print_exc(); send_json_error(self, 500, translate_error(e))
                    return
                
                citations_list = []
                seen_hashes = set()
                
                # 1. BookLinks
                if links_data:
                    for link in links_data:
                        cit = build_single_citation(raw_w, link=link, source_type="古籍实体影印本")
                        h = cit['hash']
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            citations_list.append(cit)
                
                # 2. Froms
                froms = raw_w.get('Froms') or []
                for f_str in froms:
                    if isinstance(f_str, str) and f_str.strip():
                        cit = build_single_citation(raw_w, comment_book=f_str.strip(), source_type="文本底层录入来源")
                        h = cit['hash']
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            citations_list.append(cit)

                # 3. Comments
                comments = raw_w.get('Comments') or []
                for comment in comments:
                    if isinstance(comment, dict):
                        book_name = comment.get('Book')
                        if book_name:
                            cit = build_single_citation(raw_w, comment_book=book_name, source_type="批注与收录记录")
                            h = cit['hash']
                            if h not in seen_hashes:
                                seen_hashes.add(h)
                                citations_list.append(cit)
                
                # 按照可靠度降序排列 (Reliability Sorting)
                citations_list.sort(key=lambda x: x['score'], reverse=True)
                
                # 保底方案
                if not citations_list:
                    raw_t = raw_w.get('Title', {}).get('Content', '') if isinstance(raw_w.get('Title'), dict) else str(raw_w.get('Title', ''))
                    title = strip_punctuation(raw_t) or '未知诗题'
                    author = poem_author or '未知'
                    dynasty = strip_punctuation(raw_w.get('Dynasty', '未知'))
                    citations_list.append({
                        "source_type": "无来源数据",
                        "score": 0,
                        "has_images": False,
                        "first_image_url": "",
                        "basic": f"{dynasty}.{author}.《{title}》.搜韵网未注版本.",
                        "gbt7714": f"[{dynasty}] {author}. {title}[M]. 搜韵网.",
                        "academic": f"〔{dynasty}〕{author}：《{title}》，搜韵网未注版本。",
                        "mla": f'{author} ({dynasty}). "{title}." Souyun.',
                        "book": "未知", "volume": "无", "edition": "无", "page": "", "raw_book": "无",
                        "hash": "fallback"
                    })
                    
                CACHE_BOOKLINKS[wid] = citations_list
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"citations": citations_list}, ensure_ascii=False).encode('utf-8'))
            else:
                send_json_error(self, 404, "无效的 API 路由")
        except Exception as e:
            import traceback; traceback.print_exc()
            send_json_error(self, 500, f"服务器内部错误: {str(e)}")


def find_free_port(start_port=8080, max_port=8090):
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    raise OSError(f"未找到空闲端口，已尝试 {start_port}-{max_port}")

def open_browser(url):
    import time
    time.sleep(0.5)
    webbrowser.open(url)

if __name__ == '__main__':
    try:
        PORT = find_free_port()
        # ThreadingHTTPServer 确保不会卡死
        server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), PoemCitationHandler)
        url = f"http://localhost:{PORT}"
        print(f"搜韵网收录诗文出处循证系统已启动！")
        print(f"服务器地址: {url}")
        print("按 Ctrl+C 可停止服务器...")
        
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()
        
        server.serve_forever()
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")
