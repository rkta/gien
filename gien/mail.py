from email.message          import Message
from email.mime.image       import MIMEImage
from email.mime.multipart   import MIMEMultipart
from email.mime.text        import MIMEText
from email.utils            import formatdate
from hashlib                import md5
from markdown               import markdown
from pygit2                 import clone_repository
from tempfile               import TemporaryDirectory
from urllib.parse           import urlparse
import os
import re
import requests

def hexhex(res):
    h = md5()
    h.update(res.encode('utf-8'))
    return h.hexdigest()

def h_message_id(repo, issueid, commentid):
    return "<{}/issues/{}/{}@github.com>".format(repo, issueid, commentid)

def h_from(obj):
    return "{} <{}@noreply.github.com>".format(obj.user.login, obj.user.login)

def h_date(obj):
    return formatdate(obj.created_at.timestamp())

def h_subject(obj, in_reply=True):
    return ("Re: {}" if in_reply else "{}").format(obj.title)

def h_to(r):
    return "{} <{}@noreply.github.com>".format(r.full_name, r.name)

def mime_images(body):
    for url in [ m.group(1) for m in re.finditer("!\[.+?\]\((.+?)\)", body) ]:
        try:
            imgfile = urlparse(url).path.split("/")[-1]
            res = requests.get(url)
            img = MIMEImage(res.content)
            img.add_header("Content-Disposition", "attachment", filename = imgfile)
            yield img
        except:
            continue

def render_message(body, opts, **kwargs):
    p = MIMEMultipart()
    m = MIMEMultipart('alternative')
    for k,v in kwargs.items():
        p[k.replace("_", "-")] = v
    try:
        m.attach(MIMEText(markdown(body), 'html'))
        m.attach(MIMEText(body, 'plain'))
        p.attach(m)
        if opts.download_images:
            for img in mime_images(body):
                p.attach(img)
    except:
        pass
    return p

def thread_issue(tup):
    (opts, r, o) = tup

    common_Subject = "{}".format(o['issue'].title)
    if opts.labels:
        for label in o['issue'].labels:
            common_Subject += " [{}]".format(label.name)
        if o['issue'].closed_at:
            common_Subject += " [CLOSED]"
    common_Subject_Re = "Re: " + common_Subject

    common_To = h_to(r)

    thread = [ render_message(o['issue'].body, opts,
                Subject=common_Subject,
                From=h_from(o['issue']),
                To=common_To,
                Date=h_date(o['issue']),
                Message_ID=h_message_id(r.full_name, o['issue'].id, 0)) ]
    
# Mimic the behaviour of the Github email notification system
    common_root = thread[-1]['Message-ID']

    for comment in o['comments']:
        thread.append(render_message(comment.body, opts,
            Subject=common_Subject_Re,
            From=h_from(comment),
            To=common_To,
            Date=h_date(comment),
            Message_ID=h_message_id(r.full_name, o['issue'].id, comment.id),
            In_Reply_To=common_root,
            References=common_root))

    return thread

def thread_wiki(repo, opts):
    h_from = "wiki@noreply.github.com".format(repo.full_name)
    to = h_to(repo)
    root_msgid = "{}@wiki".format(hexhex(repo.full_name))

    thread = []

    with TemporaryDirectory() as DIR:
        clone_repository(repo.clone_url.replace(".git",".wiki"), DIR)
        for r,d,f in os.walk(DIR):
            if r.find(".git") > -1:
                continue
            for ff in f:
                path = "{}/{}".format(r,ff)
                if ff.endswith(".md"):
                    with open(path, "r") as FILE:
                        body = FILE.read()
                        date = formatdate()
                        subject = "[WIKI] {}".format(ff[:-3])
                        if len(thread)>0:
                            msgid = "{}@{}.wiki".format(hexhex(path), repo.name)
                            msg = render_message(body, opts,
                                    Subject     = subject,
                                    From        = h_from,
                                    Message_ID  = msgid,
                                    To          = to,
                                    In_Reply_To = root_msgid,
                                    References  = root_msgid,
                                    Date        = date)
                        else:
                            msgid = root_msgid
                            msg = render_message(body, opts,
                                    Subject    = subject,
                                    From       = h_from,
                                    Message_ID = msgid,
                                    To         = to,
                                    Date       = date)
                        thread.append(msg)
    return thread
