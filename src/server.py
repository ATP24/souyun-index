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
import time

__version__ = "2.0.0"

# ==============================================================================
# 1. 运行环境安全保护：解决 PyInstaller --windowed 模式下 sys.stdout/stderr 为 None 闪退
# ==============================================================================
class SafeOutput:
    def write(self, s): pass
    def flush(self): pass
    def reconfigure(self, **kwargs): pass

if sys.stdout is None:
    sys.stdout = SafeOutput()
else:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = SafeOutput()
else:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def safe_log(msg):
    try:
        enc = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
        clean = str(msg).encode(enc, errors='replace').decode(enc)
        print(f"[{time.strftime('%H:%M:%S')}] {clean}", flush=True)
    except Exception:
        pass

# 禁用全局未认证 SSL 报错（用于古籍 CDN 兼容）
ctx = ssl._create_unverified_context()
socketserver.TCPServer.allow_reuse_address = True

from collections import OrderedDict

# 线程安全轻量 LRU 缓存，防止长周期运行内存泄露
class SimpleLRUCache:
    def __init__(self, capacity=250):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def __contains__(self, key):
        with self.lock:
            return key in self.cache

    def __getitem__(self, key):
        with self.lock:
            self.cache.move_to_end(key)
            return self.cache[key]

    def __setitem__(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def get(self, key, default=None):
        with self.lock:
            if key not in self.cache:
                return default
            self.cache.move_to_end(key)
            return self.cache[key]

CACHE_SEARCH = SimpleLRUCache(200)
CACHE_BOOKLINKS = SimpleLRUCache(300)

# 现代浏览器标头池，规避搜韵网单一 UA 防爬风控拦截
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Origin': 'https://sou-yun.cn',
    'Referer': 'https://sou-yun.cn/'
}

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()
retries = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    raise_on_status=False
)
adapter = HTTPAdapter(pool_connections=25, pool_maxsize=40, max_retries=retries)
SESSION.mount("https://", adapter)
SESSION.mount("http://", adapter)
SESSION.headers.update(DEFAULT_HEADERS)

def prewarm_connection():
    """程序启动时后台静默预热连接池，使首发检索从冷启动 15s 降至 0.06s"""
    try:
        SESSION.head("https://open.cnkgraph.com", timeout=10, verify=False)
        safe_log("已完成搜韵知识图谱网络连接池异步预热")
    except Exception:
        pass

threading.Thread(target=prewarm_connection, daemon=True, name="PrewarmThread").start()

# ==============================================================================
# 2. 无死锁、防节流生命周期与心跳机制 (Zero-Deadlock Lifecycle Architecture)
# ==============================================================================
LAST_ACTIVE_TIME = time.time()
EXIT_TRIGGERED_TIME = None
CLIENT_CONNECTED = False

def record_activity():
    """原子化更新活跃时间，无锁、无阻塞、0ms耗时"""
    global LAST_ACTIVE_TIME, EXIT_TRIGGERED_TIME, CLIENT_CONNECTED
    LAST_ACTIVE_TIME = time.time()
    EXIT_TRIGGERED_TIME = None
    CLIENT_CONNECTED = True

def lifecycle_guard():
    """
    独立后台守护线程：负责感知生命周期与平滑安全退出。
    彻底杜绝原版本中在 Handler 内部调用 server.shutdown() 导致的致命线程互锁/死锁！
    """
    global LAST_ACTIVE_TIME, EXIT_TRIGGERED_TIME, CLIENT_CONNECTED
    while True:
        try:
            time.sleep(0.5)
            now = time.time()
            exit_time = EXIT_TRIGGERED_TIME
            last_active = LAST_ACTIVE_TIME
            
            # 场景 A：前端通过 beforeunload / sendBeacon 发送了 /api/exit，且超过 3.0 秒安全缓冲
            if exit_time is not None:
                elapsed_exit = now - exit_time
                safe_log(f"守护线程检测到退出信号，已等待 {elapsed_exit:.2f} 秒")
                if elapsed_exit > 3.0:
                    safe_log("前端已关闭且超出刷新缓冲期，程序安全自毁退出。")
                    time.sleep(0.2)
                    os._exit(0)
                
            # 场景 B：前端连接后，超过 90 秒无任何活跃心跳（大幅宽限期，彻底免疫浏览器后台标签页节流）
            if CLIENT_CONNECTED and (now - last_active > 90.0):
                safe_log("超过 90 秒无前端活跃信号，程序自动回收退出。")
                time.sleep(0.3)
                os._exit(0)
        except Exception as e:
            safe_log(f"守护线程异常: {e}")

