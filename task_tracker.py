"""A dependency-free task tracker for GH-600 practice."""

import argparse
import json
from pathlib import Path


def load_tasks(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_tasks(path, tasks):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")


def add_task(tasks, title):
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty")
    task = {"id": max((task["id"] for task in tasks), default=0) + 1,
            "title": title, "completed": False}
    tasks.append(task)
    return task


def complete_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            return task
    raise ValueError(f"Task {task_id} was not found")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/tasks.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Add a task")
    add.add_argument("title")
    list_command = commands.add_parser("list", help="Show tasks")
    list_command.add_argument(
        "--status",
        choices=("all", "pending", "completed"),
        default="all",
        help="Filter tasks by completion status (default: all)",
    )
    complete = commands.add_parser("complete", help="Mark a task as completed")
    complete.add_argument("id", type=int)
    args = parser.parse_args(argv)
    try:
        tasks = load_tasks(args.data)
        if args.command == "add":
            task = add_task(tasks, args.title)
            save_tasks(args.data, tasks)
            print(f"Added task {task['id']}")
        elif args.command == "complete":
            task = complete_task(tasks, args.id)
            save_tasks(args.data, tasks)
            print(f"Completed task {task['id']}")
        elif args.command == "list":
            for task in tasks:
                if args.status == "pending" and task["completed"]:
                    continue
                if args.status == "completed" and not task["completed"]:
                    continue
                marker = "x" if task["completed"] else " "
                print(f"{task['id']}. [{marker}] {task['title']}")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
