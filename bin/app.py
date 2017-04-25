# coding=utf-8
import argparse
import base64
import curses
import datetime
import imaplib
from email.header import decode_header, make_header
import sys
from typing import List, Tuple, Iterable
import toolz
import npyscreen
from net.imap.imapclient import IMAPClient
from net.imap.response_types import Address, BodyData


IMAP_SEARCH_FIELDS = {
    'ANSWERED': None,
    'BCC': str,
    'BEFORE': datetime.date,
    'BODY': str,
    'CC': str,
    'DELETED': None,
    'DRAFT': None,
    'FLAGGED': None,
    'FROM': str,
    'HEADER': str,
    'KEYWORD': str,
    'LARGER': int,
    'NEW': None,
    'OLD': None,
    'ON': datetime.date,
    'RECENT': None,
    'SEEN': None,
    'SENTBEFORE': datetime.date,
    'SENTON': datetime.date,
    'SENTSINCE': datetime.date,
    'SINCE': datetime.date,
    'SMALLER': int,
    'SUBJECT': str,
    'TEXT': str,
    'TO': str,
    'UID': int,
    'UNANSWERED': None,
    'UNDELETED': None,
    'UNDRAFT': None,
    'UNFLAGGED': None,
    'UNKEYWORD': None,
    'UNSEEN': None
}


# seach, see https://tools.ietf.org/html/rfc3501.html#section-6.4.4

# ALL
#      All messages in the mailbox; the default initial key for
#      ANDing.
#
#   ANSWERED
#      Messages with the \Answered flag set.
#
# BCC <string>
#      Messages that contain the specified string in the envelope
#      structure's BCC field.
#
#   BEFORE <date>
#      Messages whose internal date (disregarding time and timezone)
#      is earlier than the specified date.
#
#   BODY <string>
#      Messages that contain the specified string in the body of the
#      message.
#
#   CC <string>
#      Messages that contain the specified string in the envelope
#      structure's CC field.
#
#   DELETED
#      Messages with the \Deleted flag set.
#
#   DRAFT
#      Messages with the \Draft flag set.
#
#   FLAGGED
#      Messages with the \Flagged flag set.
#
#   FROM <string>
#      Messages that contain the specified string in the envelope
#      structure's FROM field.
#
#   HEADER <field-name> <string>
#      Messages that have a header with the specified field-name (as
#      defined in [RFC-2822]) and that contains the specified string
#      in the text of the header (what comes after the colon).  If the
#      string to search is zero-length, this matches all messages that
#      have a header line with the specified field-name regardless of
#      the contents.
#
#   KEYWORD <flag>
#      Messages with the specified keyword flag set.
#
#   LARGER <n>
#      Messages with an [RFC-2822] size larger than the specified
#      number of octets.
#
#   NEW
#      Messages that have the \Recent flag set but not the \Seen flag.
#      This is functionally equivalent to "(RECENT UNSEEN)".
#
# NOT <search-key>
#    Messages that do not match the specified search key.
#
# OLD
#    Messages that do not have the \Recent flag set.  This is
#    functionally equivalent to "NOT RECENT" (as opposed to "NOT
#    NEW").
#
# ON <date>
#    Messages whose internal date (disregarding time and timezone)
#    is within the specified date.
#
# OR <search-key1> <search-key2>
#    Messages that match either search key.
#
# RECENT
#    Messages that have the \Recent flag set.
#
# SEEN
#    Messages that have the \Seen flag set.
#
# SENTBEFORE <date>
#    Messages whose [RFC-2822] Date: header (disregarding time and
#    timezone) is earlier than the specified date.
#
# SENTON <date>
#    Messages whose [RFC-2822] Date: header (disregarding time and
#    timezone) is within the specified date.
#
# SENTSINCE <date>
#    Messages whose [RFC-2822] Date: header (disregarding time and
#    timezone) is within or later than the specified date.
#
# SINCE <date>
#    Messages whose internal date (disregarding time and timezone)
#    is within or later than the specified date.
#
# SMALLER <n>
#    Messages with an [RFC-2822] size smaller than the specified
#    number of octets.
#
# SUBJECT <string>
#    Messages that contain the specified string in the envelope
#    structure's SUBJECT field.
#
# TEXT <string>
#    Messages that contain the specified string in the header or
#    body of the message.
#
# TO <string>
#    Messages that contain the specified string in the envelope
#    structure's TO field.
#
# UID <sequence set>
#    Messages with unique identifiers corresponding to the specified
#    unique identifier set.  Sequence set ranges are permitted.
#
# UNANSWERED
#    Messages that do not have the \Answered flag set.
#
# UNDELETED
#    Messages that do not have the \Deleted flag set.
#
# UNDRAFT
#    Messages that do not have the \Draft flag set.
#
# UNFLAGGED
#    Messages that do not have the \Flagged flag set.
#
# UNKEYWORD <flag>
#    Messages that do not have the specified keyword flag set.
#
# UNSEEN
#    Messages that do not have the \Seen flag set.


