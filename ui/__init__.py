import curses

import npyscreen

from bin.app import server
from net.imap.search_constants import process_command
from net.imap.util import process_from, process_subject, process_body, process_flags, process_size


class ActionControllerSearch(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^.*', self.set_search, False)  # ^ = beginning

    # noinspection PyUnusedLocal
    def set_search(self, command_line, widget_proxy, live):
        self.parent.wCommand.value = ''
        ids = process_command(server, command_line)
        # todo has attachment?
        mails = server.fetch(ids, data=['ENVELOPE', 'BODY', 'FLAGS', 'RFC822.SIZE'])

        self.parent.wMain.values = []
        for k, v in mails.items():
            row = [v[b'ENVELOPE'],
                   process_from(v[b'ENVELOPE'].from_[0]),
                   process_subject(v[b'ENVELOPE'].subject),
                   process_body(server, k, v[b'BODY']),
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
        # noinspection PyUnresolvedReferences
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
        p = F.add(npyscreen.Textfield, name="Text:", relx=MAXX - len(value) - 2, rely=1)
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