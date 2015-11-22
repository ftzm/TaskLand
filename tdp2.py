#!/usr/bin/python
import re
import os
import datetime

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "config.rc"), "r") as f:
    todolist = f.readlines()[0].strip()

with open(todolist, "r") as f:
    file = f.readlines()


x_re = re.compile('^(x)')
pri_re = re.compile('^(\([A-Z]\))')
p_re = re.compile('\+(\w+)')
c_re = re.compile('@(\w+)')
p_id_re = re.compile('P:(\w+)')
c_id_re = re.compile('C:(\w+)')
r_id_re = re.compile('R:(\w+)')
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
    def __init__(self, line, num):
        self.num = num
        line, self.x = extract(line, x_re)
        line, self.priority = extract(line, pri_re)
        line, dates = extract_all(line, date_re)
        line, self.contexts = extract_all(line, p_re)
        line, self.projects = extract_all(line, c_re)
        line, self.parent_id = extract(line, p_id_re)
        line, self.child_id = extract(line, c_id_re)
        line, self.repeat = extract(line, r_id_re)
        self.text = line.strip()

        dates = [datetime.date(*map(int, d.split('-'))) for d in dates]
        datenum = len(dates)
        if datenum == 3:
            self.done, self.due, self.created = dates
        elif datenum == 2 and self.x:
            self.done, self.due, self.created = dates[0], None, dates[1]
        elif datenum == 2:
            self.done, self.due, self.created = None, dates[0], dates[1]
        elif datenum == 1:
            self.done, self.due, self.created = None, None, dates[0]
        else:
            self.done, self.due, self.created = None, None, None

        self.sort_date = self.done or self.due or self.created or \
            datetime.date(1, 1, 1)

    def compose_parts(self, exclusions=None):
        parts = ['n', 'x', 'p', 'dn', 'd', 'c', 't', 'pr', 'cn',
                 'r', 'p_id', 'c_id']

        conversions = {
            'n': '{:>3}'.format(self.num),
            'x': self.x,
            'p': self.priority,
            'dn': self.done.strftime('%Y-%m-%d') if self.done else None,
            'd': self.due.strftime('%Y-%m-%d') if self.due else None,
            'c': self.created.strftime('%Y-%m-%d') if self.created else None,
            'pr': ' '.join(['+{}'.format(p) for p in self.projects])
                 if self.projects else None,
            'cn': ' '.join(['@{}'.format(c) for c in self.contexts])
                 if self.contexts else None,
            'p_id': ''.join(['P:', self.parent_id]) if self.parent_id
                 else None,
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
        magenta = color_prefix.format(5)
        # cyan = color_prefix.format(6)
        orange = color_prefix.format(16)
        gray = color_prefix.format(19)
        # background = '\x1b[48;5;18m'

        pc = {
            'n': gray,
            'x': gray,
            'p': red,
            'dn': gray,
            'd': orange,
            'c': green,
            'pr': blue,
            'cn': yellow,
            'p_id': gray,
            'c_id': gray,
            'r': magenta,
            }

        output = []
        for p in parts:
            if p[0] not in ['t'] and p[1] is not None:
                output.append((p[0], '{}{}{}'.format(pc[p[0]], p[1], unset)))
            else:
                output.append(p)

        return output

    def print_line(self, exclude=None, color=True):
        parts = self.compose_parts()
        if color:
            parts = self.colorize_parts(parts)
        line = ' '.join([p[1] for p in parts if p[1] is not None])
        return line


def normal_print():
    for t in tasks:
        if t.sort_date <= datetime.date.today():
            print(t.print_line())


def nest():
    output_lines = []
    parents = []
    for t in tasks:
        if t.parent_id:
            parents.append(t)

    # sort parents so that they are dealt with top to bottom,
    # with child-parents coming after their parents so they aren't moved
    # after their children in the next sorting step.

    # put top level parents at top
    insert_point = 0
    i = 0
    while i < len(parents):
        if not parents[i].child_id:
            parents.insert(insert_point, parents.pop(i))
            insert_point += 1
        i += 1
    sorted_parents = insert_point  # number of entries from top that are sorted

    # iterate over sorted tasks, looking for all unsorted children parents
    # put each child parent under its parent

    i = 0
    while i < sorted_parents:
        child_id = parents[i].parent_id
        insert_point = i + 1
        j = sorted_parents
        while j < len(parents):
            if child_id == parents[j].child_id:
                parents.insert(insert_point, parents.pop(j))
                sorted_parents += 1
                insert_point += 1
            j += 1
        i += 1

    # rearrange children to follow their parents
    for t in parents:
        # pop children from lines
        children = []
        list_length = len(tasks)
        i = 0
        while i < list_length:
            if t.parent_id == tasks[i].child_id:
                children.append(tasks.pop(i))
                list_length -= 1
            else:
                i += 1
        # find where to insert and insert all children
        insert_point = tasks.index(t) + 1
        for child in children:
            tasks.insert(insert_point, child)
            insert_point += 1

    # pretty indented print
    hierarchy = []
    closed_id = 0
    latest_parent_id = 0
    for t in tasks:
        orphan = False
        # closed/open indicator, set switch to hide following tasks
        parent_id = t.parent_id
        if parent_id:
            latest_parent_id = parent_id
            if 'c' not in parent_id:
                line = '  ' + t.print_line()
            else:
                line = '  ' + t.print_line()
                closed_id = latest_parent_id
        # align non plus or minused tasks
        else:
            line = '  ' + t.print_line()
        # calc indent level based on degree of nested child tags
        if t.child_id:
            child_id = t.child_id
            if child_id not in hierarchy:
                # necessary to check if child is orphan
                if child_id == latest_parent_id:
                    hierarchy.append(child_id)
                else:
                    hierarchy = []
                    orphan = True
            else:
                hierarchy = hierarchy[:hierarchy.index(child_id)+1]
            if not orphan:
                indents = hierarchy.index(child_id)+1
            else:
                indents = 0
            line = "   " * indents + line
        else:
            hierarchy = []
        # if the closed_id is in the hierarchy, then the task will be hidden
        if closed_id not in hierarchy:
            output_lines.append(line)

    for l in output_lines:
        print(l)


tasks = [Task(l, i+1) for i, l in enumerate(file)]

nest()
# normal_print()
