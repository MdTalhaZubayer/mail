# coding=utf-8

from net.imap.imapclient import IMAPClient
from net.imap.search_constants import search_mails
from net.imap.walk import walk_parts
from net.utils import parse_command_line_args
from ui import MailBox

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

search_mails(server, 'from:christian')

message_id = 151

m140 = server.fetch([message_id], data=['ENVELOPE', 'BODYSTRUCTURE', 'FLAGS', 'RFC822.SIZE'])

bodystructure_ = m140[message_id][b'BODYSTRUCTURE']

text, attachments = walk_parts(bodystructure_, msgid=message_id, server=server)

if __name__ == "__main__":
    App = MailBox()
    App.run()

if __name__ == "__main__":
    App = MailBox()
    App.run()
