from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static, Input


class VantaApp(App[None]):
    """Vanta — a local AI agent for your terminal."""

    TITLE = "Vanta"
    SUB_TITLE = "Your local AI agent"

    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("ctrl+q", "quit", "Quit Vanta"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Main layout container
        with Vertical(id="main-viewport"):
            yield Static("Start a conversation...", id="chat-viewport")
            yield Input(placeholder="Type your message...", id="input-area")

        yield Footer()


if __name__ == "__main__":
    VantaApp().run()
