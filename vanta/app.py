from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input

from vanta.messages import AssistantMessage, ErrorMessage, SystemNotice, UserMessage


class VantaApp(App[None]):
    """Vanta — a local AI agent for your terminal."""

    TITLE = "Vanta"
    SUB_TITLE = "Your local AI agent"

    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+q", "quit", "Quit Vanta"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Main layout container
        with Vertical(id="main-viewport"):
            with VerticalScroll(id="chat-viewport"):
                yield SystemNotice("Vanta local session active · Inference disconnected")
            yield Input(placeholder="Type your message...", id="input-area")

        yield Footer()

    def on_mount(self) -> None:
        """Focus the input area when the application starts."""
        self.query_one("#input-area", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle prompt submission from the input area."""
        user_text = event.value.strip()
        if not user_text:
            return

        chat_viewport = self.query_one("#chat-viewport", VerticalScroll)
        event.input.value = ""

        if user_text == "/clear":
            await chat_viewport.remove_children()
            await chat_viewport.mount(
                SystemNotice("Conversation cleared · Ready for new messages")
            )
            return

        # Mount user message
        await chat_viewport.mount(UserMessage(user_text))

        # Mount assistant response (sample / preview)
        if user_text.lower() == "/demo":
            assistant_text = (
                "Here is a markdown preview with syntax highlighting:\n\n"
                "```python\n"
                "# Local inference pipeline\n"
                "async def process_prompt(prompt: str) -> str:\n"
                "    return f'Processed: {prompt}'\n"
                "```\n\n"
                "- Fast local execution\n"
                "- Zero telemetry or cloud dependencies"
            )
            await chat_viewport.mount(AssistantMessage(assistant_text))
        else:
            await chat_viewport.mount(
                AssistantMessage(
                    "Inference is currently disconnected. Please connect Vanta to a running Ollama instance."
                )
            )
        chat_viewport.scroll_end(animate=False)



if __name__ == "__main__":
    VantaApp().run()