def parse_command_line_args():
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--host', required=True, dest='host', action='store', help='IMAP host connect to')
    parser.add_argument('--username', required=True, dest='username', action='store', help='Username to login with')
    parser.add_argument('--password', required=True, dest='password', action='store', help='Password to login with')
    parser.add_argument('--port', dest='port', action='store', type=int, default=993,
                        help='IMAP port to use (default is 143, or 993 for SSL)')
    parser.add_argument('--ssl', dest='ssl', action='store_true', default=True, help='Use SSL connection')
    parser.add_argument('--file', dest='file', action='store', default=None, help='Config file (same as livetest)')
    parser.add_argument('--version', action='version', version='0.00001')

    return parser.parse_args()


args = parse_command_line_args()
print('Connecting...')
# client = create_client_from_config(args)
server = IMAPClient(args.host, use_uid=True, ssl=args.ssl)
server.login(args.username, args.password)
print('Connected.')

select_info = server.select_folder('INBOX')
print('%d messages in INBOX' % select_info[b'EXISTS'])

messages = server.search([b'NOT', b'DELETED'])
print("%d messages that aren't deleted" % len(messages))

print(server.search(['KEYWORD', 'test']))

server.add_flags([1], ['test'])
print(server.search(['KEYWORD', 'test']))

server.remove_flags([1], ['test'])
print(server.search(['KEYWORD', 'test']))


message_id = 151

m140 = server.fetch([message_id], data=['ENVELOPE', 'BODYSTRUCTURE', 'FLAGS', 'RFC822.SIZE'])

bodystructure_ = m140[message_id][b'BODYSTRUCTURE']


def walk_parts(msg: BodyData, msgid, download_attachments=None):

    text = ''
    html = ''
    attachments = {}

    if download_attachments is None:
        download_attachments = []

    for part, body_number in flatten_message(msg):

        dtypes = part.dtypes
        content_type = part.content_type

        if dtypes:
            for key, filename in dtypes.items():
                key = key.lower()
                decoded_data = None
                if key == b'filename':
                    if filename.decode('utf8') in download_attachments:
                        BODY = 'BODY[{}]'.format(body_number).encode('utf8')
                        data = server.fetch([msgid], data=[BODY])[msgid][BODY]
                        decoder = part[5]

                        if decoder == b'base64':
                            decoded_data = base64.b64decode(data)
                        else:
                            pass
                        with open(filename.decode('utf8'), 'wb') as f:
                            f.write(decoded_data)

                    attachments[filename.decode('utf8')] = (content_type, part.size, decoded_data)

        else:
            if body_number.startswith('1'):
                BODY = 'BODY[{}]'.format(body_number)  # use correct
                key = BODY.encode('utf8')

                decoder = part[5]
                charset = part[2][1].decode('utf8')

                if content_type in ['text/plain', 'text/html'] and not text:  # .get_content_type()
                    data = server.fetch([msgid], data=[BODY])[msgid][key]

                    if decoder == b'base64':
                        decoded_data = base64.b64decode(data)
                    else:
                        decoded_data = data

                    text = decoded_data.decode(charset)

                    continue
                # if not text and content_type == 'text/html':  # .get_content_type()
                #     html = server.fetch([msgid], data=[BODY])[msgid][key].decode(charset).encode('utf8')
                #     continue

            ctypes = part.ctypes
            if not ctypes:
                continue
            for key, val in ctypes.items():
                if key.lower() == b'name':
                    filename = val.decode('utf8')

                    BODY = 'BODY[{}]'.format(body_number).encode('utf8')
                    m = server.fetch([msgid], data=[BODY])[msgid]

                    break

    print(text, html, attachments)
    return text, html, attachments


