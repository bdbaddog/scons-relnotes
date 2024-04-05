#!/usr/bin/env python

from enum import StrEnum
import yaml
import pprint
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader


from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


this_release = "4.7.1"
prev_release = "4.7.0"

CHANGE_TYPES = {
    "new": "NEW FUNCTIONALITY",
    "deprecated": "DEPRECATED FUNCTIONALITY",
    "change": "CHANGED EXISTING FUNCTIONALITY",
    "enhancement": "ENHANCED EXISTING FUNCTIONALITY",
    "fix": "FIXES",
    "improvement": "IMPROVEMENTS",
    "packaging": "PACKAGING",
    "docs": "DOCUMENTATION",
    "dev": "DEVELOPMENT",
}


release_parts = {t: [] for t in CHANGE_TYPES}
all_prs = dict()


class ChangeItem:
    def __init__(self, item_info) -> None:
        # TODO: Validated below
        self.type = item_info.get("type")
        self.issue = item_info.get("item")
        self.description = item_info.get("description")

    def __str__(self) -> str:
        return self.description


class PRInfo:
    def __init__(self, info) -> None:
        self.items = []
        for i in info:
            if i.get("change"):
                change = i["change"]
                self.author = change["author"]
                self.issue = change.get("issue", False)
                self.notes = change.get("notes", False)
            elif i.get("description"):
                self.items.append(ChangeItem(i))

    def __str__(self) -> str:
        return self.notes


def read_files(directory="samples"):
    for f in Path(directory).glob("*.yaml"):
        print(f"Processing: {f}")
        with f.open(mode="r") as blurb:
            info = yaml.load_all(blurb, Loader)
            pr_info = PRInfo(info)
            if pr_info.author in all_prs:
                all_prs[pr_info.author].append(pr_info)
            else:
                all_prs[pr_info.author] = [pr_info]

            for part in pr_info.items:
                release_parts[part.type].append(part)


def get_git_shortlog():
    """
    git shortlog --no-merges -ns 4.0.1..HEAD
    """
    return """git shortlog --no-merges -ns 4.7.0..HEAD
     7  Raymond Li
     5  Mats Wichmann
     2  William Deegan"""


def render_release_notes():

    env = Environment(trim_blocks=True, loader=FileSystemLoader("templates"))
    template = env.get_template("release.txt.jinja2")
    rendered_template = template.render(
        CHANGE_TYPES=CHANGE_TYPES,
        release_parts=release_parts,
        this_release=this_release,
        prev_release=prev_release,
        git_shortlog_content=get_git_shortlog(),
    )

    with open("RELEASE.txt", "w") as rn:
        print(
            rendered_template,
            file=rn,
        )


def split_and_sort_key(name):
    """Splits the name into first and last name and returns a sorting key.

    Args:
        name: A string containing "first name last name".

    Returns:
        A tuple containing the last name (lowercased), the first name (lowercased), and the original name.
    """
    print(f"Processing {name}")
    first, last = name.lower().split()  # Lowercase for case-insensitive sorting
    return (last, first, name)  # Sort by last name, then first name, then original name


def render_changes():

    all_ordered_prs = {
        k: all_prs[k] for k in sorted(all_prs.keys(), key=split_and_sort_key)
    }

    env = Environment(trim_blocks=True, loader=FileSystemLoader("templates"))
    template = env.get_template("changes.txt.jinja2")
    rendered_template = template.render(
        all_ordered_prs=all_ordered_prs,
        this_release=this_release,
        prev_release=prev_release,
    )

    with open("CHANGES.txt", "w") as rn:
        print(
            rendered_template,
            file=rn,
        )


if __name__ == "__main__":
    read_files("samples")
    print("done")

    render_release_notes()
    render_changes()

    # for doc in dictionary:
    #     print("New document:")
    #     for key, value in doc.items():
    #         print(key + " : " + str(value))
    #         if type(value) is list:
    #             print(str(len(value)))