import pytest
from textual.containers import VerticalScroll
from textual.widgets import Input, Markdown

from vanta.app import VantaApp
from vanta.messages import AssistantMessage, ErrorMessage, SystemNotice, UserMessage

@pytest.mark.asyncio
async def test_initial_messages_presence():
    app = VantaApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-viewport", VerticalScroll)
        # Should only have one system notice
        assert len(chat.children) == 1
        assert isinstance(chat.children[0], SystemNotice)

        await pilot.exit(None)


@pytest.mark.asyncio
async def test_input_submission_adds_messages():
    app = VantaApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-viewport", VerticalScroll)
        input_widget = app.query_one("#input-area", Input)

        # Type a query and submit
        input_widget.value = "Explain Python decorators"
        await pilot.press("enter")
        await pilot.pause()

        # Should have added both UserMessage and AssistantMessage (the 'not connected' message)
        # Total messages = 1 (initial) + 2 (user+asst) = 3
        assert len(chat.children) == 3
        new_user = [c for c in chat.children if isinstance(c, UserMessage)][-1]
        assert new_user.content == "Explain Python decorators"

        new_asst = [c for c in chat.children if isinstance(c, AssistantMessage)][-1]
        assert "inference" in new_asst.content.lower()
        assert "ollama" in new_asst.content.lower()

        await pilot.exit(None)


@pytest.mark.asyncio
async def test_commands_demo_and_clear():
    app = VantaApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-viewport", VerticalScroll)
        input_widget = app.query_one("#input-area", Input)

        # Submit /demo
        input_widget.value = "/demo"
        await pilot.press("enter")
        await pilot.pause()

        asst_msgs = list(chat.query(AssistantMessage))
        assert any("markdown preview" in m.content.lower() for m in asst_msgs)

        # Submit /clear
        input_widget.value = "/clear"
        await pilot.press("enter")
        await pilot.pause()

        assert len(chat.children) == 1
        assert isinstance(chat.children[0], SystemNotice)
        assert "cleared" in chat.children[0].content.lower()

        await pilot.exit(None)

@pytest.mark.asyncio
async def test_assistant_message_update_content():
    app = VantaApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-viewport", VerticalScroll)

        # Add assistant message manually to test update
        await chat.mount(AssistantMessage("Initial"))
        asst_msg = chat.query(AssistantMessage)[-1]

        await asst_msg.update_content("Updated message")
        assert asst_msg.content == "Updated message"

        await pilot.exit(None)