def flatten_message(msg: BodyData) -> Iterable[Tuple[BodyData, str]]:
    if not msg.is_multipart:
        stack = [(msg, '1')]
    else:
        stack = [(m, str(n)) for n, m in enumerate(msg[0], 1)]
    flattened_parts = []
    while stack:  # flatten message parts and enumerate them
        part, body_number = stack.pop()
        if part and part.is_multipart:
            for subpart in part:
                if type(subpart) == list:
                    for i, s in enumerate(subpart, 1):
                        stack.append((s, body_number + '.' + str(i)))
            continue
        flattened_parts.append((part, body_number))
    return reversed(flattened_parts)


# msg = email.message_from_string(m140[140][b'BODYSTRUCTURE'].decode('utf8'))

text, html, attachments = walk_parts(bodystructure_, msgid=message_id)
# text, html, attachments = walk_parts(bs, msgid=message_id, download_attachments=['1546085.pdf'])

exit(1)
# for part in msg.walk():
#     if part.is_multipart():
#         continue

#For example, a simple text message of 48 lines and 2279 octets
 # can have a body structure of: ("TEXT" "PLAIN" ("CHARSET"
 # "US-ASCII") NIL NIL "7BIT" 2279 48)


#
# x = server.fetch([141], data=['BODY[HEADER.FIELDS (SUBJECT FROM)]', 'BODY.PEEK[1] <0.100>'])
# server.fetch([140], data=['BODY[1]'])[140]
#
#
# base64.b64decode(server.fetch([140], data=['BODY[1]'])[140][b'BODY[1]'])
# b'Sehr geehrter Herr Dr. Christian Wengert!\n\nVielen Dank f\xc3\xbcr Ihre sofortige Antwort und eine detaillierte Beschreibung des T\xc3\xa4tigkeitsfeldes vom Unternehmen.\nDie weiteren Informationen \xc3\xbcber die Stelle und Ihr Unternehmen haben mein Interesse noch verst\xc3\xa4rkt und ich bin deshalb noch st\xc3\xa4rker an dem Stellenangebot interessiert.\n\nMit bestem Dank und freundlichen Gr\xc3\xbc\xc3\x9fen,\n\nAron Birsa.\n\n-------- Original Message --------\nSubject: Re: Python Anwendungsprogrammierer\nLocal Time: April 21, 2017 10:47 AM\nUTC Time: April 21, 2017 8:47 AM\nFrom: christian@codefour.ch\nTo: Aron Birsa <aron@birsa.ch>\njobs-rav@codefour.ch <jobs-rav@codefour.ch>\n\nGuten Tag Aron\n\nVielen Dank f\xc3\xbcr Dein Mail.\n\ncodefour ist aus einer anderen Firma (Smart Power Pool) hervorgegangen. In dieser Firma haben wir Studien und Simulationen f\xc3\xbcr Energieversorger gemacht (vorwiegend mit Numpy und Scipy).\n\nDaraus hat sich ein gr\xc3\xb6\xc3\x9feres Software-Projekt ergeben, welches nun in der reinen Software-Firma codefour weitergef\xc3\xbchrt wird: Der Auftrag ist die Entwicklung eines Asset Management Systems. Die Idee hinter einem Asset Management System ist, Infrastruktur (Strom, Eisenbahn, Wasser, etc) von A-Z zu verwalten. Dazu geh\xc3\xb6rt einerseits, dass man regelm\xc3\xa4\xc3\x9fige Inspektionen per Tablet durchfuehren kann (im Feld: Was ist der Kurzschlussstrom der Mittelspannungsanlage) aber auch die gewonnenen Daten sinnvoll analysieren und auswerten kann, damit zuk\xc3\xbcnftige Investition- und Ersatzentscheide optimal gef\xc3\xa4llt werden k\xc3\xb6nnen (im B\xc3\xbcro: Welche Trafos riskieren bald einen Ausfall).\n\nDas Projekt war urspr\xc3\xbcnglich ein Nebenprojekt, hat sich aber zu einem wichtigen Projekt entwickelt. Die Stromfirma mit der ich das begonnen hat, sucht nach neuen M\xc3\xa4rkten und hat sich entschieden, dieses Projekt nun in den Markt zu pushen (nicht nur Strom, sondern jedwede groessere Infrastruktur).\n\nDas gibt nun ziemlich viel Arbeit und daher suche ich Verst\xc3\xa4rkung! Ich denke, dass der spannende Teil erst jetzt beginnt.\n- Wie kann man Voraussagen f\xc3\xbcr die Zukunft treffen?\n- Was sind gute Investitionsentscheide?\n- Sollen wir die Blockchain einf\xc3\xbchren, damit die Daten wirklich unver\xc3\xa4nderbar sind und immer nachvollziehbar ist, was wann gemacht wurde (das ist aus gesetzlichen Gr\xc3\xbcnden: Sollte mal ein Unfall passieren kann man beweisen, dass man das ordnungsgem\xc3\xa4\xc3\x9f gewartet hat und wer)\n- Verbindung von mehr Daten und anderen Systemen\n\nF\xc3\xbcr den bisherigen Erfolg war sehr wichtig, dass wir auch mal mitgehen zun einer Inspektion und uns so eine Schalttafel, Trafostration, Turbine auch mal ansehen und wirklich verstehen wo der Schuh dr\xc3\xbcckt.\n\nDie Arbeit beinhaltet:\n- Entwicklung von Python (90%)\n- Weiterentwicklung der bestehenden App\n- Implementation neuer Funktionen\n- Tests\n- Entwicklung am Frontend (JS/CSS, wobei wir versuchen m\xc3\xb6glichst wenig JS zu machen)\n\nKlingt das interessant f\xc3\xbcr Dich?\n\nBeste Gruesse\n\nChristian\n\nOn 20 Apr 2017, at 08:13, Aron Birsa <aron@birsa.ch> wrote:\n\nSehr geehrter Herr dr. Christian Wengert!\n\nIch sah Ihre Stellenanzeige f\xc3\xbcr die ausgeschriebene Position als Python Programmierer auf der Internetseite http://ec.europa.eu/ und war sofort begeistert.\nDas T\xc3\xa4tigkeitsfeld des Unternehmens Codefour finde ich sehr interessant.\nMein LinkedIn Profil finden Sie unter dieser Internetadresse https://www.linkedin.com/in/aron-birsa-15b75629/.\nFalls ich Ihren Vorstellungen entspreche, w\xc3\xbcrde Ich mich sehr freuen, wenn Sie mir zus\xc3\xa4tzliche Informationen zur Verf\xc3\xbcgung stellen k\xc3\xb6nnten.\n\nMit bestem Dank und freundlichen Gr\xc3\xbc\xc3\x9fen,\n\nAron Birsa.\n\n<stellenanzeige.png>'
# base64.b64decode(server.fetch([140], data=['BODY[2]'])[140][b'BODY[2]'])
# b'<div>Sehr geehrter Herr Dr. Christian Wengert!<br></div><div><br></div><div>Vielen Dank f\xc3\xbcr Ihre sofortige Antwort und eine detaillierte Beschreibung des T\xc3\xa4tigkeitsfeldes vom Unternehmen.<br></div><div>Die weiteren Informationen \xc3\xbcber die Stelle und Ihr Unternehmen haben mein Interesse noch verst\xc3\xa4rkt und ich bin deshalb noch st\xc3\xa4rker an dem Stellenangebot interessiert.<br></div><div><br></div><div>Mit bestem Dank und freundlichen Gr\xc3\xbc\xc3\x9fen,<br></div><div><br></div><div>Aron Birsa.<br></div><div class="protonmail_signature_block protonmail_signature_block-empty"><div class="protonmail_signature_block-user protonmail_signature_block-empty"><div><br></div></div><div class="protonmail_signature_block-proton protonmail_signature_block-empty"><br></div></div><div><br></div><blockquote class="protonmail_quote" type="cite"><div>-------- Original Message --------<br></div><div>Subject: Re: Python Anwendungsprogrammierer<br></div><div>Local Time: April 21, 2017 10:47 AM<br></div><div>UTC Time: April 21, 2017 8:47 AM<br></div><div>From: christian@codefour.ch<br></div><div>To: Aron Birsa &lt;aron@birsa.ch&gt;<br></div><div>jobs-rav@codefour.ch &lt;jobs-rav@codefour.ch&gt;<br></div><div><br></div><div>Guten Tag Aron<br></div><div class=""><br></div><div class="">Vielen Dank f\xc3\xbcr Dein Mail.&nbsp;<br></div><div class=""><br></div><div class="">codefour ist aus einer anderen Firma (Smart Power Pool) hervorgegangen. In dieser Firma haben wir Studien und Simulationen f\xc3\xbcr Energieversorger gemacht (vorwiegend mit Numpy und Scipy).&nbsp;<br></div><div class=""><div>Daraus hat sich ein gr\xc3\xb6\xc3\x9feres Software-Projekt ergeben, welches nun in der reinen Software-Firma codefour weitergef\xc3\xbchrt wird:&nbsp;Der Auftrag ist die Entwicklung eines Asset Management Systems. Die Idee hinter einem Asset Management System ist, Infrastruktur (Strom, Eisenbahn, Wasser, etc) von A-Z zu verwalten. Dazu geh\xc3\xb6rt &nbsp;einerseits, dass man regelm\xc3\xa4\xc3\x9fige Inspektionen per Tablet durchfuehren kann (im Feld: Was ist der Kurzschlussstrom der Mittelspannungsanlage) aber auch die gewonnenen Daten sinnvoll analysieren und auswerten kann, damit zuk\xc3\xbcnftige Investition- und Ersatzentscheide optimal gef\xc3\xa4llt werden k\xc3\xb6nnen (im B\xc3\xbcro: Welche Trafos riskieren bald einen Ausfall).<br></div><div><br></div><div>Das Projekt war urspr\xc3\xbcnglich ein Nebenprojekt, hat sich aber zu einem wichtigen Projekt entwickelt. Die Stromfirma mit der ich das begonnen hat, sucht nach neuen M\xc3\xa4rkten und hat sich entschieden, dieses Projekt nun in den Markt zu pushen (nicht nur Strom, sondern jedwede groessere Infrastruktur).<br></div><div><br></div><div>Das gibt nun ziemlich viel Arbeit und daher suche ich Verst\xc3\xa4rkung! Ich denke, dass der spannende Teil erst jetzt beginnt.&nbsp;<br></div></div><div class="">- Wie kann man Voraussagen f\xc3\xbcr die Zukunft treffen?&nbsp;<br></div><div class="">- Was sind gute Investitionsentscheide?&nbsp;<br></div><div class="">- Sollen wir die Blockchain einf\xc3\xbchren, damit die Daten wirklich unver\xc3\xa4nderbar sind und immer nachvollziehbar ist, was wann gemacht wurde (das ist aus gesetzlichen Gr\xc3\xbcnden: Sollte mal ein Unfall passieren kann man beweisen, dass man das ordnungsgem\xc3\xa4\xc3\x9f gewartet hat und wer)<br></div><div class="">- Verbindung von mehr Daten und anderen Systemen<br></div><div class=""><br></div><div class=""><div><br></div><div>F\xc3\xbcr den bisherigen Erfolg war sehr wichtig, dass wir auch mal mitgehen zun einer Inspektion und uns so eine Schalttafel, Trafostration, Turbine auch mal ansehen und wirklich verstehen wo der Schuh dr\xc3\xbcckt.<br></div></div><div class=""><br></div><div class=""><br></div><div class="">Die Arbeit beinhaltet:&nbsp;<br></div><div class="">- Entwicklung von Python (90%)<br></div><div class="">&nbsp; - Weiterentwicklung der bestehenden App<br></div><div class="">&nbsp; - Implementation neuer Funktionen&nbsp;<br></div><div class="">&nbsp; - Tests<br></div><div class="">- Entwicklung am Frontend (JS/CSS, wobei wir versuchen m\xc3\xb6glichst wenig JS zu machen)<br></div><div class=""><div><br></div><div><br></div><div>Klingt das interessant f\xc3\xbcr Dich?&nbsp;<br></div></div><div class=""><br></div><div class=""><br></div><div class="">Beste Gruesse<br></div><div class=""><br></div><div class="">Christian<br></div><div class=""><br></div><div class=""><br></div><div class=""><div><br></div><div><blockquote class="" type="cite"><div class="">On 20 Apr 2017, at 08:13, Aron Birsa &lt;<a class="" href="mailto:aron@birsa.ch" rel="noreferrer nofollow noopener">aron@birsa.ch</a>&gt; wrote:<br></div><div><br></div><div class=""><div class="">Sehr geehrter Herr dr. Christian Wengert!<br></div><div class=""><br></div><div class="">Ich sah Ihre Stellenanzeige f\xc3\xbcr die ausgeschriebene Position als Python Programmierer auf der Internetseite <a class="" href="http://ec.europa.eu/" rel="noreferrer nofollow noopener">http://ec.europa.eu/</a> und war sofort begeistert.<br></div><div class="">Das T\xc3\xa4tigkeitsfeld des Unternehmens Codefour finde ich sehr interessant.<br></div><div class="">Mein LinkedIn Profil finden Sie unter dieser Internetadresse <a class="" href="https://www.linkedin.com/in/aron-birsa-15b75629/" rel="noreferrer nofollow noopener">https://www.linkedin.com/in/aron-birsa-15b75629/</a>.<br></div><div class="">Falls ich Ihren Vorstellungen entspreche, w\xc3\xbcrde Ich mich sehr freuen, wenn Sie mir zus\xc3\xa4tzliche Informationen zur Verf\xc3\xbcgung stellen k\xc3\xb6nnten.<br></div><div class=""><br></div><div class="">Mit bestem Dank und freundlichen Gr\xc3\xbc\xc3\x9fen,<br></div><div class=""><br></div><div class="">Aron Birsa.<br></div><div class="protonmail_signature_block protonmail_signature_block-empty"><div class="protonmail_signature_block-user protonmail_signature_block-empty"><div class=""><br></div></div><div class="protonmail_signature_block-proton protonmail_signature_block-empty"><br></div></div><div class=""><br></div><div><span>&lt;stellenanzeige.png&gt;</span><br></div></div></blockquote></div></div></blockquote><div><br></div>'


