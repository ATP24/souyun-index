<div align="center">
  <h1>📜 souyun-index</h1>
  <p><strong>搜韵诗文出处循证与书影映射聚合系统</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.x+-blue.svg" alt="Python 3.x+">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
    <img src="https://img.shields.io/badge/Architecture-Zero--Dependency-orange.svg" alt="Zero Dependency">
    <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg" alt="Cross Platform">
  </p>
</div>

---

## 📖 简介 (Introduction)

在古典人文学术研究中，明辨文本底本、追溯原始影印资料是文献考证的核心环节。**`souyun-index`** 是一款专为古典文学研究者、高校学者以及古籍爱好者量身定制的学术辅助工具。

本项目基于 [搜韵网开放图谱 API](https://open.cnkgraph.com/)，通过底层文献寻址与数据聚合技术，帮助用户在极简的界面中，高速定位任意古典诗词的“纸质书籍影印出处”，并智能生成符合国际主流学术规范的引文格式。

---

## ✨ 核心特性 (Features)

* 📚 **海量图谱直连映射**：越过冗杂的前端检索，在底层直接提取古籍高清扫描件 CDN 链接，实现原图满屏沉浸式阅览。
* ⚖️ **文献权威性智能加权**：内置基于四级梯度的文献考信算法（优先呈现《别集》、《全集》；其次《总集》；末次《诗话》），确保高质量底本优先展示。
* 📝 **多维学术引文生成**：支持一键切换并复制三种规范引文格式：
  * 用户自设基础格式
  * 国标 **GB/T 7714** 格式
  * 国际通用 **MLA** 规范
* 🎨 **古典优雅的跨端 UI**：采用纯正的中式美学与学术检索引擎标准排版（Hero Section），自适应动态防遮挡折叠算法，阅读体验极佳。
* ⚡ **极致零依赖 (Zero-Dependency)**：后端引擎完全基于 Python 核心标准库构建，无需配置任何第三方库或数据库，支持跨平台无痛部署。

## 💡 使用指引 (Usage Guide)

*   🎯 **精准为王**：强烈建议输入具体的【诗句片段】或【全整诗名】（如“登鹳雀楼”或“白日依山尽”），避免仅仅输入单字或极其常见的双字词，以防触发底层站点的防爬限流。
*   📑 **智能多源折叠**：一首诗若有多个出处，系统按权威度智能打分，只默认展开最权威首个出处（如别集优先于总集）。其余详细收录情况点击折叠面板即可查看。
*   🖼️ **原典影印图像**：当检测到《四部丛刊》等古籍的高清扫描件时，卡片右上角将自动呈现“原典影印图像”按钮，点击即可开启满屏沉浸式阅览。
*   ⛔ **彻底退出机制**：由于采用了最轻量、最稳定的系统架构，程序不包含脆弱的自动销毁机制。关闭网页即可结束使用。如需释放后台进程，只需在任务管理器中结束 `souyun-index-windows.exe` 即可。

---

## 📸 界面预览 (Screenshots)

*图 1：检索首屏界面*
<img width="771" alt="检索首屏界面" src="https://github.com/user-attachments/assets/f2d4acee-c837-446e-98f9-abd01cc9e9d9" />

*图 2：出处溯源、引文生成与书影对照界面*
<img width="536" alt="出处溯源界面" src="https://github.com/user-attachments/assets/a820b9bf-cbd9-4353-851b-69628b9b464a" />

---

## 🚀 快速上手 (Quick Start)

为照顾不同技术背景的用户，本项目提供两种启动方案：

### 方案 A：免安装独立程序 (面向非技术人员，推荐)

无需安装 Python 或任何环境，开箱即用：
1. 访问本仓库的 **[Releases](#)** 页面。
2. 下载针对您操作系统的执行文件（如 `souyun-index-windows.exe` 或 Mac 版本）。
3. 双击运行即可。系统将自动启动并发服务并于默认浏览器中弹出使用界面。

### 方案 B：源代码本地运行 (面向开发者/部署人员)

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/souyun-index.git
   cd souyun-index
   ```
2. **一键启动**
   项目无需 `pip install`，确保已安装 Python 3 即可。
   * Windows 用户：双击 `start.bat`
   * Mac/Linux 用户：终端执行 `./start.sh`

*(手动启动命令：`cd src && python server.py`)*

---

## 🛠️ 构建与编译 (Build)

如果您修改了源代码，并希望自行打包出独立的免安装分发包（.exe / Mac App），请执行以下操作：

1. 准备构建环境：`pip install pyinstaller`
2. 运行构建脚本：
   * Windows: 双击 `build.bat`
   * 输出的可执行文件将位于 `src/dist/` 目录下。
3. **自动化构建 (CI/CD)**：本项目已内置 `.github/workflows/release.yml`。在 GitHub 上发布新 Release 时，云端流水线将自动编译并附加跨平台可执行文件至下载区。

---

## 🤝 参与贡献 (Contributing)

我们非常欢迎来自学界与开发界的开源贡献！如果您有更好的算法逻辑、UI 设计建议或发现了 Bug，请随时提交 Pull Request 或 Issue。

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送至分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

---

## ⚖️ 声明与版权 (Acknowledgments & License)

* **数据来源声明**：本系统仅为学术交流与非盈利性研究所用的文献聚合工具。所有诗文图谱数据、接口及影印资料均来源于 [搜韵网开放平台](https://open.cnkgraph.com/)。请使用者务必遵守原平台的用户服务协议，尊重并保护原站长与学者的数字资产。
* **开源许可**：本项目代码基于 [MIT License](LICENSE) 开源。允许自由使用、修改与分发。
