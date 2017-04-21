# coding=utf-8
import argparse

from net.imap.imapclient import IMAPClient


def parse_command_line_args():
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--host', required=True, dest='host', action='store', help='IMAP host connect to')
    parser.add_argument('--username', required=True, dest='username', action='store', help='Username to login with')
    parser.add_argument('--password', required=True, dest='password', action='store', help='Password to login with')
    parser.add_argument('--port', dest='port', action='store', type=int, default=993, help='IMAP port to use (default is 143, or 993 for SSL)')
    parser.add_argument('--ssl', dest='ssl', action='store_true', default=True, help='Use SSL connection')
    parser.add_argument('--file', dest='file', action='store', default=None, help='Config file (same as livetest)')
    parser.add_argument('--version', action='version', version='%(prog)s 0.00001')

    args = parser.parse_args()

    return args


def main():
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


if __name__ == "__main__":
    main()
