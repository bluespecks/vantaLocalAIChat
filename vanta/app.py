from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header, Static


class VantaApp(App[None]):
    """Vanta — a local AI agent for your terminal."""

    TITLE = "Vanta"
    SUB_TITLE = "Your local AI agent"

    CSS_PATH = "app.tcss"

    # Properly disable command palette in Textual 8.x
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("ctrl+q", "quit", "Quit Vanta"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Center(id="welcome-area"):
            with Vertical(id="welcome-panel"):
                yield Static("V A N T A", id="brand")
                yield Static("Your local AI agent.", id="tagline")
                yield Static(
                    "Private by design. Powered by your local models.",
                    id="description",
                )
                yield Static(
                    "LOCAL-FIRST  /  OLLAMA",
                    id="status",
                )
                yield Static(
                    "A new way to work with local AI.",
                    id="hint",
                )

        # Ensure Footer does not expose palette actions
        yield Footer(show_command_palette=False)


if __name__ == "__main__":
    VantaApp().run()
