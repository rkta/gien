from email.mime.multipart   import MIMEMultipart
from email.mime.text        import MIMEText
from markdown               import markdown

def render_multipart_message(body, **kwargs):
    m = MIMEMultipart('alternative')
    for k,v in kwargs.items():
        m[k.replace("_", "-")] = v
    try:
        m.attach(MIMEText(markdown(body), 'html'))
        m.attach(MIMEText(body, 'plain'))
    except:
        pass
    return m
