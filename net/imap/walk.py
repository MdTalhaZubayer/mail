# coding=utf-8
import base64
from typing import Iterable, Tuple, Dict

from net.imap.response_types import BodyData


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


def walk_parts(msg: BodyData, msgid, server, download_attachments=None) -> Tuple[str, Dict[str, str]]:

    text = ''
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
                        # with open(filename.decode('utf8'), 'wb') as f:
                        #     f.write(decoded_data)

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
                    # filename = val.decode('utf8')
                    # BODY = 'BODY[{}]'.format(body_number).encode('utf8')
                    # m = server.fetch([msgid], data=[BODY])[msgid]

                    break

    return text, attachments
