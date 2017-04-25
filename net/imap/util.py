# Copyright (c) 2015, Menno Smits
# Released subject to the New BSD License
# Please see http://en.wikipedia.org/wiki/BSD_licenses

from __future__ import unicode_literals

from email.header import make_header, decode_header

from six import binary_type, text_type

from net.imap.imapclient import IMAPClient
from net.imap.response_types import Address, BodyData


def to_unicode(s):
    if isinstance(s, binary_type):
        return s.decode('ascii')
    return s


def to_bytes(s, charset='ascii'):
    if isinstance(s, text_type):
        return s.encode(charset)
    return s


def process_from(data: Address) -> str:
    name = data.name.decode('utf8') if data.name else ''
    if name.startswith('='):
        name = make_header(decode_header(name))
    mailbox = data.mailbox.decode('utf8') if data.mailbox else ''
    host = data.host.decode('utf8') if data.host else ''

    return f'{name} <{mailbox}@{host}>'


def process_subject(data: bytes) -> str:
    name = make_header(decode_header(data.decode('utf8')))
    return name


def process_body(server: IMAPClient, k: int, data: BodyData) -> str:
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
