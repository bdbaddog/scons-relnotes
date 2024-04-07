#!/usr/bin/env python

from enum import StrEnum
import yaml
import time
import os
import sys
import pprint
import argparse
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


# From SCons site_init/BuildCommandLine.py
def get_datestring():
    """
    Determine the release date and the pattern to match a date
    Mon, 05 Jun 2010 21:17:15 -0700
    NEW DATE WILL BE INSERTED HERE
    """

    min = (time.daylight and time.altzone or time.timezone) // 60
    hr = min // 60
    min = -(min % 60 + hr * 100)
    # TODO: is it better to take the date of last rev? Externally:
    #   SOURCE_DATE_EPOCH =`git log -1 --pretty=%ct`
    date = (
        time.strftime(
            "%a, %d %b %Y %X",
            time.localtime(int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))),
        )
        + " %+.4d" % min
    )

    return date


def capitalize_first(info):
    """
    Ensure that the first character of the description of this part of the PR is capitalized
    """
    if info is None:
        return ""
    else:
        info = info.strip()
        return info[0].upper() + info[1:]


class ChangeItem:
    _LEGAL_KEYS = set(['type','issue','description'])
    def __init__(self, item_info) -> None:
        # TODO: Validated below
        found_keys = set(item_info.keys())
        bad_keys = found_keys - self._LEGAL_KEYS
        if bad_keys:
            print(f"ERROR: TYPO FOUND: {bad_keys}")
            sys.exit(-1)

        self.type = item_info["type"].strip()
        self.issue = item_info.get("issue") or -1
        self.description = capitalize_first(item_info["description"])

    def __str__(self) -> str:
        return self.description


class PRInfo:
    def __init__(self, info) -> None:
        self.items = []
        for i in info:
            if i.get("author"):
                self.author = i["author"].strip()
            else:
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
                print(f"{part.type} -> {part.description}")
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

    env = Environment(
        trim_blocks=True, lstrip_blocks=True, loader=FileSystemLoader("templates")
    )
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
        datestamp=get_datestring(),
    )

    with open("CHANGES.txt", "w") as rn:
        print(
            rendered_template,
            file=rn,
        )

def process_cmdline():
    parser = argparse.ArgumentParser(prog='scons-relnotes',
                                     description='Produce CHANGES.txt and RELEASE.txt for SCons')
    
    parser.add_argument('--version', default='4.7.1', help='The version you are producing release/changes for')
    parser.add_argument('--prev', default='4.7.0', help='The previous released version of the tool')
    args = parser.parse_args()

    prev_release = args.prev
    this_release = args.version



if __name__ == "__main__":
    process_cmdline()
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
