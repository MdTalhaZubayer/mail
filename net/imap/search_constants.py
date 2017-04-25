# coding=utf-8
import datetime
import imaplib
from typing import List

import sys
import toolz

from net.imap.imapclient import IMAPClient

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


def process_command(server: IMAPClient, query: str) -> List[int]:
    if query == 'quit' or query == 'q':
        sys.exit(1)
    if query == 'help':
        pass  # todo show all search options

    return search_mails(server, query)


def search_mails(server, query: str) -> List[int]:
    terms = extract_search_terms(query)

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


def extract_search_terms(query: str) -> List[str]:
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
    return terms