# das hier mit attachment
    # http://stackoverflow.com/questions/6225763/downloading-multiple-attachments-using-imaplib
    # x = server.fetch([139], data=['BODYSTRUCTURE'])
    # f = x[139][b'BODYSTRUCTURE']


def process_command(query: str) -> List[int]:
    if query == 'quit' or query == 'q':
        sys.exit(1)
    if query == 'help':
        pass  # todo show all search options

    terms = []

    processed_query = [x.split(':') for x in query.split()]

    grouped = toolz.groupby(lambda x: x[0], processed_query)

    for group, items in grouped.items():
        if len(items) > 1:
            terms.append('OR')

        for item in items:
            if len(item) == 2:
                field, term = item
            else:
                field, term = 'text', item[0]
            field = field.upper()
            if field.startswith('-'):
                field = field[1:]
                terms.append('NOT')
            convert = IMAP_SEARCH_FIELDS.get(field, None)
            if field in IMAP_SEARCH_FIELDS:
                terms.append(field)
            if term and convert:
                terms.append(convert(term))
    mails = []
    if terms:
        try:
            mails = server.search(terms)
        except ValueError:  # no criteria specidfied
            pass
        except imaplib.IMAP4.error:
            pass
        except Exception as e:  # todo what else
            pass

    return mails


