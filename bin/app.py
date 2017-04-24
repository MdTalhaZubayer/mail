# coding=utf-8
import argparse
import curses
import datetime
import toolz

from net.imap.imapclient import IMAPClient

IMAP_SEARCH_FIELDS = {
    'ALL': str,
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


#
#
# class DemoFrame(Frame):
#     def __init__(self, screen):
#         super(DemoFrame, self).__init__(screen,
#                                         screen.height,
#                                         screen.width,
#                                         has_border=False,
#                                         name="__mail__")
#         # Internal state required for doing periodic updates
#         self._last_frame = 0
#         self._sort = 5
#         self._reverse = True
#
#         # Create the basic form layout...
#         layout = Layout([1], fill_frame=True)
#         self._header = TextBox(1, as_string=True)
#         self._header.disabled = True
#         self._header.custom_colour = "label"
#         self._list = MultiColumnListBox(
#             Widget.FILL_FRAME,
#             [">6", 10, ">4", ">7", ">7", "100%"],
#             [],
#             titles=["PID", "USER", "NI", "VIRT", "RSS", "CPU%"],
#             name="mc_list")
#         self._searchbox = Text(label='search', name=None, on_change=None, validator=None)
#
#         self.add_layout(layout)
#         layout.add_widget(self._header)
#         layout.add_widget(self._list)
#         layout.add_widget(self._searchbox)
#
#         layout.add_widget(Label("Press `<`/`>` to change sort, `r` to toggle order, or `q` to quit."))
#         self.fix()
#
#         # Add my own colour palette
#         self.palette = defaultdict(
#             lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
#         for key in ["selected_focus_field", "label"]:
#             self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
#         self.palette["title"] = (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE)
#
#     def process_event(self, event):
#         # Do the key handling for this Frame.
#         if isinstance(event, KeyboardEvent):
#             if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
#                 raise StopApplication("User quit")
#             elif event.key_code in [ord("r"), ord("R")]:
#                 self._reverse = not self._reverse
#             elif event.key_code == ord("<"):
#                 self._sort = max(0, self._sort - 1)
#             elif event.key_code == ord(">"):
#                 self._sort = min(7, self._sort + 1)
#
#             # Force a refresh for improved responsiveness
#             self._last_frame = 0
#
#         # Now pass on to lower levels for normal handling of the event.
#         return super(DemoFrame, self).process_event(event)
#
#     def _update(self, frame_no):
#         self.b = 1
#         # Refresh the list view if needed
#         if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
#             self._last_frame = frame_no
#
#             # Create the data to go in the multi-column list...
#             last_selection = self._list.value
#             last_start = self._list.start_line
#             list_data = []
#             for a in range(3):
#
#
#                 data = [
#                         1 * a * self.b,
#                         2 * a * self.b,
#                         3 * a * self.b,
#                         4 * a * self.b,
#                         5 * a * self.b,
#                         6 * a * self.b,
#                     ]
#                 list_data.append(data)
#
#             new_data = [
#                 ([
#                      str(x[0]),
#                      str(x[1]),
#                      str(x[2]),
#                      str(x[3]),
#                      str(x[4]),
#                      str(x[5])
#
#                  ], x[0]) for x in list_data
#             ]
#
#             # Update the list and try to reset the last selection.
#             self._list.options = new_data
#             self._list.value = last_selection
#             self._list.start_line = last_start
#             self._header.value = "fdfddf"
#             self.b += 1
#
#         # Now redraw as normal
#         super(DemoFrame, self)._update(frame_no)
#
#     # @property
#     # def frame_update_count(self):
#     #     Refresh once every 2 seconds by default.
#         # return 100



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

x = server.fetch([141], data=['BODY[HEADER.FIELDS (SUBJECT FROM)]', 'BODY.PEEK[1] <0.100>'])

# das hier mit attachment
# http://stackoverflow.com/questions/6225763/downloading-multiple-attachments-using-imaplib
x = server.fetch([139], data=['BODYSTRUCTURE'])
f = x[139][b'BODYSTRUCTURE']
len(f[0])
#
# while True:
#     query = input('gimme')
#     if query == 'quit' or query == 'q':
#         break
#     if query == 'help':
#         print('help todo')
#         continue
#     terms = []
#
#     processed_query = [x.split(':') for x in query.split()]
#
#     grouped = toolz.groupby(lambda x: x[0], processed_query)
#
#     for group, items in grouped.items():
#         if len(items) > 1:
#             terms.append('OR')
#
#         for field, term in items:
#             field = field.upper()
#             if field.startswith('-'):
#                 field = field[1:]
#                 terms.append('NOT')
#             convert = IMAP_SEARCH_FIELDS.get(field, None)
#             if field in IMAP_SEARCH_FIELDS:
#                 terms.append(field)
#             if term and convert:
#                 terms.append(convert(term))
#
#     print(terms)
#     print(server.search(terms))


def process_command(query):

    if query == 'quit' or query == 'q':
        pass
    if query == 'help':
        pass

    terms = []

    processed_query = [x.split(':') for x in query.split()]

    grouped = toolz.groupby(lambda x: x[0], processed_query)

    for group, items in grouped.items():
        if len(items) > 1:
            terms.append('OR')

        for field, term in items:
            field = field.upper()
            if field.startswith('-'):
                field = field[1:]
                terms.append('NOT')
            convert = IMAP_SEARCH_FIELDS.get(field, None)
            if field in IMAP_SEARCH_FIELDS:
                terms.append(field)
            if term and convert:
                terms.append(convert(term))
    mails = server.search(terms)
    return mails

import npyscreen


def process_subject(data):
    return data.decode('utf8').replace('Subject: ', '').strip()
def process_from(data):
    return data.decode('utf8').replace('From: ', '').strip()


def process_body(data):
    return data.decode('utf8').strip()


def process_size(data):
    return int(data)


def process_flags(data):
    return data  # todo

class ActionControllerSearch(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^.*', self.set_search, False)  # ^ = beginning

    def set_search(self, command_line, widget_proxy, live):
        # print(command_line)
        # self.parent.value.set_filter(command_line[1:])
        # self.parent.wMain.values = self.parent.value.get()
        # self.parent.wMain.display()

        self.parent.wCommand.value = ''
        ids = process_command(command_line)

        mails = server.fetch(ids, data=['BODY[HEADER.FIELDS (SUBJECT)]', 'BODY[HEADER.FIELDS (FROM)]', 'BODY.PEEK[1] <0.100>', 'FLAGS', 'RFC822.SIZE'])

        # data = []
        # [data.append([k, b'BODY[HEADER.FIELDS (SUBJECT FROM)]', b'BODY[1][0]', 'FLAGS', 'RFC822.SIZE']) for k,v in mails.items()]

        self.parent.wMain.values = []
        for k, v in mails.items():
            row = [k,
                   process_subject(v[b'BODY[HEADER.FIELDS ("SUBJECT")]']),
                   process_from(v[b'BODY[HEADER.FIELDS ("FROM")]']),
                   process_body(v[b'BODY[1]<0>']),
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

def on_table_update(*args, **kwargs):
    a = 3


class MyGrid(npyscreen.GridColTitles):
    def __init__(self, screen, col_titles=None, *args, **kwargs):

        super(MyGrid, self).__init__(screen, col_titles, *args, **kwargs)
        self.select_whole_line = True


    def set_up_handlers(self):
        super(MyGrid, self).set_up_handlers()
        self.handlers = {
            curses.ascii.NL: self.select,
            curses.ascii.CR: self.select,
            curses.KEY_UP: self.h_move_line_up,
                    curses.KEY_LEFT:    self.h_move_cell_left,
                    curses.KEY_DOWN:    self.h_move_line_down,
                    curses.KEY_RIGHT:   self.h_move_cell_right,
                    "k":                self.h_move_line_up,
                    "h":                self.h_move_cell_left,
                    "j":                self.h_move_line_down,
                    "l":                self.h_move_cell_right,
                    curses.KEY_NPAGE:   self.h_move_page_down,
                    curses.KEY_PPAGE:   self.h_move_page_up,
                    curses.KEY_HOME:    self.h_show_beginning,
                    curses.KEY_END:     self.h_show_end,
                    ord('g'):           self.h_show_beginning,
                    ord('G'):           self.h_show_end,
                    curses.ascii.TAB:   self.h_exit,

                    curses.KEY_BTAB:     self.h_exit_up,
                    '^P':               self.h_exit_up,
                    '^N':               self.h_exit_down,
                    #curses.ascii.NL:    self.h_exit,
                    #curses.ascii.SP:    self.h_exit,
                    #ord('x'):       self.h_exit,
                    ord('q'):       self.h_exit,
                    curses.ascii.ESC:   self.h_exit,
                    curses.KEY_MOUSE:    self.h_exit_mouse,
                }

        self.complex_handlers = [
                    ]
    def select(self, *args, **kwargs):

        a, b = self.edit_cell
        mail_id = self.values[a][0]
        # todo fetch message and siplay it on a separate screen
        # todo can we do tabbed?


class FmSearchActive(npyscreen.FormMuttActive):
    ACTION_CONTROLLER = ActionControllerSearch
    MAIN_WIDGET_CLASS = MyGrid
    MAIN_WIDGET_CLASS_START_LINE = 2
    STATUS_WIDGET_CLASS = npyscreen.Textfield
    STATUS_WIDGET_X_OFFSET = 0
    COMMAND_WIDGET_CLASS = MyTextCommandBox
    COMMAND_WIDGET_NAME = 'Search'
    COMMAND_WIDGET_BEGIN_ENTRY_AT = None
    COMMAND_ALLOW_OVERRIDE_BEGIN_ENTRY_AT = True

    # DATA_CONTROLER = DataController
    # new_handlers = {
    #  curses.KEY_ENTER: on_table_update,
    # }
    MAIN_WIDGET_CLASS.select_whole_line = True

    # a = MAIN_WIDGET_CLASS.event_handlers
    bb  =3




class TestApp(npyscreen.NPSApp):
    def main(self):
        F = FmSearchActive()
        F.wStatus1.value = "mail "
        F.wStatus2.value = "search / commands "

        F.wMain.values = []
        # for x in range(36):
        #     row = []
        #     for y in range(4):
        #         row.append(y)
        #     F.wMain.values.append(row)

        F.wMain.col_titles = ['id', 'from', 'subject', 'content', 'flags', 'size']

        F.edit()


if __name__ == "__main__":
    App = TestApp()
    App.run()

if __name__ == "__main__":
    App = TestApp()
    App.run()
    main()

    # def demo(screen):
    #     screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True)
    #
    # while True:
    #     try:
    #         Screen.wrapper(demo, catch_interrupt=True)
    #         sys.exit(0)
    #     except ResizeScreenError:
    #         pass
