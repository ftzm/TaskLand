#!/usr/bin/python
import re
import base62
import datetime


x_re = re.compile('^(x)')
pri_re = re.compile('^(\([A-Z]\))')
p_re = re.compile('\+(\w+)')
c_re = re.compile('@(\w+)')
a_re = re.compile('A:([\d\-]+)')
p_id_re = re.compile('P:(\w+)')
c_id_re = re.compile('C:(\d+)')
r_id_re = re.compile('R:(\w+)')
o_re = re.compile('O:(\w+)')
date_re = re.compile('(\d{4}-\d{2}-\d{2})')


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
    def __init__(self, line):
        self.num = 0
        line, self.x = extract(line, x_re)
        line, self.priority = extract(line, pri_re)
        line, self.added = extract(line, a_re)
        line, dates = extract_all(line, date_re)
        line, self.order = extract(line, o_re)
        if self.order is not None:
            try:
                self.order = base62.decode(self.order)
            except:
                print('Error: corrupted order code')
        line, self.contexts = extract_all(line, c_re)
        line, self.projects = extract_all(line, p_re)
        line, self.parent_id = extract(line, p_id_re)
        if self.parent_id is not None and 'c' in self.parent_id:
            self.parent_id = self.parent_id[:-1]
            self.contracted = True
        else:
            self.contracted = False
        line, self.child_id = extract(line, c_id_re)
        line, self.repeat = extract(line, r_id_re)
        self.text = line.strip()

        if self.added is not None:
            self.added = datetime.date(*map(int, self.added.split('-')))

        dates = [datetime.date(*map(int, d.split('-'))) for d in dates]
        datenum = len(dates)
        if datenum == 2:
            self.done, self.due = dates[0], dates[1]
        elif datenum == 1 and self.x is not None:
            self.done, self.due = dates[0], None
        elif datenum == 1:
            self.done, self.due = None, dates[0]
        else:
            self.done, self.due = None, None

    def compose_parts(self, order, exclusions=None):
        parts = ['n', 'x', 'pr', 'dn', 'd', 't', 'p', 'c',
                 'r', 'a', 'o', 'p_id', 'c_id']

        if exclusions is not None:
            parts = [p for p in parts if p not in exclusions]

        conversions = {
            'n': '{:>3}'.format(self.num),
            'x': self.x,
            'pr': self.priority,
            'dn': self.done.strftime('%Y-%m-%d') if self.done else None,
            'd': self.due.strftime('%Y-%m-%d') if self.due else None,
            'a': self.added.strftime('A:%Y-%m-%d') if self.added else None,
            'o': 'O:{}'.format(base62.encode(order)),
            'p': ' '.join(['+{}'.format(p) for p in self.projects])
                 if self.projects else None,
            'c': ' '.join(['@{}'.format(c) for c in self.contexts])
                 if self.contexts else None,
            'p_id': ''.join(['P:', self.parent_id, 'c' if self.contracted
                             else '']) if self.parent_id else None,
            'c_id': ''.join(['C:', self.child_id]) if self.child_id else None,
            'r': ''.join(['R:', self.repeat]) if self.repeat else None,
            't': self.text
            }

        output = [(p, conversions[p]) for p in parts]

        return(output)

    def colorize_parts(self, parts):
        color_prefix = '\x1b[38;5;{}m'
        unset = '\x1b[0m'
        red = color_prefix.format(1)
        green = color_prefix.format(2)
        yellow = color_prefix.format(3)
        blue = color_prefix.format(4)
        magenta = color_prefix.format(13)
        cyan = color_prefix.format(6)
        orange = color_prefix.format(9)
        gray = color_prefix.format(10)
        white = color_prefix.format(14)
        # background = '\x1b[48;5;18m'

        pc = {
            'n': gray,
            'x': gray,
            'pr': red,
            'f': cyan,
            'dn': gray,
            'd': orange,
            'a': green,
            'o': gray,
            'p': blue,
            'c': yellow,
            'p_id': gray,
            'c_id': gray,
            'r': magenta,
            't': white,
            }

        output = []
        for p in parts:
            if p[1] is not None:
                output.append((p[0], '{}{}{}'.format(pc[p[0]], p[1], unset)))

        return output

    def compose_line(self, color=True, exclusions=None, order=None):
        if not order:
            order = self.num
        parts = self.compose_parts(order, exclusions)
        if color:
            parts = self.colorize_parts(parts)
        line = ' '.join([p[1] for p in parts if p[1] is not None])
        return line
