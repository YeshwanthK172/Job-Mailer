"""Send mail from the user's own account over SMTP (use a Gmail *App Password*)."""
import mimetypes
import smtplib
import ssl
from email.message import EmailMessage


def send_email(smtp_user, smtp_password, to_addr, subject, body,
               attachment_bytes=None, attachment_name=None,
               host="smtp.gmail.com", port=465):
    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment_bytes and attachment_name:
        ctype, _ = mimetypes.guess_type(attachment_name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(attachment_bytes, maintype=maintype, subtype=subtype, filename=attachment_name)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def test_login(smtp_user, smtp_password, host="smtp.gmail.com", port=465):
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as server:
        server.login(smtp_user, smtp_password)
    return True
