#!/usr/bin/env python3

# gien - export Github issue tracker contents to local email storage
# Copyright (C) 2016 2ion <dev@2ion.de>
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
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from github import Github, GithubException
from progressbar import ProgressBar, Bar
import email.utils
import mailbox
import markdown
import sys
import shutil

def die(*args):
    print("[error]", *args, file=sys.stderr)
    sys.exit(1)

def get_options():
    r = None
    ap = ArgumentParser(description="Export Github issue trackers to local email storage")
    ap.add_argument("-u", "--user",
            default=None,
            help="Github API authentication: user")
    ap.add_argument("-p", "--password",
            default=None,
            help="Github API authentication: password")
    ap.add_argument("-r", "--repository",
            default="2ion/gien",
            help="Github repository name the issue tracker of which shall be exported. Example: 2ion/gien")
    ap.add_argument("-i", "--issues",
            default="all",
            choices=["all", "open", "closed"],
            help="Filter issues by state. Defaults to all.")
    ap.add_argument("-o", "--output",
            default="output.mbox",
            help="Path to the output mbox file.")
    ap.add_argument("-l", "--labels",
            action="store_true",
            default=False,
            help="If the issue has labels, add them to the email Subject: header. If the issue has been marked as closed, at a [CLOSED] label to the subject.")
    r = ap.parse_args()
    if not (r.user and r.password):
        die("Missing option: both --user and --password are required.")
    return r

def fetch_rate_limit(api):
    limit = api.get_rate_limit()
    return "{}/{}, reset @ {}".format(limit.rate.remaining,
            limit.rate.limit, limit.rate.reset)

def fetch_data(opts):
    data = []
    repo = None
    try:
        api = Github(opts.user, opts.password)
        print("Rate limit:", fetch_rate_limit(api), file=sys.stderr)
        repo = api.get_repo(opts.repository)
        issues = repo.get_issues(state=opts.issues, direction="asc")
        data = [{
            "issue"    : i,
            "comments" : i.get_comments(), # ordered by ascending id
            "labels"   : i.get_labels() } for i in issues ] # ordered by created asc
    except GithubException as e:
        die("Github API exception", e)
    return data, repo

def h_message_id(repo, issueid, commentid):
    return "<{}/issues/{}/{}@github.com>".format(repo, issueid, commentid)

def h_from(obj):
    return "{} <{}@noreply.github.com>".format(obj.user.login, obj.user.login)

def h_date(obj):
    return email.utils.formatdate(obj.created_at.timestamp())

def h_subject(obj, in_reply=True):
    return ("Re: {}" if in_reply else "{}").format(obj.title)

def h_to(r):
    return "{} <{}@noreply.github.com>".format(r.full_name, r.name)

def render_message(body, **kwargs):
    m = MIMEMultipart('alternative')
    for k,v in kwargs.items():
        m[k.replace("_", "-")] = v
    m.attach(MIMEText(markdown.markdown(body), 'html'))
    m.attach(MIMEText(body, 'plain'))
    return m

def make_thread(opts, r, o):
    lbl = "{}: {}".format(o['issue'].id, o['issue'].title)
    (w, _) = shutil.get_terminal_size()
    lw = int(w * 0.6)
    if len(lbl)>lw-1:
        s = lw-4
        lbl = lbl[:s]
        lbl += "... "
    else:
        lbl = lbl.ljust(lw, ' ')
    pb = ProgressBar(
            widgets=[ lbl, Bar(left='[', right=']') ],
            maxval=o['issue'].comments+1).start()
    tick = 1

    common_Subject = "{}".format(o['issue'].title)
    if opts.labels:
        for label in o['issue'].labels:
            common_Subject += " [{}]".format(label.name)
        if o['issue'].closed_at:
            common_Subject += " [CLOSED]"
    common_Subject_Re = "Re: " + common_Subject

    common_To = h_to(r)

    thread = [ render_message(o['issue'].body,
                Subject=common_Subject,
                From=h_from(o['issue']),
                To=common_To,
                Date=h_date(o['issue']),
                Message_ID=h_message_id(r.full_name, o['issue'].id, 0)) ]
    
# Mimic the behaviour of the Github email notification system
    common_root = thread[-1]['Message-ID']

    for comment in o['comments']:
        thread.append(render_message(comment.body,
            Subject=common_Subject_Re,
            From=h_from(comment),
            To=common_To,
            Date=h_date(comment),
            Message_ID=h_message_id(r.full_name, o['issue'].id, comment.id),
            In_Reply_To=common_root,
            References=common_root))
        tick += 1
        pb.update(tick)

    pb.finish()
    return thread

def main():
    opts = get_options()
    data, repo = fetch_data(opts)

    mb = mailbox.mbox(opts.output)
    mb.lock()

    for issue in data:
        for msg in make_thread(opts, repo, issue):
            mb.add(msg)

    mb.flush()
    mb.unlock()
    mb.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
