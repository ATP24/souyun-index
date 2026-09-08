# 📜 souyun-index (搜韵网收录诗文出处循证系统)

> 专为古典文学研究者、高校学者及古籍爱好者量身打造的文献寻证与名家诗话集释工具。

[![Release](https://img.shields.io/github/v/release/ATP24/souyun-index?color=orange&label=Release)](https://github.com/ATP24/souyun-index/releases)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#-下载与使用指南)

---

## ✨ v2.0.0 核心特性

* 📜 **原典前后文语境透视**：在古籍出处卡片中点击“原典前后文”，即可展开古籍收录本诗的原始上下文，朱砂笔意高亮命中行，分页符智能转译为雅致叶码标（如 `〔第25叶正〕`）。
* 📖 **历代名家汇评集释**：打通古籍出处与历代文学批评，一键汇总宋、元、明、清数十部名家诗话批评（如《古今诗话》《诗薮》《唐诗解》《而庵说唐诗》等）。
* 🖼️ **全套跨页书影连续翻阅**：自动抓取多页跨页高清扫描件（文渊阁四库全书、古今图书集成等），内置全屏展卷视窗，支持点击与键盘 `←` / `→` 方向键切页。
* ⚡ **极速响应与网络防卡死**：启用高并发长连接池启动预热技术，检索首发响应从 15.5 秒骤降至 **0.06 秒**；前后端协同实现标点与全角特殊空白清洗，彻底根除 HTTP 500。
* 📑 **学术引文与 BibTeX 导出**：支持一键复制标准学术引文，提供单篇及批量 BibTeX 导出。

---

## 🚀 下载与使用指南

### 方式一：直接下载发布包（开箱即用，无需配置环境）

请前往 👉 **[GitHub Releases 最新发布页](https://github.com/ATP24/souyun-index/releases/latest)** 下载对应平台的压缩包：

| 操作系统 | 下载文件 | 运行方式 |
| :--- | :--- | :--- |
| **🪟 Windows** | `souyun-index-v2.0.0-windows.zip` | 解压后双击 `souyun-index-windows.exe`，浏览器自动启动 |
| **🍎 macOS / 🐧 Linux** | `souyun-index-v2.0.0-macos-linux.zip` | 解压后在终端执行 `./start.sh`，浏览器自动打开交互页面 |

---

### 方式二：从源码克隆运行（跨平台开发者）

确保本机已安装 Python 3.8+：

```bash
# 1. 克隆代码仓库
git clone https://github.com/ATP24/souyun-index.git
cd souyun-index

# 2. 安装轻量依赖
pip install -r requirements.txt

# 3. 启动本地服务
python src/server.py
```

终端将打印本地服务端口（默认 `http://localhost:8080`）并自动唤起默认浏览器。

---

## 📁 目录结构

```text
souyun-index/
├── src/                      # 核心源码
│   ├── index.html            # 单文件前端界面（宋风雅致设计、展卷翻阅、语境透视）
│   └── server.py             # 高性能本地服务（连接池预热、图谱解析、无死锁生命周期）
├── tests/                    # 核心自动化测试套件
├── CHANGELOG.md              # 详细版本演进历史
├── README.md                 # 项目说明
├── requirements.txt          # Python 运行依赖
├── start.bat                 # Windows 本地源码启动入口
├── start.sh                  # macOS / Linux 本地源码启动入口
└── LICENSE                   # MIT 开源协议
```

---

## 💡 数据致谢

本项目底层数据检索与图谱关联由 **[搜韵网开放图谱 (Open CNKGraph)](https://open.cnkgraph.com/)** 提供，谨向搜韵网及为中华优秀传统文化数字化做出卓越贡献的团队致以诚挚敬意！

---

## 📄 开源协议

本项目基于 [MIT 许可证](LICENSE) 开源。
