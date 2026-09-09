<div align="center">
  <h1>📜 souyun-index</h1>
  <p><strong>搜韵诗文出处循证与历代名家汇评集释系统</strong></p>
  <p><em>寻原典之脉络，集历代之评章。一键透视古籍前后文语境，全套跨页书影无缝展卷。</em></p>

  <p>
    <a href="https://github.com/ATP24/souyun-index/releases"><img src="https://img.shields.io/github/v/release/ATP24/souyun-index?color=orange&label=Release" alt="Release v2.0.0"></a>
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
    <img src="https://img.shields.io/badge/Architecture-Zero--Dependency-orange.svg" alt="Zero Dependency">
    <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Cross Platform">
  </p>

  <p>
    <a href="#-界面预览">📸 界面预览</a> •
    <a href="#-核心特性">✨ 核心特性</a> •
    <a href="#-下载与使用指南">🚀 下载使用</a> •
    <a href="#-文献检索与考信指引">💡 考信指引</a> •
    <a href="#-声明与版权">⚖️ 声明版权</a>
  </p>
</div>

---

## 📸 界面预览 (Screenshots)

<div align="center">
  <p><strong>图 1：极简雅致的古典检索首屏</strong></p>
  <img width="771" alt="检索首屏界面" src="https://github.com/user-attachments/assets/f2d4acee-c837-446e-98f9-abd01cc9e9d9" />

  <br><br>

  <p><strong>图 2：出处溯源、前后文语境透视与名家汇评集释面板</strong></p>
  <img width="536" alt="出处溯源界面" src="https://github.com/user-attachments/assets/a820b9bf-cbd9-4353-851b-69628b9b464a" />
</div>

---

## 📖 研发背景与痛点 (Introduction)

在古典文学与文献学研究中，明辨底本渊源、核验出处语境、参订历代批点是学术论证不可或缺的核心基石。然而，学者与古典爱好者在日常检索中常面临诸多痛点：

1. **断章取义与语境割裂**：多数平台仅标注古籍书名，不提供古籍收录该诗时的前后文数行原句，无法探知古人引诗的上下文原意；
2. **名家批评散佚难寻**：历代名家（如胡应麟、高棅、沈德潜等）对名篇的考据与诗话批点零散分部于各部典籍，查阅费时费力；
3. **跨页古籍书影断档**：引文一旦跨页，传统单页查看模式往往截断关键篇章；
4. **长句标点检索易挂起**：复制包含标点、全角空格的诗句检索时，常因网络冷握手超时或底层字符死锁导致前端直接报错崩溃。