def process_from(data: Address) -> str:
    name = data.name.decode('utf8') if data.name else ''
    if name.startswith('='):
        name = make_header(decode_header(name))
    mailbox = data.mailbox.decode('utf8') if data.mailbox else ''
    host = data.host.decode('utf8') if data.host else ''

    return f'{name} <{mailbox}@{host}>'
    # return data.decode('utf8').replace('From: ', '').strip()


def process_subject(data: bytes) -> str:

    name = make_header(decode_header(data.decode('utf8')))
    return name
    # return data.decode('utf8').replace('From: ', '').strip()


def process_body(k: int, data: BodyData) -> str:
    content = ''
    if data.is_multipart:

        for part in data[0]:
            # for typ, subtyp, charset_and_encoding, body_id, body_description, body_encoding, body_size, nmd5 in part:
                pass
    else:
        body_1 = server.fetch([k], data=['BODY[1]'])[k]

    return content


def process_size(data) -> int:
    return int(data)  # todo make human readable


def process_flags(data) -> str:
    return data  # todo split and show nicely

#
# def write_file(filename, addr, data):
#     os.chdir(addr)
#     fd = open(filename, "wb")
#     fd.write(data)
#     fd.close()
#
#
# def gen_filename(name, mtyp, addr, date, n):
#     timepart = strftime("%d %b %y %H_%M_%S")
#     file = email.Header.decode_header(name)[0][0]
#     file = os.path.basename(file)
#     print
#     "Saved attachment  " + file + "  from  " + addr
#     print
#     "\n"
#     path = os.path.join('.', file)
#     pre, ext = os.path.splitext(file)
#     pre = pre + "_" + timepart
#     path = '%s%s' % (os.path.join('.', pre), ext)
#     return path
#
#

