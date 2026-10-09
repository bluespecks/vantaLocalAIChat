import pytest
from textual.pilot import Pilot
from vanta.app import VantaApp

@pytest.mark.asyncio
async def test_app_mounts():
    app = VantaApp()
    async with app.run_test() as pilot:
        assert app.title == "Vanta"
        assert app.query("#welcome-panel")

        # Verify Command Palette is not accessible
        # If disabled properly, it should not exist or be attachable
        # Textual 8.x behavior:
        assert app.use_command_palette is False

        await pilot.exit(None)
