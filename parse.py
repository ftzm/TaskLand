#!/usr/bin/python
"""task class and functions for parsing lines as tasks"""

import re
import base62
import utils

x_re = re.compile('^(x)')
pri_re = re.compile(r'^(\([A-Z]\))')
p_re = re.compile(r'\+(\w+)')
c_re = re.compile(r'@(\w+)')
a_re = re.compile(r'A:([\d\-]+)')
p_id_re = re.compile(r'P:(\w+)')
c_id_re = re.compile(r'C:(\d+)')
r_id_re = re.compile(r'R:(\w+)')
o_re = re.compile(r'O:(\w+)')
date_re = re.compile(r'(\d{4}-\d{2}-\d{2})')


def extract(line, reg):
    target = reg.search(line)
    if target:
        s = target.start()
        e = target.end()
        target = target.group(1)
        line = ''.join([line[:s], line[e:]])
    return line, target


def extract_all(line, reg):
    targets = []
    target = ''
    while target is not None:
        target = reg.search(line)
        if target is not None:
            s = target.start()
            e = target.end()
            target = target.group(1)
            targets.append(target)
            line = ''.join([line[:s], line[e:]])
    return line, targets


class Task(object):
    """task object"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, line):

        self.num = 0
        line, self.x = extract(line, x_re)
        line, self.priority = extract(line, pri_re)
        line, self.child_id = extract(line, c_id_re)
        line, self.repeat = extract(line, r_id_re)
        line, self.contexts = extract_all(line, c_re)
        line, self.projects = extract_all(line, p_re)
        line, self.parent_id = extract(line, p_id_re)
        line, self.added = extract(line, a_re)
        line, self.order = extract(line, o_re)
        line, dates = extract_all(line, date_re)
        self.text = line.strip()
        self.done = None
        self.due = None

        if self.added is not None:
            self.added = utils.string_to_datetime(self.added)

        dates = [utils.string_to_datetime(d) for d in dates]
        if len(dates) == 2:
            self.done, self.due = dates[0], dates[1]
        elif len(dates) == 1 and self.x is not None:
            self.done = dates[0]
        elif len(dates) == 1:
            self.due = dates[0]

        if self.order is not None:
            self.order = base62.decode(self.order)

        if self.parent_id is not None and 'c' in self.parent_id:
            self.parent_id = self.parent_id[:-1]
            self.contracted = True
        else:
            self.contracted = False

    @property
    def num_string(self):
        return '{:>3}'.format(self.num)

    @property
    def done_string(self):
        return self.done.strftime('%Y-%m-%d') if self.done else None

    @property
    def due_string(self):
        return self.due.strftime('%Y-%m-%d') if self.due else None

    @property
    def added_string(self):
        return self.added.strftime('A:%Y-%m-%d') if self.added else None

    @property
    def order_string(self):
        return 'O:{}'.format(base62.encode(self.num))

    @property
    def projects_string(self):
        output = None
        if self.projects:
            output = ' '.join(['+{}'.format(p) for p in self.projects])
        return output

    @property
    def contexts_string(self):
        output = None
        if self.contexts:
            output = ' '.join(['@{}'.format(p) for p in self.contexts])
        return output

    @property
    def parent_id_string(self):
        output = None
        if self.parent_id:
            output = ''.join(['P:', self.parent_id,
                              'c' if self.contracted else ''])
        return output

    @property
    def child_id_string(self):
        output = None
        if self.child_id:
            output = ''.join(['C:', self.child_id,
                              'c' if self.contracted else ''])
        return output

    @property
    def repeat_string(self):
        output = None
        if self.repeat:
            output = ''.join(['R:', self.repeat])
        return output

    def compose_line(self, color=True, exclusions=None, reorder=None):
        """convert task object into a string for display or writing"""

        if exclusions is None:
            exclusions = []
        self.num = reorder or self.num

        parts = [
            ('n', 'gray', self.num_string),
            ('x', 'gray', self.x),
            ('pr', 'red', self.priority),
            ('dn', 'gray', self.done_string),
            ('d', 'orange', self.due_string),
            ('t', 'white', self.text),
            ('p', 'blue', self.projects_string),
            ('c', 'yellow', self.contexts_string),
            ('r', 'magenta', self.repeat_string),
            ('a', 'green', self.added_string),
            ('o', 'gray', self.order_string),
            ('p_id', 'gray', self.parent_id_string),
            ('c_id', 'gray', self.child_id_string),
            ]

        if color:
            parts = [utils.colorize(s, c) for l, c, s in parts
                     if l not in exclusions and s]
        else:
            parts = [s for l, c, s in parts if l not in exclusions and s]
        return ' '.join(parts)
