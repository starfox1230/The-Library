"""Keep automatic Time Drain queue maintenance out of the user's undo path."""
from __future__ import annotations

from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


def queue_changes_allowed(collection) -> bool:
    if collection is None:
        return False
    # Automatic writes after undo would discard redo and can re-bury the very
    # card the user is trying to restore. Reads/refreshes must leave it intact.
    return not bool(collection.undo_status().redo)


@contextmanager
def automatic_queue_change(collection):
    """Merge an automatic bury/unbury into the action that advanced the queue.

    Capture a fresh target immediately before each synchronous operation. Never
    cache an undo ID across hooks or background jobs. If the undo stack is empty,
    the first automatic operation supplies the anchor for subsequent ones.
    """
    if collection is None:
        yield False
        return
    before = collection.undo_status()
    if before.redo:
        yield False
        return
    target = before.last_step if before.undo else 0
    try:
        yield True
    finally:
        after = collection.undo_status()
        if target and after.undo and not after.redo and after.last_step != target:
            try:
                collection.merge_undo_entries(target)
            except Exception:
                # The mutation has already succeeded. Retain its ordinary undo
                # entry if another add-on invalidated the target; the redo guard
                # still prevents the old undo/re-bury loop.
                logger.warning("Speed Streak could not group automatic queue undo", exc_info=True)


def is_review_undo(collection, changes) -> bool:
    # Anki returns a localized operation name, so compare with its translator.
    return collection is not None and getattr(changes, "operation", "") == collection.tr.actions_answer_card()
