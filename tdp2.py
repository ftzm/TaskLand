#!/usr/bin/python
import sys
import re
import os
import datetime
import collections

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

        if exclusions is not None:
            parts = [p for p in parts if p not in exclusions]

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
        white = color_prefix.format(7)
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
            't': white,
            }

        output = []
        for p in parts:
            if p[1] is not None:
                output.append((p[0], '{}{}{}'.format(pc[p[0]], p[1], unset)))

        return output

    def compose_line(self, color=False, exclusions=None):
        parts = self.compose_parts(exclusions)
        if color:
            parts = self.colorize_parts(parts)
        line = ' '.join([p[1] for p in parts if p[1] is not None])
        return line


def projects_get(tasks):
    return sorted({p for t in tasks for p in t.projects},
                  key=lambda s: s.lower())


def contexts_get(tasks):
    return sorted({p for t in tasks for p in t.contexts},
                  key=lambda s: s.lower())


def view_by_project(tasks):
    return [t for p in projects_get(tasks) for t in tasks if p in t.projects]


def view_by_context(tasks):
    return [t for p in contexts_get(tasks) for t in tasks if p in t.contexts]


def filter_contexts(tasks, *strings):
    return [t for t in tasks if any(s in t.contexts for s in strings)]


def filter_projects(tasks, *strings):
    return [t for t in tasks if any(s in t.projects for s in strings)]


def filter_include_any(tasks, *strings):
    return [t for t in tasks if any(s in t.text for s in strings)]


def filter_include_all(tasks, *strings):
    return [t for t in tasks if all(s in t.text for s in strings)]


def filter_exclude(tasks, *strings):
    return [t for t in tasks if not any(s in t.text for s in strings)]


def sh_to_date():
    pass


def view_until(tasks, date):
    """takes datetime object, returns all tasks up to and including date"""
    return [t for t in tasks if t.sort_date <= date]


def view_until_cli():
    pass


def view_today(tasks):
    return view_until(tasks, datetime.date.today())


def view_week(tasks):
    return view_until(tasks, datetime.date.today()+datetime.timedelta(7))


def normal_print(tasks, color, trimmings):
    for t in tasks:
        if t.sort_date <= datetime.date.today():
            print(t.compose_line(color, trimmings))


def nest(tasks, color, trimmings):
    output_lines = []
    parents = [t for t in tasks if t.parent_id]

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
                line = '  ' + t.compose_line(color, trimmings)
            else:
                line = '  ' + t.compose_line(color, trimmings)
                closed_id = latest_parent_id
        # align non plus or minused tasks
        else:
            line = '  ' + t.compose_line(color, trimmings)
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


def get_console_size():
    """returns rows and columns as 2 tuple"""
    return [int(i) for i in os.popen('stty size', 'r').read().split()]


def date_headers(tasks, color, trimmings):
    previous_date = ''
    for t in tasks:
        date = t.sort_date.strftime('%Y-%m-%d')
        if date == '1-01-01':
            date = 'No Date'
        if date != previous_date:
            previous_date = date
            buff = get_console_size()[1] - len(date)
            print('\x1b[48;5;18m{}{}\x1b[0m'.format(date, ' '*buff))
        print(t.compose_line())


def add(tasks):
    return tasks


def edit(tasks):
    return tasks


def remove(tasks):
    return tasks


def do(tasks):
    return tasks


def undo(tasks):
    return tasks


def schedule(tasks):
    return tasks


def unschedule(tasks):
    return tasks


def prioritize(tasks):
    return tasks


def unprioritize(tasks):
    return tasks


def set_context(tasks):
    return tasks


def unset_context(tasks):
    return tasks


def set_project(tasks):
    return tasks


def unset_project(tasks):
    return tasks


def set_child(tasks):
    return tasks


def unset_child(tasks):
    return tasks


def contract(tasks):
    return tasks


def expand(tasks):
    return tasks


def future_set(tasks):
    return tasks


def future_order_before(tasks):
    return tasks


def future_order_after(tasks):
    return tasks


def recur_set(tasks):
    return tasks


def recur_unset(tasks):
    return tasks


def catch(tasks):
    return tasks


def write_tasks(tasks):
    pass


