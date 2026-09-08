# 🤝 参与贡献指南 (Contributing Guidelines)

感谢您对 **souyun-index (搜韵网收录诗文出处循证系统)** 的关注！作为数字人文（Digital Humanities）领域的开源项目，我们热忱欢迎文史学者、古籍数字化研究人员及软件开发者共同参与建设。

---

## 🧭 贡献原则与学术考信标准

1. **“言必有据，据必明本”**：任何对底本提取、版本判定逻辑的修改，须附带权威学术依据（如四库提要、书目答问、中国古籍善本书目等）；
2. **零干扰、高纯粹**：前端遵循古典文人宣纸审美，严禁引入生硬的现代广告、破坏阅读沉浸感的弹窗或突兀的颜色风格；
3. **高兼容与便携性**：后端尽量控制第三方依赖，注重单文件免安装运行的极端便携性。

---

## 🛠️ 本地开发环境准备

### 1. 代码克隆
```bash
git clone https://github.com/ATP24/souyun-index.git
cd souyun-index
```

### 2. 依赖安装
```bash
pip install -r requirements.txt
```

### 3. 运行本地服务
```bash
# Windows
start.bat

# Linux / macOS
chmod +x start.sh && ./start.sh
```

---

## 🧪 自动化测试规范

任何 Pull Request 提交前，**必须确保所有测试用例 100% 通过**：

```bash
# 运行全套功能集成测试（语境、汇评、多页书影）
python tests/test_all_v2.py

# 运行全场景标点与超时专项测试
python tests/test_fix_500.py
```

---

## 🌿 Git 分支与 Commit 规范

提交信息请遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 规范：

* `feat`: 新增特性或学术功能（如增加新的古籍格式规范）
* `fix`: 缺陷修复（如修复超时或字符兼容性问题）
* `docs`: 文档变更（如补充考证示例、更新 README）
* `style`: 不影响代码运行的格式变动（如空白清洗）
* `refactor`: 既不修复缺陷也不添加新功能的代码重构
* `test`: 增加或修改自动化测试用例

示例：
```bash
git commit -m "feat(citation): 增加丛书子目叶码提取逻辑"
git commit -m "fix(network): 优化连接池重试机制"
```

---

## 📬 提交 Pull Request 流程

1. Fork 本仓库并基于 `main` 分支创建您的特性分支：`git checkout -b feat/your-feature-name`
2. 进行代码修改并确保测试通过
3. 提交变更并推送至您的远程分支：`git push origin feat/your-feature-name`
4. 在 GitHub 上开启 Pull Request，并详细描述修改动机与测试验证结果。
