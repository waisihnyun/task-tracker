"""Baseline behavior. Add feature tests during Exercise 1."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import task_tracker as tracker


class TaskTrackerTests(unittest.TestCase):
    def test_add_task_trims_title_and_assigns_unique_ids(self):
        tasks = []
        tracker.add_task(tasks, "  Read module  ")
        tracker.add_task(tasks, "Try agent")
        self.assertEqual(tasks, [
            {"id": 1, "title": "Read module", "completed": False},
            {"id": 2, "title": "Try agent", "completed": False},
        ])

    def test_blank_title_is_rejected(self):
        tasks = []
        with self.assertRaises(ValueError):
            tracker.add_task(tasks, "   ")
        self.assertEqual(tasks, [])

    def test_complete_task_changes_only_the_requested_task(self):
        tasks = []
        tracker.add_task(tasks, "First")
        tracker.add_task(tasks, "Second")
        tracker.complete_task(tasks, 2)
        self.assertFalse(tasks[0]["completed"])
        self.assertTrue(tasks[1]["completed"])

    def test_unknown_task_is_rejected(self):
        with self.assertRaises(ValueError):
            tracker.complete_task([], 99)

    def test_storage_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "tasks.json"
            self.assertEqual(tracker.load_tasks(path), [])
            tasks = []
            tracker.add_task(tasks, "Learn")
            tracker.save_tasks(path, tasks)
            self.assertEqual(tracker.load_tasks(path), tasks)

    def test_cli_lists_pending_and_completed_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                tracker.main(["--data", str(path), "add", "Read module"])
                tracker.main(["--data", str(path), "add", "Try agent"])
                tracker.main(["--data", str(path), "complete", "1"])
            output = io.StringIO()
            before = path.read_bytes()
            with contextlib.redirect_stdout(output):
                tracker.main(["--data", str(path), "list"])
            self.assertEqual(output.getvalue(), "1. [x] Read module\n2. [ ] Try agent\n")
            self.assertEqual(path.read_bytes(), before)

    def test_cli_list_status_filters_preserve_saved_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            tasks = [
                {"id": 8, "title": "Completed first", "completed": True},
                {"id": 3, "title": "Pending", "completed": False},
                {"id": 11, "title": "Completed last", "completed": True},
            ]
            tracker.save_tasks(path, tasks)
            before = path.read_bytes()

            expected_outputs = (
                (["list"], "8. [x] Completed first\n3. [ ] Pending\n"
                           "11. [x] Completed last\n"),
                (["list", "--status", "all"],
                 "8. [x] Completed first\n3. [ ] Pending\n"
                 "11. [x] Completed last\n"),
                (["list", "--status", "pending"], "3. [ ] Pending\n"),
                (["list", "--status", "completed"],
                 "8. [x] Completed first\n11. [x] Completed last\n"),
            )
            for arguments, expected in expected_outputs:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    tracker.main(["--data", str(path), *arguments])
                self.assertEqual(output.getvalue(), expected)

            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(tracker.load_tasks(path), tasks)

    def test_cli_list_empty_filter_result_succeeds_without_task_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            tracker.save_tasks(path, [
                {"id": 1, "title": "Finished", "completed": True},
            ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                tracker.main([
                    "--data", str(path), "list", "--status", "pending",
                ])
            self.assertEqual(output.getvalue(), "")

    def test_cli_list_rejects_invalid_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                with self.assertRaises(SystemExit) as raised:
                    tracker.main([
                        "--data", str(path), "list", "--status", "finished",
                    ])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("invalid choice: 'finished'", error.getvalue())
            self.assertIn("pending", error.getvalue())
            self.assertIn("completed", error.getvalue())


if __name__ == "__main__":
    unittest.main()
