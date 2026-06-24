"""Tests for the edge-detection logic. Run: python test_logic.py"""

from door_music_trigger import is_close_edge


def test_open_to_closed_fires():
    assert is_close_edge("open", "closed") is True


def test_closed_to_closed_does_not_fire():
    assert is_close_edge("closed", "closed") is False


def test_closed_to_open_does_not_fire():
    assert is_close_edge("closed", "open") is False


def test_open_to_open_does_not_fire():
    assert is_close_edge("open", "open") is False


def test_initial_state_does_not_fire():
    # previous is None on startup -> never fire on first observation
    assert is_close_edge(None, "closed") is False
    assert is_close_edge(None, "open") is False


def _run():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)} passed.")


if __name__ == "__main__":
    _run()
