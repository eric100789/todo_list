import os
import sqlite3
from datetime import datetime, timedelta

import pytest

from database import (
    get_connection, add_task, auto_complete_task, cleanup_auto_completed, get_task_by_id, delete_task
)


def test_cleanup_does_not_delete_auto_completed(tmp_path):
    # Use the real DB path but ensure we clean up any created task at the end.
    # Create a task, mark it auto-completed with an old timestamp, run cleanup,
    # and assert the task still exists and remains completed.

    # Add a task
    tid = add_task("Auto test", description="test", due_date=None, is_starred=False, category_id="__auto_complete__")

    try:
        # Mark auto-completed now
        auto_complete_task(tid)

        # Manually set auto_completed_at to an old date (beyond retention)
        old = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        conn.execute("UPDATE tasks SET auto_completed_at = ? WHERE id = ?", (old, tid))
        conn.commit()
        conn.close()

        # Run cleanup with retention 3 days
        cleanup_auto_completed(3)

        # Task should still exist and be completed
        task = get_task_by_id(tid)
        assert task is not None
        assert task.get("status") == "completed"
        # After cleanup, category should be cleared so it leaves the board
        assert task.get("category_id") is None
    finally:
        # Clean up test artifacts
        delete_task(tid)
