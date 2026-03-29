from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual import work
from textual.screen import ModalScreen
from textual.widgets import Label
from google.oauth2.credentials import Credentials

from widgets import EmailTable, Sidebar, LogPanel
from gmail_api import GmailClient


class ConfirmScreen(ModalScreen):
    """确认对话框"""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n,escape", "dismiss", "No"),
    ]

    def __init__(self, message: str, callback=None):
        super().__init__()
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Label(self.message, id="confirm-message")

    def on_mount(self):
        self.query_one(Label).styles.align = ("center", "middle")

    def action_confirm(self):
        if self.callback:
            self.callback()
        self.dismiss(True)

    def action_dismiss(self):
        self.dismiss(False)


class DetailScreen(ModalScreen):
    """邮件详情弹窗"""

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, email: dict):
        super().__init__()
        self.email = email

    def compose(self) -> ComposeResult:
        content = f"""📧 Email Details
──────────────────────────────────────
From: {self.email.get('from', 'N/A')}
Subject: {self.email.get('subject', 'N/A')}
Date: {self.email.get('date', 'N/A')}

Snippet:
{self.email.get('snippet', 'N/A')}
"""
        yield Static(content)


class GmailTUIApp(App):
    """Gmail TUI 客户端"""

    CSS = """
    /* 颜色定义 */
    $primary: #00d9ff;
    $accent: #ff00ff;
    $surface: #0d1117;
    $panel: #161b22;
    $text: #e6edf3;
    $text-on-primary: #0d1117;
    $text-on-accent: #ffffff;

    Screen {
        background: $surface;
        color: $text;
    }

    #main-container {
        layout: grid;
        grid-size: 2;
        grid-columns: 20 1fr;
        height: 100%;
    }

    #sidebar {
        background: $panel;
        border-right: outer $primary;
        padding: 1;
    }

    #sidebar Button {
        width: 100%;
        margin-bottom: 1;
        background: $surface;
        border: none;
    }

    #sidebar Button:hover {
        background: $primary;
        color: $text;
    }

    #sidebar Button.active {
        background: $accent;
        color: $text-on-accent;
    }

    EmailTable {
        background: $surface;
        border: none;
    }

    DataTable {
        background: $surface;
    }

    DataTable > .datatable--header {
        background: $panel;
        color: $primary;
        text-style: bold;
    }

    DataTable > .datatable--cursor {
        background: $accent 40%;
        color: $text;
    }

    DataTable > .datatable--hover {
        background: $primary 20%;
    }

    #log-panel {
        dock: bottom;
        height: 8;
        background: $panel;
        border-top: outer $primary;
        padding: 1;
    }

    Button {
        background: $primary;
        color: $text-on-primary;
        border: none;
        padding: 1 2;
    }

    Button:hover {
        background: $accent;
    }

    .label-badge {
        background: $accent;
        color: $text-on-accent;
        padding: 0 1;
        margin-left: 1;
    }
    """
    TITLE = "🔥 Gmail TUI"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "view_detail", "View"),
        Binding("d", "delete", "Delete"),
        Binding("1", "clean_1y", "Clean 1y"),
        Binding("2", "clean_2y", "Clean 2y"),
        Binding("3", "clean_3y", "Clean 3y"),
        Binding("/", "search", "Search"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, gmail_client: GmailClient = None):
        super().__init__()
        self.gmail_client = gmail_client
        self.emails = []  # Store loaded emails
        self.current_query = ""  # Current search query

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            yield Sidebar(id="sidebar")
            yield EmailTable(id="email-table")
        yield LogPanel(id="log-panel")
        yield Footer()

    def on_mount(self):
        if self.gmail_client:
            self.log_message("✅ Ready. Press R to load emails.")
        else:
            self.log_message("⚠️ No Gmail client. Run from main.py")

    def on_button_pressed(self, event):
        """处理侧边栏按钮点击"""
        button_id = event.button.id

        if button_id == "btn-inbox":
            self._load_emails_by_label("INBOX")
        elif button_id == "btn-sent":
            self._load_emails_by_label("SENT")
        elif button_id == "btn-spam":
            self._load_emails_by_label("SPAM")
        elif button_id == "btn-trash":
            self._load_emails_by_label("TRASH")
        elif button_id == "btn-clean-1y":
            self.action_clean_1y()
        elif button_id == "btn-clean-2y":
            self.action_clean_2y()
        elif button_id == "btn-clean-3y":
            self.action_clean_3y()

    def action_refresh(self):
        """刷新邮件列表"""
        self._load_emails_by_label("INBOX")

    @work(exclusive=True)
    async def _load_emails_by_label(self, label: str):
        """异步加载邮件"""
        if not self.gmail_client:
            self.log_message("❌ Gmail client not initialized")
            return

        self.log_message(f"📥 Loading {label}...")

        table = self.query_one("#email-table", EmailTable)
        table.loading = True
        table.clear()

        try:
            # 获取邮件列表
            messages = self.gmail_client.list_messages(label_ids=[label], max_results=100)
            self.emails = []

            self.log_message(f"📊 Found {len(messages)} emails, loading details...")

            # 获取每封邮件的详情
            for msg in messages[:50]:  # 限制加载前50封
                msg_detail = self.gmail_client.get_message(msg["id"])
                if msg_detail:
                    parsed = GmailClient.parse_message(msg_detail)
                    self.emails.append(parsed)
                    table.add_email(parsed)

            self.log_message(f"✅ Loaded {len(self.emails)} emails")

        except Exception as e:
            self.log_message(f"❌ Error: {e}")
        finally:
            table.loading = False

    def action_view_detail(self):
        """查看选中邮件详情"""
        table = self.query_one("#email-table", EmailTable)
        row = table.cursor_row

        if 0 <= row < len(self.emails):
            self.push_screen(DetailScreen(self.emails[row]))

    def action_delete(self):
        """删除选中的邮件"""
        if not self.gmail_client:
            self.log_message("❌ Gmail client not initialized")
            return

        table = self.query_one("#email-table", EmailTable)
        row = table.cursor_row

        if 0 <= row < len(self.emails):
            email = self.emails[row]

            def do_delete():
                result = self.gmail_client.batch_delete([email["id"]])
                if "error" in result:
                    self.log_message(f"❌ Delete failed: {result['error']}")
                else:
                    self.log_message(f"✅ Deleted email: {email['subject'][:30]}")
                    self.emails.pop(row)
                    table.remove_row(row)

            self.push_screen(
                ConfirmScreen(f"Delete '{email['subject'][:30]}...'?", do_delete)
            )

    def action_clean_1y(self):
        """清理1年以上的邮件"""
        self._clean_old_emails(1)

    def action_clean_2y(self):
        """清理2年以上的邮件"""
        self._clean_old_emails(2)

    def action_clean_3y(self):
        """清理3年以上的邮件"""
        self._clean_old_emails(3)

    @work(exclusive=True)
    async def _clean_old_emails(self, years: int):
        """异步清理老旧邮件"""
        if not self.gmail_client:
            self.log_message("❌ Gmail client not initialized")
            return

        query = f"older_than:{years}y"
        self.log_message(f"🔍 Searching emails older than {years} year(s)...")

        try:
            # 搜索老旧邮件
            messages = self.gmail_client.list_messages(query=query, max_results=1000)
            count = len(messages)

            if count == 0:
                self.log_message(f"✅ No emails older than {years} year(s)")
                return

            # 确认删除
            def do_delete():
                ids = [msg["id"] for msg in messages]
                self.log_message(f"🗑️ Deleting {count} emails...")
                result = self.gmail_client.batch_delete(ids)

                if "error" in result:
                    self.log_message(f"❌ Delete failed: {result['error']}")
                else:
                    self.log_message(f"✅ Deleted {result['deleted']} emails in {result['batches']} batch(es)")

            self.call_from_thread(
                self.push_screen,
                ConfirmScreen(
                    f"Found {count} emails older than {years}y.\nDelete them?",
                    do_delete
                )
            )

        except Exception as e:
            self.log_message(f"❌ Error: {e}")

    def action_search(self):
        """搜索邮件 (TODO)"""
        self.log_message("🔍 Search: Coming soon!")

    def action_help(self):
        """显示帮助"""
        self.push_screen(DetailScreen({
            "from": "Help",
            "subject": "Keyboard Shortcuts",
            "date": "",
            "snippet": """↑↓ - Navigate emails
Enter - View email detail
R - Refresh email list
D - Delete selected email
1/2/3 - Clean emails older than 1/2/3 years
/ - Search emails
Q - Quit application"""
        }))

    def log_message(self, message: str):
        """添加日志消息到日志面板"""
        log_panel = self.query_one("#log-panel", LogPanel)
        log_panel.log(message)


if __name__ == "__main__":
    app = GmailTUIApp()
    app.run()