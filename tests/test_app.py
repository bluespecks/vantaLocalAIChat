import pytest
from textual.pilot import Pilot
from vanta.app import VantaApp

@pytest.mark.asyncio
async def test_app_layout_regions():
    app = VantaApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-viewport")
        input_area = app.query_one("#input-area")
        footer = app.query_one("Footer")

        # Verify vertical stacking (chat bottom <= input top)
        # Input bottom <= footer top
        chat_bottom = chat.region.y + chat.region.height
        input_top = input_area.region.y
        input_bottom = input_area.region.y + input_area.region.height
        footer_top = footer.region.y

        assert chat_bottom <= input_top
        assert input_bottom <= footer_top

        # Verify margin/gap logic: input top should be greater than
        # chat bottom + minimum separation
        assert input_top > chat_bottom

        await pilot.exit(None)
