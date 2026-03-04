#!/usr/bin/env python3
"""Focus a specific iTerm2 session by ID.

Called by terminal-notifier when the user clicks a notification banner.
Activates the exact session, selects its tab, and brings the window to front.

Usage: notify.py <session-uuid>
"""

import sys

import iterm2


async def main(connection):
    if len(sys.argv) < 2:
        return

    session_id = sys.argv[1]
    app = await iterm2.async_get_app(connection)
    session = app.get_session_by_id(session_id)

    if session:
        await session.async_activate(
            select_tab=True,
            order_window_front=True,
        )


try:
    iterm2.run_until_complete(main)
except Exception:
    pass