#
# def write_file(filename, addr, data):
#     os.chdir(addr)
#     fd = open(filename, "wb")
#     fd.write(data)
#     fd.close()
#
#
# def gen_filename(name, mtyp, addr, date, n):
#     timepart = strftime("%d %b %y %H_%M_%S")
#     file = email.Header.decode_header(name)[0][0]
#     file = os.path.basename(file)
#     print("Saved attachment  " + file + "  from  " + addr)
#
#     path = os.path.join(AttachDir, file)
#     pre, ext = os.path.splitext(file)
#     pre = pre + "_" + timepart
#     path = '%s%s' % (os.path.join(AttachDir, pre), ext)
#     return path
#
# #
# def walk_parts(msg, addr, date, count, msgnum):
#     for part in msg.walk():
#         if part.is_multipart():
#             continue
#         dtypes = part.get_params(None, 'Content-Disposition')
#         if not dtypes:
#             if part.get_content_type() == 'text/plain':
#                 continue
#             ctypes = part.get_params()
#             if not ctypes:
#                 continue
#             for key, val in ctypes:
#                 if key.lower() == 'name':
#                     filename = gen_filename(val, part.get_content_type(), addr, date, count)
#                     break
#             else:
#                 continue
#         else:
#             attachment, filename = None, None
#             for key, val in dtypes:
#                 key = key.lower()
#                 if key == 'filename':
#                     filename = val
#                 if key == 'attachment':
#                     attachment = 1
#             if not attachment:
#                 continue
#             filename = gen_filename(filename, part.get_content_type(), addr, date, count)
#
#         try:
#             data = part.get_payload(decode=1)
#         except:
#             typ, val = sys.exc_info()[:2]
#             warn("Message %s attachment decode error: %s for %s ``%s''"
#                  % (msgnum, str(val), part.get_content_type(), filename))
#             continue
#
#         if not data:
#             warn("Could not decode attachment %s for %s"
#                  % (part.get_content_type(), filename))
#             continue
#
#         if type(data) is type(msg):
#             count = walk_parts(data, addr, date, count, msgnum)
#             continue
#
#         if SaveAttachments:
#             exists = "0"
#             try:
#                 curdir = os.getcwd()
#                 list = os.listdir('.\\')
#                 for name in list:
#                     if name == addr:
#                         exists = "1"
#                         break
#                 if exists == "1":
#                     write_file(filename, addr, data)
#                     os.chdir(curdir)
#                 else:
#                     os.mkdir(addr)
#                     write_file(filename, addr, data)
#                     os.chdir(curdir)
#                     exists == "0"
#                     os.chdir(curdir)
#             except IOError, val:
#                 error('Could not create "%s": %s' % (filename, str(val)))
#
#         count += 1
#
#     return count

