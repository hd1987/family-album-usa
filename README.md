# 走遍美国中英文阅读

将《走遍美国》26 集中英文对照文档转换为适合电脑和手机访问的静态阅读网站。

在线访问：[https://usa.adihuang.com](https://usa.adihuang.com)

## 功能

- 收录 26 集、每集 3 幕的中英文对照剧本
- 电脑端双栏显示，手机端上下排列
- 支持显示或隐藏中文，并记住用户选择
- 隐藏中文时保留页面布局，避免阅读位置跳动
- 无搜索、账号、分析统计和阅读进度追踪
- 无 JavaScript 时仍可阅读完整双语内容

## 技术方案

项目使用 Python 标准库解析 DOCX、整理内容并生成静态 HTML。页面使用原生 HTML、CSS 和少量 JavaScript，无运行时框架和第三方依赖。

GitHub Pages 发布目录为 `docs/`。

## 目录结构

```text
source/       原始 DOCX 文档，不直接修改
scripts/      内容解析、清理和静态站点生成脚本
data/         生成的结构化内容和清理报告
templates/    HTML 模板
assets/       CSS 和 JavaScript 源文件
docs/         生成的 GitHub Pages 站点
tests/        自动化测试和测试夹具
```

`data/`、`docs/` 根目录及 `docs/assets/` 中的生成文件不应手动修改。需要调整页面或内容时，应修改源文件、模板、资源或生成脚本，然后重新构建。

## 本地预览

```bash
python3 -m http.server 8000 --directory docs
```

浏览器访问 [http://localhost:8000](http://localhost:8000)。

## 重新构建

从原始 DOCX 生成结构化内容：

```bash
python3 -m scripts.build_content \
  "source/走遍美国中英文对照.docx" \
  --output-dir data
```

生成静态网站：

```bash
python3 -m scripts.build_site data/episodes.json --output-dir docs
```

## 测试

```bash
python3 -m unittest discover -s tests -v
node tests/test_reader_js.mjs
```

测试覆盖文档解析、内容规范化、数据结构、页面渲染、站点链接和中文显示偏好。

## 部署

仓库使用 GitHub Pages 从 `main` 分支的 `/docs` 目录发布，域名由 `docs/CNAME` 配置为 `usa.adihuang.com`。

更新站点时，先重新构建并运行测试，再提交生成文件。推送到 `main` 后，GitHub Pages 会发布最新内容。
