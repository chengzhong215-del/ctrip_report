#!/usr/bin/env python3
"""把 OTA 质检报告 Markdown 转成精排 PDF。

用法：
    python make_pdf.py <md 文件路径>

输出：同目录同名 .pdf 文件
- 页眉左侧：自动从 md 第一个 # 标题提取
- 页眉右侧：自动取当天日期（本地时区）
- 页脚：页码 X / Y

环境依赖：
    pip install markdown weasyprint --break-system-packages
    系统需要 Noto Sans/Serif CJK 字体（Ubuntu: apt-get install fonts-noto-cjk）
"""

import sys
import re
import datetime
import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# --- 命令行参数 ---
if len(sys.argv) < 2:
    print("用法：python make_pdf.py <md 文件路径>", file=sys.stderr)
    sys.exit(1)

MD_PATH = Path(sys.argv[1])
if not MD_PATH.exists():
    print(f"错误：找不到文件 {MD_PATH}", file=sys.stderr)
    sys.exit(1)

OUT_PATH = MD_PATH.with_suffix(".pdf")

# --- 1. Markdown → HTML ---
md_text = MD_PATH.read_text(encoding="utf-8")

# 从第一个 # 标题提取酒店名作为页眉
_m = re.search(r"^#\s+(.+?)\s*$", md_text, flags=re.MULTILINE)
HOTEL_NAME = _m.group(1).strip() if _m else "OTA 质检报告"

# 尝试从第二个 ## 标题提取平台信息，拼接到页眉
_m2 = re.search(r"^##\s+(.+?)\s*$", md_text, flags=re.MULTILINE)
SUBTITLE = _m2.group(1).strip() if _m2 else ""

if SUBTITLE:
    # 去掉"质检报告""报告"等冗余词，保留平台/类型信息
    SUBTITLE_CLEAN = re.sub(r"(主页|质检|报告)", "", SUBTITLE).strip()
    HEADER_TEXT = f"{HOTEL_NAME} · {SUBTITLE_CLEAN or '主页质检报告'}"
else:
    HEADER_TEXT = f"{HOTEL_NAME} · 主页质检报告"

# 页眉长度控制（太长会挤到日期），超过 36 个中文字时做截断
if len(HEADER_TEXT) > 36:
    HEADER_TEXT = HEADER_TEXT[:34] + ".."

# 当天日期（本地时区）
TODAY_STR = datetime.date.today().isoformat()  # 形如 2026-04-24

# --- 预处理：修复 markdown 中常见的"粗体行紧接列表/表格"排版问题 ---
# python-markdown 的标准行为：列表/表格前必须有空行，否则会被并入上方段落。
# 这里在"**...** 独占一行"后没有空行就直接跟 `- ` / `1. ` / `|` 的地方自动插入空行。
md_text = re.sub(
    r"(^\*\*[^*\n]+\*\*\s*)\n(?=[-*]\s|\d+\.\s|\|)",
    r"\1\n\n",
    md_text,
    flags=re.MULTILINE,
)

# --- 预处理：嵌套列表的 2 空格缩进自动转为 4 空格 ---
# python-markdown 默认需要 4 空格才能识别嵌套列表，但人写 md 常用 2 空格。
# 这里把行首的 2 空格 + `-` 或 `*` 或数字. 转换为 4 空格。
# 注意只处理 2/6/10... 这种 2 的倍数但不是 4 的倍数的缩进。
def _fix_nested_list(line):
    m = re.match(r"^( +)([-*]\s|\d+\.\s)(.*)$", line)
    if not m:
        return line
    indent = m.group(1)
    rest = m.group(2) + m.group(3)
    n = len(indent)
    # 如果缩进是 2/6/10...（奇数个 2 空格），翻倍到 4/12/20...
    if n % 4 != 0:
        new_indent = " " * (n * 2)
        return new_indent + rest
    return line

md_text = "\n".join(_fix_nested_list(line) for line in md_text.split("\n"))

# --- 把报告抬头那行 "**xxx**：yyy **zzz**：aaa" 拆成块级列表，便于排版 ---
def _split_meta_line(m):
    line = m.group(0)
    pairs = re.findall(r"\*\*([^*]+?)\*\*：([^*\n]+?)(?=\s*\*\*|$)", line)
    if len(pairs) < 2:
        return line
    return "\n".join(f"- **{k}**：{v.strip()}" for k, v in pairs)