**`souyun-index`** 基于 [搜韵网开放图谱 (Open CNKGraph)](https://open.cnkgraph.com/) 底层文献寻址与数据聚合能力，彻底重构了引文循证链路，帮助研究者在兼具宋风宣纸美感与现代高效交互的界面中，高速定位纸质古籍出处、深读前后文语境、博览历代名家汇评。

---

## ✨ v2.0.0 核心特性 (Features)

### 1. 📜 原典前后文语境透视 (Context Excerpt Viewer)
* 在出处卡片中点击 **`📜 原典前后文`**，平滑展开古籍收录本诗的原始排版上下文（包含前文数行、引文命中行与后文数行）；
* **朱砂笔意高亮**：正文命中诗句呈典雅朱砂微晕下划线，一眼锁定古籍正文引用处；
* **古典叶码转译**：古籍底层分页标符（如 `<pb:...-25a>`）智能转译为雅致叶码折叠标（如 `〔第25叶正〕`）。

### 2. 📖 历代名家汇评集释 (Collective Commentary)
* 打通“典籍出处”与“历代文学批评”，自动汇总宋、元、明、清数十部名家诗话批评专著；
* 涵盖《古今诗话》《诗薮》《唐诗品汇》《唐诗解》《而庵说唐诗》《梦溪笔谈》等数十部经典，小楷笺条式排版，集历代评章于一卷。

### 3. 🖼️ 全套跨页书影连续翻阅 (Multi-Page Lightbox)
* 自动抓取并聚合《文渊阁四库全书》《古今图书集成》等古籍全套高清扫描件 CDN；
* 内置全屏展卷视窗，卡片动态标识叶数（如 `🖼️ 原书书影 (3叶)`），视窗内提供翻页器与悬浮大箭头；
* **物理键盘交互**：支持按下键盘 `←`（上一叶）与 `→`（下一叶）无缝翻阅，按 `ESC` 瞬时展卷收拢。

### 4. ⚡ 预热长连接池与网络防卡死 (Prewarmed Connection Pool)
* 程序启动时后台静默预热长连接通道，首发检索响应延迟从 15.5 秒骤降至 **0.06 秒（提速 260 倍）**；
* 前后端协同实现智能标点与全角特殊空白符（`\u3000`）清洗过滤，彻底杜绝超时与 HTTP 500。

### 5. ⚖️ 文献考信权威性智能加权 (Philological Weighting)
* 内置四级梯度的文献考信算法：
  * **第一梯度**：作者《别集》《全集》（如《杜工部集》）—— 最高考信权重；
  * **第二梯度**：历代权威《总集》（如《全唐诗》《文选》）；
  * **第三梯度**：大型官修类书（如《御定渊鉴类函》《古今图书集成》）；
  * **第四梯度**：历代名家《诗话》《笔记》。
* 默认优先展开最具底本价值的第一出处，其余版本整洁折叠。

### 6. 📑 学术规范引文与 BibTeX 批量导出
* 预置国标 **GB/T 7714**、国际 **MLA** 与基础格式，一键点击复制；
* 支持单篇与多出处批量生成并导出标准 **BibTeX** 引文条目。

---

## 🚀 下载与使用指南 (Quick Start)

### 方式一：直接下载发布包（开箱即用，无需配置环境）

请前往 👉 **[GitHub Releases 最新发布页](https://github.com/ATP24/souyun-index/releases/latest)** 下载对应系统的压缩包：

| 操作系统 | 下载文件 | 运行方式 |
| :--- | :--- | :--- |
| **🪟 Windows** | [**`souyun-index-v2.0.0-windows.zip`**](https://github.com/ATP24/souyun-index/releases/download/v2.0.0/souyun-index-v2.0.0-windows.zip) | 解压后双击 `souyun-index-windows.exe` 直接运行，自动开启浏览器页面 |
| **🍎 macOS / 🐧 Linux** | [**`souyun-index-v2.0.0-macos-linux.zip`**](https://github.com/ATP24/souyun-index/releases/download/v2.0.0/souyun-index-v2.0.0-macos-linux.zip) | 解压后在终端执行 `./start.sh` 或 `python3 src/server.py` 即可启动 |

---

### 方式二：从源码克隆运行（面向开发者）

系统核心具备**极致零依赖 (Zero-Dependency)** 特性，纯标准库即可直接运行：

```bash
# 1. 克隆代码仓库
git clone https://github.com/ATP24/souyun-index.git
cd souyun-index

# 2. 启动本地服务（直接使用 Python 核心库运行）
python src/server.py
```

*提示：若本地安装了 `requests`，系统将自动激活 0.06s 高并发长连接池与预热加速通道。*

---

## 💡 文献检索与考信指引 (Research Tips)

1. **精确字句优先**：建议输入经典【诗句片段】（如 `好雨知时节`、`白日依山尽`）或【全整诗名】（如 `登鹳雀楼`、`春夜喜雨`），系统会自动清洗多余标点并秒级直达；
2. **前后文比勘**：若发现古籍收录诗句与通行本有异文，点击 `📜 原典前后文` 即可比对古人抄录引用的真实语境；
3. **安全平稳退出**：系统内置无死锁后台守护机制，日常使用关闭浏览器网页即可。

---

## 📁 规范目录结构 (Project Architecture)

```text
souyun-index/
├── src/                  # 核心应用源码
│   ├── index.html        # 单文件前端界面（宋风美学排版、展卷翻阅、语境透视）
│   └── server.py         # 核心本地服务（连接池预热、图谱解析、无死锁生命周期）
├── CHANGELOG.md          # 详细版本演进记录
├── README.md             # 项目说明与用户指南
└── LICENSE               # MIT 开源许可证
```

---

## ⚖️ 声明与版权 (Acknowledgments & License)

* **数据来源声明**：本系统仅供学术交流与非盈利文献研读使用。底层诗文知识图谱数据与原始古籍扫描件索引来源于 **[搜韵网开放平台 (Open CNKGraph)](https://open.cnkgraph.com/)**，向搜韵网团队在中华古籍文献数字化领域做出的杰出贡献致以诚挚敬意！
* **开源许可**：本项目基于 [MIT License](LICENSE) 开源，允许自由使用、学习与衍生。