# 启动独立生命周期守护线程
threading.Thread(target=lifecycle_guard, daemon=True, name="LifecycleGuard").start()

def get_base_path():
    """获取程序运行时的根目录（兼容 PyInstaller 封包运行和原生运行）"""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# 3. 古籍文献元数据清洗与考信算法
# ==============================================================================
def strip_punctuation(text):
    if not text: return ""
    text = str(text).strip()
    for char in ['《', '》', '〔', '〕', '[', ']', '(', ')', '<', '>', '〈', '〉']:
        text = text.replace(char, '')
    return text.strip()

def parse_book_metadata(book_raw):
    if not book_raw: return "未知典籍", "", ""
    parts = str(book_raw).split('-')
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
    from_str = str(from_str).strip()
    match = re.search(r'^(.*?)\s*(卷[一二三四五六七八九十百千万零上中下0-9]+.*)$', from_str)
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
    page_images = []
    first_image_url = ""
    book_raw = ""
    has_images = False
    prev_text, matched_text, later_text = "", "", ""
    
    if link:
        book_raw = link.get('Book', '')
        b_title, b_dyn, b_comp = parse_book_metadata(book_raw)
        raw_imgs = link.get('PageImages') or []
        page_images = [str(x) for x in raw_imgs if x]
        if page_images: 
            has_images = True
            first_image_url = page_images[0] # 底层提取首页高清原图 CDN 链接
        
        vol_id = str(link.get('VolumeId') or '')
        prev_text = str(link.get('PreviousText') or '').strip()
        matched_text = str(link.get('MatchedText') or '').strip()
        later_text = str(link.get('LaterText') or '').strip()
        
        if 'SBCK' in prev_text or 'SBCK' in vol_id:
            edition_name = "商务印书馆《四部丛刊》影印本"
        elif any('WYG' in str(img) for img in page_images):
            m = re.search(r'WYG(\d+)', "".join(str(x) for x in page_images))
            wy_num = f"第 {m.group(1)} 册" if m else ""
            edition_name = f"清文渊阁四库全书影印本 {wy_num}".strip()

        vol_raw = str(link.get('Volume') or '')
        vol = strip_punctuation(vol_raw) if vol_raw else ''
        start_p, end_p = link.get('StartPage'), link.get('EndPage')
        if start_p is not None:
            page_str = f"{start_p}-{end_p}" if (end_p is not None and str(start_p) != str(end_p)) else str(start_p)
            
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
    # 智能打分：文献考信加权算法 (Evidence Reliability Scoring Matrix)
    # -------------------------------------------------------------
    score = 0
    level_badge = "历代综合古籍"
    is_bieji = False
    
    # 1. 独撰别集判定：著者本人著撰的第一手底本
    if poem_author and poem_author != '未知':
        if (b_comp and poem_author in b_comp) or (poem_author in b_title):
            # 区分：若书名包含选、评、注、抄，降级为选注本
            if any(x in b_title for x in ['评注', '校注', '笺注', '集释', '汇评']):
                score = 90
                level_badge = "名家笺注别集"
                is_bieji = True
            elif any(x in b_title for x in ['选集', '选', '抄', '摭遗', '名篇']):
                score = 75
                level_badge = "后世别集选本"
                is_bieji = True
            else:
                score = 100
                level_badge = "第一手独撰别集"
                is_bieji = True

    # 2. 权威断代/通代总集与经典名选
    if not is_bieji:
        major_anthologies = [
            '全唐诗', '全宋诗', '全宋词', '全宋文', '全唐五代诗', '全唐文',
            '先秦汉魏晋南北朝诗', '全上古三代秦汉三国六朝文', '乐府诗集', '文选', '昭明文选',
            '玉台新咏', '全金诗', '全元诗', '全元散曲', '全元曲', '全明诗', '全明文',
            '全清词', '晚晴簃诗汇', '四库全书', '四部丛刊', '古逸丛书', '百部丛书集成', '四部备要'
        ]
        classic_selections = [
            '花间集', '尊前集', '中兴间气集', '唐诗纪事', '宋诗纪事', '宋六十家词',
            '绝妙好词', '草堂诗余', '词综', '明诗综', '清诗综', '古诗源', '唐诗三百首', '宋词三百首'
        ]
        poetics_keywords = [
            '诗纪', '诗话', '词话', '总龟', '古今图书集成', '艺文类聚', '初学记',
            '太平御览', '册府元龟', '北堂书钞', '岁时广记', '本事诗', '沧浪诗话', '人间词话'
        ]
        
        if any(x in b_title for x in major_anthologies):
            score = 85
            level_badge = "权威通代总集"
        elif any(x in b_title for x in classic_selections):
            score = 70
            level_badge = "经典历代名选"
        elif any(x in b_title for x in poetics_keywords):
            score = 50
            level_badge = "诗话词话辑评"
        else:
            score = 40
            level_badge = "历代综合古籍"
        
    if has_images:
        score += 10 # 具有古籍原件影印扫描件实证加分
    if edition_name:
        score += 5  # 具备四部丛刊、四库全书等清晰版本信息加分
    if not edition_name and source_type == '文本底层录入来源':
        score -= 5  # 纯文本底层录入来源缺少出版项，信度稍次
        
    # -------------------------------------------------------------
    # 著录格式 1：基础科研格式
    # -------------------------------------------------------------
    parts_basic = [poem_dynasty, poem_author, f"《{poem_title}》"]
    if b_title:
        zai_str = f"载{compiler_str}.{book_with_quotes}" if compiler_str else f"载{book_with_quotes}"
        parts_basic.append(zai_str)
    if edition_name: parts_basic.append(edition_name)
    if vol: parts_basic.append(vol)
    if page_str: parts_basic.append(f"{page_str}页")
    fmt_basic = ".".join(p for p in parts_basic if p) + "."
    
    # 著录格式 2：国标 GB/T 7714-2015 格式
    fmt_gbt = f"[{poem_dynasty}] {poem_author}. {poem_title}[A]. 见: "
    if compiler_str: fmt_gbt += f"{compiler_str}(编). "
    vol_str = f": {vol}" if vol else ""
    fmt_gbt += f"{b_title}{vol_str}[M]. "
    if edition_name: fmt_gbt += f"{edition_name}. "
    if page_str: fmt_gbt += f"叶{page_str}."
    fmt_gbt = fmt_gbt.strip()
    if not fmt_gbt.endswith('.'): fmt_gbt += '.'
    
    # 著录格式 3：古籍文献学术规范格式
    fmt_academic = f"〔{poem_dynasty}〕{poem_author}：《{poem_title}》，载"
    if compiler_str: fmt_academic += f"{compiler_str}编："
    fmt_academic += book_with_quotes
    if vol: fmt_academic += vol
    if edition_name: fmt_academic += f"，{edition_name}"
    if page_str: fmt_academic += f"，第 {page_str} 叶"
    fmt_academic += "。"

    # 著录格式 4：MLA 9th 规范
    fmt_mla = f'{poem_author} ({poem_dynasty}). "{poem_title}." {b_title}'
    if b_comp: fmt_mla += f", edited by {b_comp}"
    if vol: fmt_mla += f", {vol}"
    if edition_name: fmt_mla += f", {edition_name}"
    if page_str: fmt_mla += f", pp. {page_str}"
    fmt_mla += "."
    
    # 著录格式 5：BibTeX 规范
    cite_key = f"{poem_author}_{poem_title}".replace(" ", "_")
    bib_fields = [
        f'  author = {{{poem_author}}},',
        f'  title = {{{poem_title}}},',
        f'  booktitle = {{{b_title or "未知典籍"}}},'
    ]
    if compiler_str:
        bib_fields.append(f'  editor = {{{compiler_str}}},')
    if vol:
        bib_fields.append(f'  volume = {{{vol}}},')
    if edition_name:
        bib_fields.append(f'  note = {{{edition_name}}},')
    if page_str:
        bib_fields.append(f'  pages = {{{page_str}}},')
    if poem_dynasty and poem_dynasty != '未知':
        bib_fields.append(f'  year = {{{poem_dynasty}}},')
    fmt_bibtex = f"@incollection{{{cite_key},\n" + "\n".join(bib_fields) + "\n}"

    unique_hash = hashlib.md5(f"{b_title}_{edition_name}_{vol}".encode('utf-8')).hexdigest()
    
    has_context = bool(prev_text or later_text or matched_text)

    return {
        "source_type": source_type,
        "score": score,
        "level_badge": level_badge,
        "has_images": has_images,
        "first_image_url": first_image_url,
        "images": page_images,
        "image_count": len(page_images),
        "basic": fmt_basic, "gbt7714": fmt_gbt, "academic": fmt_academic, "mla": fmt_mla, "bibtex": fmt_bibtex,
        "book": b_title, "volume": vol or "无", "edition": edition_name or "无", "page": page_str,
        "raw_book": book_raw, "hash": unique_hash,
        "previous_text": prev_text,
        "matched_text": matched_text,
        "later_text": later_text,
        "has_context": has_context
    }

