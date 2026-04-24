# 上传到 GitHub 的操作指引

这份指引教你把本次升级的内容推送到 `https://github.com/chengzhong215-del/ctrip_report` 仓库。

---

## 情况判断：先决定用哪种方式

### 方式 A：完全替换旧版（推荐）

如果你确定旧版 `ctrip_report` 不再维护，直接用 v2.0 全新内容覆盖，适合大多数情况。

**优点**：仓库整洁，README 开头的"版本升级"说明能清楚交代历史。

### 方式 B：保留旧版到 v1 分支，主分支升级到 v2

如果你想保留旧版（万一有人只想要纯携程分析），适合愿意花一点维护成本的情况。

**优点**：历史用户可以继续用 v1；缺点：多一条分支要管。

---

## 方式 A：完全替换（推荐）的操作步骤

### Step 1：本地准备目录

打开终端，进入你本地存放代码的地方：

```bash
# 克隆仓库（如果本地还没有）
cd ~/your-projects-folder
git clone https://github.com/chengzhong215-del/ctrip_report.git
cd ctrip_report

# 或者进入已有的本地仓库目录
cd ~/path/to/ctrip_report
git pull origin main
```

### Step 2：把旧文件先备份到一个单独分支（保险起见）

```bash
# 把当前主分支保留下来，作为历史快照
git checkout -b v1-legacy
git push origin v1-legacy

# 回到主分支准备升级
git checkout main
```

这样旧版永远挂在 `v1-legacy` 分支里，万一以后需要可以找回。

### Step 3：清空主分支的旧内容（保留 .git 目录）

```bash
# 删除所有旧文件（但保留 .git 目录）
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
```

### Step 4：解压这次打包的新内容

把我给你的 `ota_report.zip` 解压，把里面 `ota_report/` 下的**所有文件和子目录**（SKILL.md / scripts/ / references/ / platforms/ / examples/）复制到本地仓库根目录。

然后再把我单独给的 `README.md` 和 `LICENSE` 也放到仓库根目录（覆盖原来的）。

最终结构应该是：

```
ctrip_report/
├── .git/
├── README.md                  ← 新的（v2 升级说明 + 徽章）
├── LICENSE                    ← 标准 MIT
├── SKILL.md                   ← 新的
├── scripts/
│   └── make_pdf.py
├── references/
│   ├── platform_facts.md
│   ├── analysis_framework.md
│   ├── report_template.md
│   └── data_quality_gate.md
├── platforms/
│   ├── ctrip.md
│   ├── meituan.md
│   ├── dianping.md
│   └── fliggy.md
└── examples/
```

### Step 5：提交并推送

```bash
git add -A
git commit -m "v2.0: Upgrade to four-platform OTA report skill

- Expand from Ctrip-only to Ctrip/Meituan/Dianping/Fliggy
- New three-layer funnel framework (Observe / Diagnose / Leverage)
- Add multi-platform comparison mode
- Platform availability pre-check
- Platform facts reference to prevent terminology mistakes
- PDF styling upgrade: teal theme, auto date
- Remove group strategy report (focus on single hotel)

Legacy v1.x is preserved in branch v1-legacy."

git push origin main
```

### Step 6（可选）：打一个 release tag

在 GitHub 网页上，仓库页 → Releases → Draft a new release：
- Tag: `v2.0.0`
- Title: `v2.0 - Four-Platform OTA Report`
- 描述可以从 README 的 Changelog 部分复制一段

打 tag 的好处：以后用户可以通过 `git clone --branch v2.0.0` 精确拿到这个版本。

---

## 方式 B：v1 保留在分支、v2 上主分支

前三步一样（Step 1-3），把旧版保留到 `v1-legacy` 分支。

区别在于：**不要直接覆盖旧版本——你可以考虑改仓库 README 里的语气**，让 `v1-legacy` 分支显得是"历史版本"而不是"被废弃"。

在 GitHub 仓库设置里：
- Settings → General → Default branch 保持为 `main`
- 可以在仓库描述里加一句："v1 preserved in [v1-legacy branch](https://github.com/chengzhong215-del/ctrip_report/tree/v1-legacy)"

---

## 仓库名要不要改？

你这次升级从"只做携程"变成"四平台 OTA 统一"，仓库名 `ctrip_report` 其实已经不够准确。

**选项 1：不改名**——所有 star、fork、issue 链接保持不变，最稳
**选项 2：改名 `ota_report`** —— GitHub 会自动 redirect 旧链接到新名字，但如果有人在别处硬编码了旧 URL 会有 404 风险

**我的建议**：现在不改。等 v2 稳定、有一批用户用下来以后，如果真需要改再改——改名是一次性成本，早改晚改无所谓。

---

## 推送前的自检清单

推送前在本地目录过一遍：

- [ ] `SKILL.md` 开头的 frontmatter（`name: ota_report`）没问题
- [ ] `README.md` 里徽章、Changelog、License 链接都在
- [ ] `LICENSE` 里的年份是 2026、用户名是 chengzhong215-del
- [ ] `scripts/make_pdf.py` 可以在本地跑通（测试一份 md）
- [ ] `.gitignore` 不是必需的，但如果你平时会在目录里产生临时文件，建议加一份（见下面）

### 可选的 .gitignore

如果你在本地测试时会生成 PDF、临时 md 等，建议加一份 `.gitignore`：

```
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# Editor
.idea/
.vscode/
*.swp

# Test outputs
*.pdf
test_*.md
!examples/*.pdf
```

最后那行 `!examples/*.pdf` 是反规则——`examples/` 目录下的样例 PDF 需要保留，不能被上面的 `*.pdf` 规则忽略掉。

---

## 遇到问题

常见问题：

**push 被拒绝："non-fast-forward"**
说明远程有新的 commit 你本地还没拉。先 `git pull origin main`，解决冲突后再 push。

**权限不足：403 或 authentication failed**
检查本地的 GitHub credentials。如果用 HTTPS 推送，可能需要 Personal Access Token（Settings → Developer settings → Personal access tokens → Generate new token，勾 `repo` 权限）。或者改用 SSH key。

**中文 commit message 乱码**
确认本地 git 和终端都是 UTF-8。mac/linux 下一般没问题，Windows 下可能要 `git config --global i18n.commitencoding utf-8`。

---

祝升级顺利。
