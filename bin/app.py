# coding=utf-8
import argparse
from collections import defaultdict

import psutil as psutil
import sys
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import StopApplication, ResizeScreenError
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, Layout, TextBox, MultiColumnListBox, Widget, Label

from net.imap.imapclient import IMAPClient


def parse_command_line_args():
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--host', required=True, dest='host', action='store', help='IMAP host connect to')
    parser.add_argument('--username', required=True, dest='username', action='store', help='Username to login with')
    parser.add_argument('--password', required=True, dest='password', action='store', help='Password to login with')
    parser.add_argument('--port', dest='port', action='store', type=int, default=993, help='IMAP port to use (default is 143, or 993 for SSL)')
    parser.add_argument('--ssl', dest='ssl', action='store_true', default=True, help='Use SSL connection')
    parser.add_argument('--file', dest='file', action='store', default=None, help='Config file (same as livetest)')
    parser.add_argument('--version', action='version', version='0.00001')

    args = parser.parse_args()

    return args


def readable_mem(mem):
    for suffix in ["", "K", "M", "G", "T"]:
        if mem < 10000:
            return "{}{}".format(int(mem), suffix)
        mem /= 1024
    return "{}P".format(int(mem))


def readable_pc(percent):
    if percent < 100:
        return str(round(percent * 10, 0) / 10)
    else:
        return str(int(percent))


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        has_border=False,
                                        name="My Form")
        # Internal state required for doing periodic updates
        self._last_frame = 0
        self._sort = 5
        self._reverse = True

        # Create the basic form layout...
        layout = Layout([1], fill_frame=True)
        self._header = TextBox(1, as_string=True)
        self._header.disabled = True
        self._header.custom_colour = "label"
        self._list = MultiColumnListBox(
            Widget.FILL_FRAME,
            [">6", 10, ">4", ">7", ">7", ">5", ">5", "100%"],
            [],
            titles=["PID", "USER", "NI", "VIRT", "RSS", "CPU%", "MEM%", "CMD"],
            name="mc_list")
        self.add_layout(layout)
        layout.add_widget(self._header)
        layout.add_widget(self._list)
        layout.add_widget(
                Label("Press `<`/`>` to change sort, `r` to toggle order, or `q` to quit."))
        self.fix()

        # Add my own colour palette
        self.palette = defaultdict(
            lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
        self.palette["title"] = (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE)

    def process_event(self, event):
        # Do the key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code in [ord("r"), ord("R")]:
                self._reverse = not self._reverse
            elif event.key_code == ord("<"):
                self._sort = max(0, self._sort - 1)
            elif event.key_code == ord(">"):
                self._sort = min(7, self._sort + 1)

            # Force a refresh for improved responsiveness
            self._last_frame = 0

        # Now pass on to lower levels for normal handling of the event.
        return super(DemoFrame, self).process_event(event)

    def _update(self, frame_no):
        # Refresh the list view if needed
        if frame_no - self._last_frame >= self.frame_update_count or self._last_frame == 0:
            self._last_frame = frame_no

            # Create the data to go in the multi-column list...
            last_selection = self._list.value
            last_start = self._list.start_line
            list_data = []
            for process in psutil.process_iter():
                try:
                    memory = process.memory_info()
                    data = [
                        process.pid,
                        process.username(),
                        int(process.nice()),
                        memory.vms,
                        memory.rss,
                        process.cpu_percent(),
                        process.memory_percent(),
                        (" ".join(process.cmdline()) if process.cmdline() else
                         "[{}]".format(process.name()))
                    ]
                    list_data.append(data)
                except psutil.AccessDenied:
                    # Some platforms don't allow querying of all processes...
                    pass

            # Apply current sort and reformat for humans
            list_data = sorted(list_data,
                               key=lambda f: f[self._sort],
                               reverse=self._reverse)
            new_data = [
                ([
                     str(x[0]),
                     x[1],
                     str(x[2]),
                     readable_mem(x[3]),
                     readable_mem(x[4]),
                     readable_pc(x[5]),
                     readable_pc(x[6]),
                     x[7]
                 ], x[0]) for x in list_data
            ]

            # Update the list and try to reset the last selection.
            self._list.options = new_data
            self._list.value = last_selection
            self._list.start_line = last_start
            self._header.value = (
                "CPU usage: {}%   Memory available: {}M".format(
                    str(round(psutil.cpu_percent() * 10, 0) / 10),
                    str(int(psutil.virtual_memory().available / 1024 / 1024))))

        # Now redraw as normal
        super(DemoFrame, self)._update(frame_no)

    @property
    def frame_update_count(self):
        # Refresh once every 2 seconds by default.
        return 40
#
# def main():
#     args = parse_command_line_args()
#     print('Connecting...')
#     # client = create_client_from_config(args)
#     server = IMAPClient(args.host, use_uid=True, ssl=args.ssl)
#     server.login(args.username, args.password)
#     print('Connected.')
#
#     select_info = server.select_folder('INBOX')
#     print('%d messages in INBOX' % select_info[b'EXISTS'])
#
#     messages = server.search([b'NOT', b'DELETED'])
#     print("%d messages that aren't deleted" % len(messages))
#
#
# if __name__ == "__main__":
#     main()

def demo(screen):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass