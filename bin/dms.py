# coding=utf-8
import os
import re
import tempfile
import subprocess
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from os.path import basename
from smtplib import SMTP
from net.imap.imapclient import IMAPClient
from net.imap.walk import walk_parts
import json
import sched
import time

with open('users.json') as f:
    config = json.loads(f.read())


PDFSANDWITCH = '/Users/christian/src/pdfsandwich/pdfsandwich'
CONVERT = '/usr/local/bin/convert'
TESSERACT = '/usr/local/bin/tesseract'
GS = '/usr/local/bin/gs'
PDFUNITE = '/usr/local/bin/pdfunite'
UNPAPER = '/usr/local/bin/unpaper'


def main():
    for username, userconf in config['users'].items():
        process_user(username, **userconf)


def process_user(username: str, receiver: str, password: str, imap: str, smtp: str):
    server = IMAPClient(imap, use_uid=True, ssl=993)
    server.login(username, password)
    print(f'{username} connected')
    server.select_folder('INBOX')
    message_ids = server.search([b'NOT', b'KEYWORD', 'processed'])  # UNSEEN
    print('%d messages in INBOX' % len(message_ids))
    messages = server.fetch(message_ids, data=['ENVELOPE', 'BODYSTRUCTURE', 'RFC822.SIZE'])
    for mid, content in messages.items():

        bodystructure = content[b'BODYSTRUCTURE']
        text, attachments = walk_parts(bodystructure, msgid=mid, server=server)

        filenames = [k for k, v in attachments.items() if v[0] == 'application/pdf']
        _, data = walk_parts(bodystructure, msgid=mid, server=server, download_attachments=filenames)

        msg = MIMEMultipart()

        with tempfile.TemporaryDirectory() as tmpdirname:

            for filename, attachment in data.items():
                input_pdf = os.path.join(tmpdirname, filename)
                output_pdf = input_pdf.replace('.pdf', '_ocr.pdf')
                output_txt = input_pdf.replace('.pdf', '.txt')
                with open(input_pdf, 'wb') as f:
                    if attachment[2] is None:
                        continue
                    f.write(attachment[2])

                    # my_env = os.environ.copy()
                    # my_env["PATH"] = "/usr/local/bin/:/usr/sbin:/sbin:" + my_env["PATH"]
                    # process = subprocess.Popen(
                    #     [PDFSANDWITCH, path, '-convert', CONVERT, '-tesseract', TESSERACT, '-gs', GS, '-pdfunite',
                    #      PDFUNITE, '-unpaper', UNPAPER, '-lang', 'deu+fra+eng'], env=my_env)
                    # process.wait()

                    process = subprocess.Popen(['/usr/local/bin/ocrmypdf', '-l', 'deu+fra+eng', '--sidecar', output_txt, input_pdf, output_pdf])
                    process.wait()

                # ocr_path = os.path.join(tmpdirname, filename.replace('.pdf', '_ocr.txt'))

                # process = subprocess.Popen(['pdftotext', output_path, ocr_path], env=my_env)
                # process.wait()

                with open(output_pdf, "rb") as fil:
                    part = MIMEApplication(fil.read(), Name=basename(f.name))
                    part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f.name)
                    msg.attach(part)
                with open(output_txt, "rb") as fil:
                    part = MIMEApplication(fil.read(), Name=basename(f.name.replace('pdf', 'txt')))
                    fil.seek(0)
                    subject = fil.readline().decode('utf8').strip()
                    msg['Subject'] = re.sub(r'([^\s\w]|_)+', '', subject)
                    part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f.name.replace('pdf', 'txt'))
                    msg.attach(part)

        conn = SMTP(smtp, port=587)
        conn.set_debuglevel(False)

        msg['From'] = username  # some SMTP servers will do this automatically, not all

        conn.login(username, password)
        try:
            conn.sendmail(username, [receiver], msg.as_string())
            server.add_flags([mid], ['processed'])
        finally:
            conn.close()

    server.logout()
    server.shutdown()


if __name__ == "__main__":
    s = sched.scheduler(time.time, time.sleep)

    def do_something(sc):
        # do your stuff
        main()
        s.enter(60, 1, do_something, (sc,))

    s.enter(0, 1, do_something, (s,))
    s.run()
