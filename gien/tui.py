#!/usr/bin/env python3

# python-progressbar specialization with context management support
# Usage:
# with TUIProgressBar("Mylabel", 100) as bar:
#    do_something()
#    bar.tick()

from progressbar import ProgressBar, FormatLabel, Bar
from shutil import get_terminal_size

class TUIProgressBar(ProgressBar):
    def __init__(self, label, ticks):
        self.label = label
        self.counter = 0
        super().__init__(maxval = ticks, widgets = self.create_widgets())

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.finish()
        return True

    def tick(self):
        self.counter += 1
        self.update(self.counter)

    def create_widgets(self):
        label = self.label
        bar = Bar(left='[', right=']')
        fmtlabel = FormatLabel(" %(value)d/%(max)d ")

        (w, _) = get_terminal_size()
        lw = int(w * 0.5)
        if len(label)>lw-1:
            s = lw-4
            label = label[:s]
            label += "... "
        else:
            label = label.ljust(lw, ' ')

        return [ label, bar, fmtlabel ]