view_commands = [
    ('bc', (view_by_context, 0, 0)),
    ('bpr', (view_by_project, 0, 0)),
    ('vc', (filter_contexts, 1, 9)),
    ('vpr', (filter_projects, 1, 9)),
    ('incl', (filter_include_all, 1, 9)),
    ('incl', (filter_include_any, 1, 9)),
    ('excl', (filter_exclude, 1, 9)),
    ('today', (view_today, 0, 0)),
    ('week', (view_week, 0, 0)),
    ('until', (view_until, 1, 1)),
    ('trim', ('trim', 1, 9)),
    ('color', ('color', 0, 0)),
    ('nest', (nest, 0, 0)),
    ('h', (date_headers, 0, 0)),
    ]
view_commands = collections.OrderedDict(view_commands)
action_commands = [
    ('a', (add, 1, 100)),  # 'a' has numbers for show atm
    ('ed', (edit, 0, 0)),
    ('rm', (remove, 0, 0)),
    ('do', (do, 0, 0)),
    ('undo', (undo, 0, 0)),
    ('s', (schedule, 1, 1)),
    ('us', (unschedule, 0, 0)),
    ('p', (prioritize, 1, 1)),
    ('up', (unprioritize, 0, 0)),
    ('c', (set_context, 1, 9)),
    ('uc', (unset_context, 1, 1)),
    ('pr', (set_project, 1, 9)),
    ('upr', (unset_project, 1, 1)),
    ('sub', (set_child, 1, 1)),
    ('usub', (unset_child, 0, 0)),
    ('cn', (contract, 0, 0)),
    ('ex', (expand, 0, 0)),
    ('f', (future_set, 0, 0)),
    ('mb', (future_order_before, 1, 1)),
    ('ma', (future_order_after, 1, 1)),
    ('re', (recur_set, 1, 1)),
    ('ure', (recur_unset, 0, 0)),
    ]
action_commands = collections.OrderedDict(action_commands)
general_commands = [
    ('catch', (catch))
    ]
general_commands = collections.OrderedDict(general_commands)


def assemble_view_command_list(args):
    command_list = []
    for arg in args:
        if arg in view_commands.keys():
            command_args = (arg, [])
            command_list.append(command_args)
        else:
            command_list[-1][1].append(arg)
    command_list.sort(key=lambda x: list(view_commands.keys()).index(x[0]))
    return command_list


def verify_view_command_list(command_list):
    for command_args in command_list:
        command, args = command_args
        min = view_commands[command][1]
        max = view_commands[command][2]
        if len(args) < min:
            if min != max:
                print("Error: '{}' takes at least {} argument{plural}".format(
                    command, min, plural='' if min == 1 else 's'))
            else:
                print("Error: '{}' takes {} argument{plural}".format(
                    command, min, plural='' if min == 1 else 's'))
            return False
        elif len(args) > max:
            surplus = args[max]
            if min != max:
                print("Error: '{}' takes at most {} argument{plural}, "
                      "and '{}' is not a command".format(
                          command, max, surplus,
                          plural='' if max == 1 else 's'))
            else:
                print("Error: '{}' takes {} argument{plural} "
                      "and '{}' is not a command".format(
                          command, max, surplus,
                          plural='' if max == 1 else 's'))
            return False
    return True


def execute_view_command_list(command_list):
    # establish print method
    print_command = normal_print
    color = False
    trimmings = []
    i = 0
    x = len(command_list)
    while i < x:
        if command_list[i][0] in ['h', 'nest']:
            # print_command = view_commands[command_list.pop(i)[0]]
            print_command = view_commands[command_list.pop(i)[0]][0]
            x -= 1
        elif command_list[i][0] == 'color':
            command_list.pop(i)
            color = True
            x -= 1
        elif command_list[i][0] == 'trim':
            trimmings = command_list.pop(i)[1]
            x -= 1
        else:
            i += 1

    tasks = [Task(l, i+1) for i, l in enumerate(file)]

    for command_args in command_list:
        command, args = command_args
        if not args:
            tasks = view_commands[command][0](tasks)
        else:
            tasks = view_commands[command][0](tasks, *args)

    print_command(tasks, color, trimmings)


def handle_view_commands(args):
    command_list = assemble_view_command_list(args)
    if verify_view_command_list(command_list):
        execute_view_command_list(command_list)


def handle_action_commands():
    pass


def handle_general_commands():
    pass


def main(args):
    if len(args) == 0:
        pass
    elif args[0] in view_commands.keys():
        handle_view_commands(args)
    elif args[0] in action_commands.keys() or args[0].isdigit():
        handle_action_commands(args)
    elif args[0] in general_commands.keys():
        handle_general_commands(args[0])
    else:
        print('Error: {} is not a valid command'.format(args[0]))


if __name__ == "__main__":  # why do I use this
    main(sys.argv[1:])
