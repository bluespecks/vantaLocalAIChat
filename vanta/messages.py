from __future__ import annotations

from datetime import datetime, timezone

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Markdown, Static


class ChatMessage(Widget):
    """Base widget for chat messages in Vanta."""

    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        layout: vertical;
    }
    """


class UserMessage(ChatMessage):
    """User prompt message."""

    def __init__(
        self,
        content: str,
        *,
        sender: str = "You",
        timestamp: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.sender = sender
        self.timestamp = timestamp or datetime.now(timezone.utc).astimezone().strftime("%H:%M")

    def compose(self) -> ComposeResult:
        header_text = f"[bold #8be9fd]❯ {self.sender}[/]  [dim #6272a4]{self.timestamp}[/]"
        yield Static(header_text, classes="message-header user-header")
        yield Static(self.content, classes="user-content", markup=False)


class AssistantMessage(ChatMessage):
    """Assistant response message with rich Markdown support."""

    def __init__(
        self,
        content: str,
        *,
        model: str = "local",
        timestamp: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.model = model
        self.timestamp = timestamp or datetime.now(timezone.utc).astimezone().strftime("%H:%M")
        self._markdown = Markdown(self.content, classes="assistant-markdown")

    def compose(self) -> ComposeResult:
        header_text = (
            f"[bold #8be9fd]◈ Vanta[/]  "
            f"[#7ee787]● {self.model}[/]  "
            f"[dim #6272a4]{self.timestamp}[/]"
        )
        yield Static(header_text, classes="message-header assistant-header")
        with Vertical(classes="assistant-body"):
            yield self._markdown

    async def update_content(self, new_content: str) -> None:
        """Update markdown content for streaming or edits."""
        self.content = new_content
        await self._markdown.update(new_content)


class SystemNotice(ChatMessage):
    """Distinguishable but unobtrusive system notice."""

    def __init__(
        self,
        content: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(
            f"[dim #6272a4]— {escape(self.content)} —[/]",
            classes="system-notice-text",
        )


class ErrorMessage(ChatMessage):
    """Distinguishable but unobtrusive error message."""

    def __init__(
        self,
        content: str,
        *,
        timestamp: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.timestamp = timestamp or datetime.now(timezone.utc).astimezone().strftime("%H:%M")

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold #e06c75]⚠ Error:[/] [#e06c75]{escape(self.content)}[/]",
            classes="error-text",
        )