class ActionControllerSearch(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^.*', self.set_search, False)  # ^ = beginning

    def set_search(self, command_line, widget_proxy, live):

        self.parent.wCommand.value = ''
        ids = process_command(command_line)
        # todo has attachment?
        mails = server.fetch(ids, data=['ENVELOPE', 'BODY', 'FLAGS', 'RFC822.SIZE'])

        # data = []
        # [data.append([k, b'BODY[HEADER.FIELDS (SUBJECT FROM)]', b'BODY[1][0]', 'FLAGS', 'RFC822.SIZE']) for k,v in mails.items()]

        self.parent.wMain.values = []
        for k, v in mails.items():
            row = [v[b'ENVELOPE'],
                   process_from(v[b'ENVELOPE'].from_[0]),
                   process_subject(v[b'ENVELOPE'].subject),
                   process_body(k, v[b'BODY']),
                   process_flags(v[b'FLAGS']),
                   process_size(v[b'RFC822.SIZE'])]

            self.parent.wMain.values.append(row)
        self.parent.wMain.update()


class MyTextCommandBox(npyscreen.TextCommandBox):
    def __init__(self, screen,
                 history=True,
                 history_max=1000,  # todo make persistent
                 set_up_history_keys=True,
                 *args, **kwargs):
        super(MyTextCommandBox, self).__init__(screen, history, history_max, set_up_history_keys, *args, **kwargs)


class MyGrid(npyscreen.GridColTitles):
    def __init__(self, screen, col_titles=None, *args, **kwargs):
        super(MyGrid, self).__init__(screen, col_titles, *args, **kwargs)
        self.complex_handlers = []
        self.handlers = {
            curses.ascii.NL: self.select,
            curses.ascii.CR: self.select,
            curses.KEY_UP: self.h_move_line_up,
            curses.KEY_LEFT: self.h_move_cell_left,
            curses.KEY_DOWN: self.h_move_line_down,
            curses.KEY_RIGHT: self.h_move_cell_right,
            curses.KEY_NPAGE: self.h_move_page_down,
            curses.KEY_PPAGE: self.h_move_page_up,
            curses.KEY_HOME: self.h_show_beginning,
            curses.KEY_END: self.h_show_end,
            ord('g'): self.h_show_beginning,
            ord('G'): self.h_show_end,
            curses.ascii.TAB: self.h_exit,
            curses.KEY_BTAB: self.h_exit_up,
            '^P': self.h_exit_up,
            '^N': self.h_exit_down,
            ord('q'): self.h_exit,
            curses.ascii.ESC: self.h_exit,
            curses.KEY_MOUSE: self.h_exit_mouse,
            "r": self.reply,
            "f": self.forward,
            "d": self.delete,
            "l": self.label,
            "c": self.compose,
        }

    def set_up_handlers(self):
        super(MyGrid, self).set_up_handlers()

    def compose(self, *args, **kwargs):
        pass

    def reply(self, *args, **kwargs):
        pass

    def forward(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def label(self, *args, **kwargs):
        pass

    def select(self, *args, **kwargs):
        a, b = self.edit_cell
        mail_id = self.values[a][0]
        # todo fetch message and siplay it on a separate screen
        # todo can we do tabbed?


class FmSearchActive(npyscreen.FormMuttActive):
    ACTION_CONTROLLER = ActionControllerSearch
    MAIN_WIDGET_CLASS = MyGrid
    MAIN_WIDGET_CLASS_START_LINE = 3
    STATUS_WIDGET_CLASS = npyscreen.Textfield
    STATUS_WIDGET_X_OFFSET = 0
    COMMAND_WIDGET_CLASS = MyTextCommandBox
    COMMAND_WIDGET_NAME = 'Search'
    COMMAND_WIDGET_BEGIN_ENTRY_AT = None
    COMMAND_ALLOW_OVERRIDE_BEGIN_ENTRY_AT = True


class MailBox(npyscreen.NPSApp):
    def main(self):
        F = FmSearchActive()
        F.wStatus1.value = "mail/inbox "
        F.wStatus2.value = "search "

        MAXY, MAXX = F.lines, F.columns

        value = 'drafts: 0'
        p = F.add(npyscreen.Textfield, name="Text:", relx=MAXX-len(value) - 2, rely=1)
        # p.additional_y_offset = 3
        p.value = value
        p.editable = False

        F.wMain.values = []

        F.wMain.col_titles = ['date', 'from', 'subject', 'content', 'flags', 'size']



        # F.wMain.additional_y_offset = 10

        F.edit()


class Screens(npyscreen.NPSApp):  # shows which screens are available
    def main(self):
        pass


class Rules(npyscreen.NPSApp):  # Set up rules
    def main(self):
        pass


class ReadMessage(npyscreen.NPSApp):  # Read message
    def main(self):
        pass


class WriteMessage(npyscreen.NPSApp):  # Write message
    def main(self):
        pass


class Settings(npyscreen.NPSApp):  # Settings
    def main(self):
        pass

if __name__ == "__main__":
    App = MailBox()
    App.run()

if __name__ == "__main__":
    App = MailBox()
    App.run()
