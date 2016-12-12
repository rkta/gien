#!/usr/bin/env python3

# gien - export Github issue tracker & wiki contents to local email storage
# Copyright (C) 2016 Jens John <jjohn@2ion.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from gien.remote import fetch_issues
from gien.mail import thread_wiki, thread_issue
from gien.tui import TUIProgressBar
from mailbox import mbox, Maildir
import os
import sys

def get_options():
    ap = ArgumentParser(description="Export Github issue trackers to local email storage")

    ap.add_argument("-I", "--archive-issues", default=False, action="store_true", help="Enable issue archiving.")
    ap.add_argument("-W", "--archive-wiki", default=False, action="store_true", help="Enable wiki archiving. Defaults to off.")
    ap.add_argument("-i", "--issues", default="all", choices=["all", "open", "closed"], help="Filter issues by state. Defaults to all.")
    ap.add_argument("-l", "--labels", action="store_true", default=False, help="If the issue has labels, add them to the email Subject: header. If the issue has been marked as closed, at a [CLOSED] label to the subject.")
    ap.add_argument("-o", "--output", default="output.mbox", help="Path to the output mbox file or Maildir. Will be created if it doesn't exist.")
    ap.add_argument("-p", "--password", required=True, help="Github API authentication: password")
    ap.add_argument("-r", "--repository", required=True, help="Github repository name the issue tracker of which shall be exported. Example: 2ion/gien")
    ap.add_argument("-t", "--threads", default=4, type=int, help="Number of worker threads. Defaults to 4.")
    ap.add_argument("-u", "--user", required=True, help="Github API authentication: user")
    ap.add_argument("--mailbox-type", type=str, choices=[ "mbox", "maildir" ], default="mbox", help="Specify the mailbox type to use. Defaults to mbox.")

    r = ap.parse_args()
    return r

def main():
    opts = get_options()
    data, repo = fetch_issues(opts)

    if opts.mailbox_type == "mbox":
        mb = mbox(opts.output)
    else:
        mb = Maildir(opts.output)
    mb.lock()

    if opts.archive_issues:
        with TUIProgressBar("Archiving issues", len(data)) as bar:
            with ThreadPoolExecutor(max_workers = opts.threads) as Exec:
                for thread in Exec.map(thread_issue, [ (opts, repo, issue,) for
                    issue in data ]):
                    bar.tick()
                    for msg in thread:
                        mb.add(msg)

    if opts.archive_wiki:
        with TUIProgressBar("Archiving the wiki", 1) as bar:
            for msg in thread_wiki(repo):
                mb.add(msg)

    mb.flush()
    mb.unlock()
    mb.close()

    return 0