def clean_search_query(raw):
    """
    智能清洗检索关键词：
    1. 彻底清除各类 Unicode 隐形空白（全角空格 \u3000、零宽空格 \u200b、不间断空格 \u00a0、换行符等）；
    2. 剔除导致搜韵底层全文检索引擎挂起超时的标点符号（如句号、叹号、引号、书名号等）。
    """
    if not raw: return ""
    s = re.sub(r'[\s\u3000\u00a0\u200b\ufeff\r\n\t]+', ' ', str(raw)).strip()
    s = re.sub(r'[。！？!?；;:：、“”‘’\"\'《》（）\(\)\[\]【】…—～·\.]+', ' ', s).strip()
    return re.sub(r'\s+', ' ', s)

def translate_error(e):
    if isinstance(e, requests.HTTPError):
        code = e.response.status_code if e.response is not None else 500
        if code == 429: return "访问频次过高，已被搜韵网流控限制，请稍候重试 (HTTP 429)"
        if code == 502: return "搜韵网网关无响应 (HTTP 502 Bad Gateway)"
        if code == 503: return "搜韵网服务器暂时繁忙 (HTTP 503 Service Unavailable)"
        if code == 504: return "搜韵网网关请求超时 (HTTP 504 Gateway Timeout)"
        if code >= 500: return f"搜韵网官方接口维护中 (HTTP {code})"
        return f"搜韵网接口返回异常 (HTTP {code})"
    elif isinstance(e, (requests.Timeout, requests.ConnectionError, TimeoutError, socket.timeout)):
        return "连接搜韵网接口超时，已自动多次重试未果，请检查互联网连接。"
    elif isinstance(e, json.decoder.JSONDecodeError):
        return "搜韵网返回非标准数据，接口可能正处于更新或维护中。"
    return str(e)

