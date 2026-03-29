from textual.widgets import DataTable, Static, Button
from textual.containers import Vertical
from rich.text import Text


class EmailTable(DataTable):
    """邮件列表表格"""

    def on_mount(self):
        self.add_columns("From", "Subject", "Date", "Labels")
        self.cursor_type = "row"
        self.zebra_stripes = True

    def add_email(self, email: dict):
        """添加一行邮件"""
        labels_text = " ".join(self._format_labels(email.get("labels", [])))
        self.add_row(
            email.get("from", ""),
            email.get("subject", ""),
            email.get("date", "")[:10],
            labels_text
        )

    def _format_labels(self, labels: list) -> list:
        """格式化标签为 emoji"""
        label_emojis = {
            "INBOX": "📥",
            "SENT": "📤",
            "SPAM": "🗑️",
            "TRASH": "🗑️",
            "STARRED": "⭐",
            "IMPORTANT": "🔴",
            "CATEGORY_PROMOTIONS": "📦",
            "CATEGORY_SOCIAL": "👥",
        }
        return [label_emojis.get(l, "") for l in labels if label_emojis.get(l)]


class Sidebar(Vertical):
    """侧边栏导航"""

    def compose(self):
        yield Button("📥 Inbox", id="btn-inbox", classes="active")
        yield Button("📤 Sent", id="btn-sent")
        yield Button("🗑️ Spam", id="btn-spam")
        yield Button("🗂️ Trash", id="btn-trash")
        yield Static("─" * 18, classes="divider")
        yield Static("🧹 CLEAN OLD:")
        yield Button("  [1y] 1+ year", id="btn-clean-1y")
        yield Button("  [2y] 2+ years", id="btn-clean-2y")
        yield Button("  [3y] 3+ years", id="btn-clean-3y")


class LogPanel(Static):
    """日志面板"""

    def log(self, message: str):
        self.update(f"📋 {message}")