# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gmail TUI 是一个基于终端的 Gmail 邮件客户端，使用 Python 的 [Textual](https://textual.textualize.io/) 框架构建。

## Running the Application

```bash
uv run main.py
```

需要先在 `../quickstart/` 目录下放置 Google OAuth `credentials.json` 文件。

## Project Architecture

```
gmail-tui/
├── main.py          # 入口点，处理认证和启动 TUI
├── app.py           # GmailTUIApp 主应用类，包含所有业务逻辑
├── widgets.py       # 自定义 Textual 组件（EmailTable, Sidebar, LogPanel）
├── gmail_api.py     # Gmail API 封装
├── auth.py          # Google OAuth 认证
└── models.py        # 数据模型定义
```

### Key Design Patterns

- **Authentication**: 使用 OAuth 2.0，需要 `credentials.json` 和 `token.json`
- **TUI Framework**: Textual v8，使用内联 `CSS` 而非 `CSS_PATH`（见下文修复记录）
- **Components**: 继承 Textual 内置组件（DataTable, Static, Button）

## Known Issues and Fixes

### 1. CSS Loading Issue (Important)

**问题**: Textual v8 存在进程级缓存，使用 `CSS_PATH` 从文件加载 CSS 时，即使文件内容已更新，缓存的旧内容仍被使用。

**原因**: 原始 `styles.tcss` 包含无效的 CSS 属性（`hatch` 不是有效的 Textual CSS 属性），这些无效内容被缓存并应用到所有后续 CSS 文件。

**解决方案**: 使用内联 `CSS` 类属性替代 `CSS_PATH`：

```python
# ❌ 错误方式 - 会被缓存
CSS_PATH = "styles.tcss"

# ✅ 正确方式 - 内联 CSS
CSS = """
$primary: #00d9ff;
Screen { background: $primary; }
"""
```

### 2. Textual v8 API 变更

**问题**: `Static.renderable` 属性在 Textual v8 中已移除。

**原因**: 旧代码使用 `self.renderable` 获取当前内容，但该属性已重命名为 `_renderable_object`（私有属性）。

**解决方案**: 如果只需要更新内容，直接使用 `update()` 方法：

```python
# ❌ 错误
current = self.renderable or ""
self.update(f"📋 {message}")

# ✅ 正确
self.update(f"📋 {message}")
```

## Textual v8 Documentation

查阅最新用法时使用 Context7 MCP 工具：
- 库: `/textualize/textual`
- 查询关键词: `Static widget update`, `CSS`, `CSS_PATH`