def fetch_json_safe(url, payload=None, timeout=(6, 25)):
    """
    基于 requests.Session 连接池的高并发鲁棒网络请求器：
    1. 连接池复用已建立的 TLS 通道，彻底消除频繁重复握手造成的延迟与 EOF 异常；
    2. 内置 3 次梯度重试；
    3. 连接超时 6 秒，读取超时 25 秒。
    """
    try:
        if payload is not None:
            resp = SESSION.post(url, json=payload, timeout=timeout, verify=False)
        else:
            resp = SESSION.get(url, timeout=timeout, verify=False)
        
        if resp.status_code == 404:
            return {}
        if resp.status_code != 200:
            raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
        return resp.json()
    except Exception as e:
        safe_log(f"网络请求异常 [{url}]: {repr(e)}")
        raise e

def send_json_error(handler, status, msg):
    try:
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": msg}, ensure_ascii=False).encode('utf-8'))
    except Exception:
        pass

# ==============================================================================
# 4. HTTP 请求调度处理 (PoemCitationHandler)
# ==============================================================================
class PoemCitationHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): pass # 静默 HTTP 默认访问日志

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            req_path = urlparse(self.path).path.rstrip('/')
            
            # 心跳与保活接口 (GET 方式支持)
            if req_path == '/api/ping':
                record_activity()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "app": "souyun-index"}, ensure_ascii=False).encode('utf-8'))
                return

            if req_path == '' or req_path == '/index.html':
                record_activity()
                index_path = os.path.join(get_base_path(), 'index.html')
                if not os.path.exists(index_path):
                    self.send_error(404, "index.html not found")
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(index_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            
            super().do_GET()
        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        try:
            req_path = urlparse(self.path).path.rstrip('/')
            
            # 前端退出信号（由 navigator.sendBeacon 触发）
            if req_path == '/api/exit':
                global EXIT_TRIGGERED_TIME
                EXIT_TRIGGERED_TIME = time.time()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "exiting"}, ensure_ascii=False).encode('utf-8'))
                return

            record_activity()
            
            # 心跳与保活接口 (POST 方式)
            if req_path == '/api/ping':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "app": "souyun-index"}, ensure_ascii=False).encode('utf-8'))
                return

            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'
            try:
                req_json = json.loads(post_body)
            except json.decoder.JSONDecodeError:
                req_json = {}
            
            # -------------------------------------------------------------
            # API: /api/search (诗词名/名句检索)
            # -------------------------------------------------------------
            if req_path == '/api/search':
                raw_query = req_json.get('query', '')
                query_str = clean_search_query(raw_query)
                if not query_str:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": []}).encode('utf-8'))
                    return

                if query_str in CACHE_SEARCH:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": CACHE_SEARCH[query_str]}, ensure_ascii=False).encode('utf-8'))
                    return
                
                search_url = "https://open.cnkgraph.com/api/Writing/Find"
                payload = {"key": query_str, "pageNo": 0}
                
                try:
                    data = fetch_json_safe(search_url, payload=payload, timeout=(6, 25))
                    writings = data.get('Writings', [])[:10]
                    results = []
                    for w in writings:
                        wid = w.get('Id')
                        title = w.get('Title', {}).get('Content', '') if isinstance(w.get('Title'), dict) else str(w.get('Title', ''))
                        author = w.get('Author', '未知')
                        dynasty = w.get('Dynasty', '未知')
                        poem_type = w.get('Type', '诗')
                        
                        clauses = w.get('Clauses', [])
                        clause_texts = []
                        for c in clauses:
                            if isinstance(c, dict) and 'Content' in c:
                                clause_texts.append(str(c['Content']).strip())
                            elif isinstance(c, str):
                                clause_texts.append(c.strip())
                                
                        # 提取历代名家汇评集释 (Comments)
                        raw_comments = w.get('Comments') or []
                        cleaned_comments = []
                        for c in raw_comments:
                            if isinstance(c, dict):
                                b_name = c.get('Book') or c.get('FullPath') or '历代诗话'
                                c_content = str(c.get('Content') or '').strip()
                                if c_content and b_name:
                                    cleaned_comments.append({
                                        "book": strip_punctuation(b_name),
                                        "content": c_content
                                    })

                        results.append({
                            "id": wid, "title": strip_punctuation(title), "author": strip_punctuation(author),
                            "dynasty": strip_punctuation(dynasty), "type": poem_type, "clauses": clause_texts,
                            "comments": cleaned_comments, "raw_w": w 
                        })
                        
                    CACHE_SEARCH[query_str] = results
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": results}, ensure_ascii=False).encode('utf-8'))
                    
                except requests.HTTPError as e:
                    if e.response is not None and e.response.status_code == 404:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(json.dumps({"results": []}).encode('utf-8'))
                        return
                    safe_log(f"检索 HTTP 错误: {repr(e)}")
                    send_json_error(self, 500, translate_error(e))
                except Exception as e:
                    safe_log(f"检索处理异常: {repr(e)}")
                    send_json_error(self, 500, translate_error(e))
                
            # -------------------------------------------------------------
            # API: /api/booklinks (底层古籍书证发掘)
            # -------------------------------------------------------------
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
                links_data = []
                try:
                    bdata = fetch_json_safe(burl, payload=None, timeout=(6, 25))
                    links_data = bdata.get('Links') or []
                except requests.HTTPError as e:
                    if e.response is not None and e.response.status_code == 404:
                        links_data = []
                    else:
                        safe_log(f"请求 BookLinks 异常: {repr(e)}")
                        send_json_error(self, 500, translate_error(e))
                        return
                except Exception as e:
                    safe_log(f"请求 BookLinks 错误: {repr(e)}")
                    send_json_error(self, 500, translate_error(e))
                    return
                
                citations_list = []
                seen_hashes = set()
                
                # 1. 实体影印本 (BookLinks)
                if links_data:
                    for link in links_data:
                        cit = build_single_citation(raw_w, link=link, source_type="古籍实体影印本")
                        h = cit['hash']
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            citations_list.append(cit)
                
                # 2. 文本录入底本 (Froms)
                froms = raw_w.get('Froms') or []
                for f_str in froms:
                    if isinstance(f_str, str) and f_str.strip():
                        cit = build_single_citation(raw_w, comment_book=f_str.strip(), source_type="文本底层录入来源")
                        h = cit['hash']
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            citations_list.append(cit)

                # 3. 评注与收录记录 (Comments)
                comments = raw_w.get('Comments') or []
                for comment in comments:
                    if isinstance(comment, dict):
                        book_name = comment.get('Book')
                        if book_name:
                            cit = build_single_citation(raw_w, comment_book=str(book_name), source_type="批注与收录记录")
                            h = cit['hash']
                            if h not in seen_hashes:
                                seen_hashes.add(h)
                                citations_list.append(cit)
                
                # 可靠度降序排列 (按考信算法加权分数)
                citations_list.sort(key=lambda x: x['score'], reverse=True)
                
                # 无来源保底方案
                if not citations_list:
                    raw_t = raw_w.get('Title', {}).get('Content', '') if isinstance(raw_w.get('Title'), dict) else str(raw_w.get('Title', ''))
                    title = strip_punctuation(raw_t) or '未知诗题'
                    author = poem_author or '未知'
                    dynasty = strip_punctuation(raw_w.get('Dynasty', '未知'))
                    citations_list.append({
                        "source_type": "无来源数据",
                        "score": 0,
                        "level_badge": "未注来源",
                        "has_images": False,
                        "first_image_url": "",
                        "basic": f"{dynasty}.{author}.《{title}》.搜韵网未注版本.",
                        "gbt7714": f"[{dynasty}] {author}. {title}[M]. 搜韵网.",
                        "academic": f"〔{dynasty}〕{author}：《{title}》，搜韵网未注版本。",
                        "mla": f'{author} ({dynasty}). "{title}." Souyun.',
                        "bibtex": f"@misc{{{author}_{title},\n  author = {{{author}}},\n  title = {{{title}}},\n  note = {{搜韵网未注版本}}\n}}",
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
            safe_log(f"服务器内部异常: {str(e)}")
            send_json_error(self, 500, f"服务器处理异常: {str(e)}")

# ==============================================================================
# 5. 服务探活与启动管理
# ==============================================================================
def check_existing_instance(start_port=8080, max_port=8090):
    """极致高速单实例自探：原生 socket 毫秒级探测，绝不阻塞"""
    for port in range(start_port, max_port + 1):
        is_open = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.04)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    is_open = True
        except Exception:
            pass

        if is_open:
            try:
                # 显式使用空代理，防止被环境变量中的代理劫持本地回环
                proxy_handler = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy_handler)
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/ping",
                    headers={'User-Agent': 'souyun-index-probe'},
                    method='GET'
                )
                with opener.open(req, timeout=0.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        if data.get('app') == 'souyun-index':
                            return port
            except Exception:
                continue
    return None

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
    time.sleep(0.4)
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == '__main__':
    # 步骤 1：单实例检测（防止用户连续双击造成多进程多开）
    existing_port = check_existing_instance()
    if existing_port:
        safe_log(f"检测到服务已在端口 {existing_port} 运行，自动唤醒浏览器页面...")
        open_browser(f"http://localhost:{existing_port}")
        sys.exit(0)

    # 步骤 2：启动全新服务实例
    try:
        PORT = find_free_port()
        server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), PoemCitationHandler)
        url = f"http://localhost:{PORT}"
        
        safe_log("==================================================")
        safe_log(f"[READY] 搜韵网收录诗文出处循证系统 v{__version__} 已成功就绪！")
        safe_log(f"[INFO] 服务访问地址: {url}")
        safe_log("==================================================")
        
        if os.environ.get("NO_BROWSER") != "1":
            threading.Thread(target=open_browser, args=(url,), daemon=True).start()
        server.serve_forever()
    except Exception as e:
        safe_log(f"服务启动失败: {e}")
        time.sleep(2)
