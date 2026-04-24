from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "anki-pocket-knife" / "lightning_mode.py"


class FakeDb:
    def __init__(self, cards: dict[int, dict[str, int]]) -> None:
        self.cards = cards

    def all(self, sql: str, *args):
        if "SELECT c.id, c.type" in sql:
            return [
                (card_id, self.cards[card_id]["type"])
                for card_id in args
                if card_id in self.cards
            ]

        if "SELECT COUNT(*)" in sql:
            deck_id = int(args[-1])
            card_ids = [int(value) for value in args[:-1]]
            return [
                (
                    sum(
                        1
                        for card_id in card_ids
                        if card_id in self.cards
                        and self.cards[card_id]["did"] != deck_id
                    ),
                )
            ]

        if "SELECT c.id, c.queue" in sql:
            return [
                (card_id, self.cards[card_id]["queue"])
                for card_id in args
                if card_id in self.cards and self.cards[card_id]["queue"] in {-3, -2}
            ]

        return []

    def execute(self, sql: str, *args) -> None:
        if "UPDATE cards" not in sql:
            return

        deck_id = int(args[0])
        card_ids = [int(value) for value in args[5:-1]]
        where_deck_id = int(args[-1])
        assert deck_id == where_deck_id

        for card_id in card_ids:
            card = self.cards.get(card_id)
            if not card:
                continue
            if card["did"] == deck_id:
                continue

            previous_did = card["did"]
            previous_odid = card["odid"]
            previous_odue = card["odue"]
            previous_due = card["due"]

            card["did"] = deck_id
            card["odid"] = previous_odid if previous_odid != 0 else previous_did
            card["odue"] = previous_odue if previous_odid != 0 else previous_due


class FakeCollection:
    def __init__(self, cards: dict[int, dict[str, int]]) -> None:
        self.db = FakeDb(cards)

    def usn(self) -> int:
        return 7


def _load_module(cards: dict[int, dict[str, int]]):
    for name in [
        "aqt",
        "aqt.qt",
        "aqt.utils",
        "anki_pocket_knife",
        "anki_pocket_knife.common",
        "anki_pocket_knife.settings",
        "anki_pocket_knife.lightning_mode",
    ]:
        sys.modules.pop(name, None)

    aqt = types.ModuleType("aqt")
    aqt.gui_hooks = types.SimpleNamespace()
    aqt.mw = types.SimpleNamespace(col=FakeCollection(cards), reset=lambda: None)
    sys.modules["aqt"] = aqt

    qt = types.ModuleType("aqt.qt")
    qt.QAction = object
    qt.QMenu = object
    qt.QTimer = object
    sys.modules["aqt.qt"] = qt

    utils = types.ModuleType("aqt.utils")
    utils.showInfo = lambda message: None
    utils.showWarning = lambda message: None
    sys.modules["aqt.utils"] = utils

    common = types.ModuleType("anki_pocket_knife.common")
    common.create_or_update_filtered_deck = lambda *args, **kwargs: 1
    common.get_card = lambda card_id: None
    common.rebuild_filtered_deck = lambda deck_id: None

    settings = types.ModuleType("anki_pocket_knife.settings")
    settings.get_setting = lambda key: 10
    settings.set_setting = lambda key, value: None

    package = types.ModuleType("anki_pocket_knife")
    package.__path__ = [str(MODULE_PATH.parent)]
    sys.modules["anki_pocket_knife"] = package
    sys.modules["anki_pocket_knife.common"] = common
    sys.modules["anki_pocket_knife.settings"] = settings

    spec = importlib.util.spec_from_file_location(
        "anki_pocket_knife.lightning_mode",
        MODULE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_restore_moves_cards_back_without_rebuilding_or_changing_schedule(monkeypatch):
    source_deck_id = 99
    cards = {
        1: {"type": 0, "queue": 0, "did": 11, "odid": 0, "odue": 0, "due": 100},
        2: {"type": 1, "queue": 1, "did": 12, "odid": 0, "odue": 0, "due": 900000},
        3: {"type": 3, "queue": 3, "did": 13, "odid": 0, "odue": 0, "due": 900100},
        4: {"type": 2, "queue": 2, "did": 14, "odid": 0, "odue": 0, "due": 42},
    }
    module = _load_module(cards)
    rebuilt: list[list[int]] = []

    monkeypatch.setattr(
        module,
        "_source_filtered_deck_for_session",
        lambda session: {"id": source_deck_id, "dyn": 1},
    )
    monkeypatch.setattr(
        module,
        "_rebuild_filtered_deck_with_exact_card_ids",
        lambda deck_id, *, card_ids, original_terms=None: rebuilt.append(card_ids) or True,
    )

    restored = module._restore_filtered_lightning_session(
        {
            "leftover_source_card_ids": [1, 2],
            "pending_lightning_card_ids": [3, 4],
            "source_filtered_deck_original_terms": [["deck:Source", 50, 0]],
        }
    )

    assert restored is True
    assert rebuilt == []

    for card_id in [1, 2, 3, 4]:
        assert cards[card_id]["did"] == source_deck_id
    assert cards[1] == {
        "type": 0,
        "queue": 0,
        "did": source_deck_id,
        "odid": 11,
        "odue": 100,
        "due": 100,
    }
    assert cards[2] == {
        "type": 1,
        "queue": 1,
        "did": source_deck_id,
        "odid": 12,
        "odue": 900000,
        "due": 900000,
    }
    assert cards[3] == {
        "type": 3,
        "queue": 3,
        "did": source_deck_id,
        "odid": 13,
        "odue": 900100,
        "due": 900100,
    }
    assert cards[4] == {
        "type": 2,
        "queue": 2,
        "did": source_deck_id,
        "odid": 14,
        "odue": 42,
        "due": 42,
    }
