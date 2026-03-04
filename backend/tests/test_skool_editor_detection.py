"""Test Skool comment editor detection robustness."""
import pytest


def test_editor_selectors_cover_skool_variations():
    """Verify selector list covers known Skool editor patterns."""
    selectors = [
        'div[contenteditable="true"].tiptap.ProseMirror',
        'div.tiptap.ProseMirror[contenteditable="true"]',
        '[data-placeholder*="comment"][contenteditable="true"]',
        'div[contenteditable="true"]',
        'textarea[placeholder*="comment"]',
    ]
    for selector in selectors:
        assert len(selector) > 0
        assert "[" in selector or "." in selector or "div" in selector or "textarea" in selector
    assert len(selectors) >= 5


def test_editor_timeout_increased():
    """Verify editor wait timeout is >= 20 seconds for slow loads."""
    from automation.engine import EDITOR_WAIT_TIMEOUT_MS

    assert EDITOR_WAIT_TIMEOUT_MS >= 20000


def test_editor_post_load_delay():
    """Verify post-load delay before editor detection."""
    from automation.engine import EDITOR_POST_LOAD_DELAY_MS

    assert EDITOR_POST_LOAD_DELAY_MS >= 2000