md_text = re.sub(
    r"^\*\*[^*\n]+\*\*：[^\n]*\*\*[^*\n]+\*\*：[^\n]*$",
    _split_meta_line,
    md_text,
    flags=re.MULTILINE,
)

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
    output_format="html5",
)

# --- 2. 精排 CSS ---
# 设计取向：
# - 正文 Noto Serif CJK SC（衬线），质感接近专业咨询/学术报告
# - 标题 Noto Sans CJK SC（无衬线），层级对比强
# - 主色：深灰蓝 #1e293b（正文/主标题/表头） + 强调色墨绿 #0f766e（重点、分隔线、徽章）
# - 中性灰阶铺底，墨绿仅在关键位置出现
# - 表格斑马纹 + 墨绿表头
# - 引用块用左边墨绿粗线强调 + 大引号装饰
# - A4 打印友好：墨绿在黑白灰度下仍深于中灰，可读

CSS_STR = r"""
@page {
    size: A4;
    margin: 20mm 18mm 22mm 18mm;

    @top-left {
        content: "__HEADER__";
        font-family: "Noto Sans CJK SC", sans-serif;
        font-size: 9pt;
        color: #64748b;
        margin-top: 8mm;
        letter-spacing: 0.3pt;
    }
    @top-right {
        content: "__DATE__";
        font-family: "Noto Sans CJK SC", sans-serif;
        font-size: 9pt;
        color: #64748b;
        margin-top: 8mm;
        letter-spacing: 0.5pt;
    }
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: "Noto Sans CJK SC", sans-serif;
        font-size: 9pt;
        color: #64748b;
        margin-bottom: 8mm;
    }
}

/* 首页无页眉 */
@page :first {
    @top-left { content: ""; }
    @top-right { content: ""; }
}

html {
    font-size: 10.5pt;
}

body {
    font-family: "Noto Serif CJK SC", "Source Han Serif SC", serif;
    line-height: 1.78;
    color: #1e293b;
    text-align: justify;
    word-break: keep-all;
    overflow-wrap: break-word;
}

/* --- 标题 --- */
h1, h2, h3, h4, h5, h6 {
    font-family: "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
    color: #1e293b;
    line-height: 1.4;
    page-break-after: avoid;
}

h1 {
    font-size: 26pt;
    font-weight: 700;
    margin: 0 0 6pt 0;
    padding-bottom: 12pt;
    border-bottom: 3pt solid #0f766e;
    letter-spacing: 0.8pt;
    color: #0f172a;
}

h2 {
    font-size: 15.5pt;
    font-weight: 700;
    margin: 26pt 0 14pt 0;
    padding: 7pt 0 7pt 12pt;
    border-left: 4pt solid #0f766e;
    background: #f1f5f9;
    color: #0f172a;
    page-break-before: auto;
    letter-spacing: 0.3pt;
}

/* 第一个 h2 不翻页 */
h1 + h2,
h1 + p + h2,
h1 + p + p + h2,
h1 + p + p + p + h2,
h1 + hr + h2,
h1 + p + hr + h2,
h1 + p + p + hr + h2 {
    page-break-before: avoid;
}

h3 {
    font-size: 13pt;
    font-weight: 700;
    margin: 20pt 0 10pt 0;
    color: #0f766e;
    border-bottom: 0.5pt solid #d1d5db;
    padding-bottom: 3pt;
}

h4 {
    font-size: 11.5pt;
    font-weight: 700;
    margin: 14pt 0 6pt 0;
    color: #334155;
}

/* --- 段落 --- */
p {
    margin: 0 0 8pt 0;
    text-indent: 0;
}

/* 报告副标题（h1 下方紧跟的 h2） */
h1 + h2 {
    font-size: 14pt;
    border-left: none;
    background: none;
    padding: 0;
    margin: 0 0 14pt 0;
    color: #64748b;
    font-weight: 400;
    letter-spacing: 0.5pt;
}

/* 三级副标题（h2 下面的 h3 如果紧跟 h1+h2） */
h1 + h2 + h3,
h1 + h2 + p + h3 {
    font-size: 11pt;
    color: #475569;
    font-weight: 400;
    border-bottom: none;
    padding-bottom: 0;
    margin: 0 0 20pt 0;
    letter-spacing: 0.3pt;
}

/* --- 元数据块（报告日期等） --- */
h1 ~ p strong:first-child {
    color: #475569;
}

/* --- 列表 --- */
ul, ol {
    margin: 6pt 0 10pt 0;
    padding-left: 20pt;
}

li {
    margin: 3pt 0;
    line-height: 1.72;
}

ul ul, ol ol, ul ol, ol ul {
    margin: 3pt 0;
}

/* --- 强调 --- */
strong {
    font-weight: 700;
    color: #0f172a;
}

em {
    font-style: normal;
    color: #64748b;
}

/* --- 表格 --- */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0 16pt 0;
    font-size: 9.5pt;
    page-break-inside: auto;
}

table thead {
    display: table-header-group;
}

table tr {
    page-break-inside: avoid;
}

th {
    background: #0f766e;
    color: #fff;
    font-family: "Noto Sans CJK SC", sans-serif;
    font-weight: 700;
    padding: 8pt 10pt;
    text-align: left;
    border: 0.5pt solid #0f766e;
    line-height: 1.4;
    letter-spacing: 0.3pt;
}

td {
    padding: 6pt 10pt;
    border: 0.5pt solid #cbd5e1;
    line-height: 1.6;
    vertical-align: top;
}

tbody tr:nth-child(even) td {
    background: #f8fafc;
}

/* --- 引用块（一页纸总结的核心容器） --- */
blockquote {
    margin: 16pt 0;
    padding: 14pt 20pt 14pt 22pt;
    border-left: 4pt solid #0f766e;
    background: #f0fdfa;
    color: #134e4a;
    font-size: 10.5pt;
    line-height: 1.8;
    page-break-inside: avoid;
    position: relative;
}

blockquote p {
    margin: 0 0 8pt 0;
}

blockquote p:last-child {
    margin-bottom: 0;
}

blockquote strong {
    color: #0f766e;
    font-size: 11pt;
    letter-spacing: 0.3pt;
}

/* 起手式引号装饰——用 h1 的 before 伪元素实现大引号 */
blockquote p:first-child::before {
    content: "\201C";
    display: inline;
    font-family: "Noto Serif CJK SC", serif;
    font-size: 18pt;
    color: #0f766e;
    margin-right: 2pt;
    vertical-align: -3pt;
    font-weight: 700;
    opacity: 0.5;
}

/* --- 评级徽章（表格中 A/A-/B+/B/B-/C+ 的颜色编码） --- */
/* 注：Markdown 表格里写成 **A-（优秀）** 这种格式时，会被渲染成 <strong>，
   这里不做强制颜色，保持表格整洁。色彩编码主要在表头背景已经体现。
   如果需要额外的评级徽章，在 md 里使用 code 标签 `A-` 来得到墨绿色强调 */

/* --- 分隔线 --- */
hr {
    border: none;
    border-top: 0.5pt solid #cbd5e1;
    margin: 20pt 0;
}

/* --- 代码 --- */
code {
    font-family: "SF Mono", Menlo, Consolas, monospace;
    background: #f1f5f9;
    color: #0f766e;
    padding: 1pt 4pt;
    border-radius: 2pt;
    font-size: 9.5pt;
}

/* --- 报告末尾附注的斜体段（由 * 包裹） --- */
body > p:last-child {
    margin-top: 14pt;
    padding-top: 10pt;
    border-top: 0.5pt dashed #cbd5e1;
    font-size: 9pt;
    color: #64748b;
    line-height: 1.6;
}

/* 避免孤行 */
p, li {
    orphans: 2;
    widows: 2;
}
"""

# --- 3. 包一层完整 HTML ---
full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{HEADER_TEXT}</title>
</head>
<body>
{html_body}
</body>
</html>
"""

css_final = CSS_STR.replace("__HEADER__", HEADER_TEXT).replace("__DATE__", TODAY_STR)

# --- 4. 生成 PDF ---
HTML(string=full_html).write_pdf(
    target=str(OUT_PATH),
    stylesheets=[CSS(string=css_final)],
)

print(f"OK -> {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.1f} KB)")
