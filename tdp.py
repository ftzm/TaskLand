#!/usr/bin/python
import sys
import re
import os
import datetime
import collections
import readline
import copy
import base62

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
a_re = re.compile('A:(\d{4}-\d{2}-\d{2})')
p_id_re = re.compile('P:(\w+)')
c_id_re = re.compile('C:(\d+)')
r_id_re = re.compile('R:(\w+)')
o_re = re.compile('O:(\w+)')
date_re = re.compile('(\d{4}-\d{2}-\d{2})')

weekdays = ['m', 't', 'w', 'r', 'f', 's', 'u']


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
        self.num = None
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
        parts = ['n', 'x', 'p', 'dn', 'd', 't', 'pr', 'cn',
                 'r', 'a', 'o', 'p_id', 'c_id']

        if exclusions is not None:
            parts = [p for p in parts if p not in exclusions]

        conversions = {
            'n': '{:>3}'.format(self.num),
            'x': self.x,
            'p': self.priority,
            'dn': self.done.strftime('%Y-%m-%d') if self.done else None,
            'd': self.due.strftime('%Y-%m-%d') if self.due else None,
            'a': self.added.strftime('A:%Y-%m-%d') if self.added else None,
            'o': 'O:{}'.format(base62.encode(order)),
            'pr': ' '.join(['+{}'.format(p) for p in self.projects])
                 if self.projects else None,
            'cn': ' '.join(['@{}'.format(c) for c in self.contexts])
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
        magenta = color_prefix.format(5)
        cyan = color_prefix.format(6)
        orange = color_prefix.format(16)
        gray = color_prefix.format(19)
        white = color_prefix.format(7)
        # background = '\x1b[48;5;18m'

        pc = {
            'n': gray,
            'x': gray,
            'p': red,
            'f': cyan,
            'dn': gray,
            'd': orange,
            'a': green,
            'o': gray,
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

    def compose_line(self, color=False, exclusions=None, order=None):
        if not order:
            order = self.num
        parts = self.compose_parts(order, exclusions)
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


def weekday_to_datetime(s):
    daynum = weekdays.index(s)
    offset = daynum - int(datetime.date.today().weekday())
    if offset < 1:
        offset += 7
    date = datetime.date.today() + datetime.timedelta(offset)
    return date


def date_to_datetime(s):
    date = None
    td = datetime.date.today()
    td = [td.year, td.month, td.day]
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if td[0] % 4 == 0:
        month_lengths[1] = 29
    if re.match('\d{1,2}$', s):
        year, month, day = None, None, int(s)
    elif re.match('\d{1,2}-\d{1,2}$', s):
        year, month, day = None, tuple([int(i) for i in s.split('-')])
    elif re.match('\d{4}-\d{1,2}-\d{1,2}$', s):
        year, month, day = tuple([int(i) for i in s.split('-')])

    # increment month if day is lower than td
    if day < td[2] and month is None:
        month = td[1] + 1
        if month > 12:
            month = 1

    # set unset months and years
    if not month:
        month = td[1]
    if not year:
        year = td[0]

    # if month lower than td's, due next year.
    if month < td[1]:
        year = td[0] + 1

    # handle edge cases where impossible dates are entered.
    if month > 12:
        print("Error: Month must be 12 or below")
    elif day > month_lengths[month-1]:
        print("Error: Not that many days in the month")
    else:
        date = datetime.date(year, month, day)
    return date


def code_to_datetime(s):
    if s[0] in weekdays:
        date = weekday_to_datetime(s)
    elif s[0].isdigit():
        date = date_to_datetime(s)
    else:
        print('Error: Not a valid date format')
    return date


# ###############
#
# View Functions
#
# ###############


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


def view_until(tasks, date):
    """takes datetime object, returns all tasks up to and including date"""
    return [t for t in tasks if t.due and t.due <= date and not t.x]


def view_until_cli(tasks, s):
    date = code_to_datetime(s)
    return view_until(tasks, date)


def view_today(tasks):
    return view_until(tasks, datetime.date.today())


def view_week(tasks):
    return view_until(tasks, datetime.date.today()+datetime.timedelta(7))


def normal_print(tasks, color, trimmings):
    for t in tasks:
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
    previous_title = ''
    for t in tasks:
        if t.priority is not None:
            title = 'Prioritized'
        elif t.x is not None:
            title = 'Finished'
        elif t.due:
            title = t.due.strftime('%Y-%m-%d')
        else:
            title = 'Future'
        if title != previous_title:
            previous_title = title
            buff = get_console_size()[1] - len(title)
            print('\x1b[48;5;18m{}{}\x1b[0m'.format(title, ' '*buff))
        print(t.compose_line(color, trimmings))


# ###############
#
# Action Functions
#
# ###############


def add(tasks, s):
    task = Task(s)
    task.created = datetime.date.today()
    task.due = datetime.date.today()
    tasks.append(task)
    return tasks


def prefill_input(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        result = input(prompt)
    finally:
        readline.set_startup_hook()
    return result


def edit(tasks, n):
    tasks[n].text = prefill_input('Edit: ', tasks[n].text)
    return tasks


def remove(tasks, n):
    followthrough = input('Task: {}\nDelete? (Y/n)'.format(
        tasks[n].compose_line()))
    if followthrough == '' or followthrough.lower() == 'y':
        removed = tasks.pop(n)
        print('Removed: ' + removed.compose_line())
    return tasks


def do(tasks, n):
    tasks[n].priority = None
    if tasks[n].parent_id is not None:
        tasks[n].parent_id = None
        tasks = clean_orphans(tasks, tasks[n].parent_id)
    if tasks[n].repeat is not None:
        tasks = repeat_recycle(tasks, n)
    else:
        tasks[n].x = 'x'
        tasks[n].done = datetime.date.today()
    return tasks


def undo(tasks):
    return tasks


def schedule(tasks, n, s):
    date = code_to_datetime(s)
    tasks[n].due = date
    return tasks


def unschedule(tasks, n):
    tasks[n].due = None
    return tasks


def prioritize(tasks, n, priority='A'):
    if not priority.isalpha() or len(priority) > 1:
        print("Not a valid priority")
    else:
        priority = priority.upper()
        tasks[n].priority = '({})'.format(priority)
    return tasks


def unprioritize(tasks, n):
    tasks[n].priority = None
    return tasks


def set_contexts(tasks, n, contexts):
    tasks[n].contexts.append(contexts)
    return tasks


def unset_contexts(tasks, n, i):
    tasks[n].contexts.pop(i-1)
    return tasks


def set_projects(tasks, n, projects):
    tasks[n].projects.append(projects)
    return tasks


def unset_projects(tasks, n, i=1):
    tasks[n].projects.pop(i-1)
    return tasks


def parent_set(tasks, n):
    parent_ids = [t.parent_id for t in tasks if t.parent_id is not None]
    for i in range(1, len(parent_ids)+2):
        if str(i) not in parent_ids:
            new_id = i
            break
    tasks[n].parent_id = str(new_id)
    return tasks


def parent_unset(tasks, n):
    tasks[n].parent_id = None
    return tasks


def parent_check_empty(tasks, id):
    if not any(t.child_id == id for t in tasks):
        for t in tasks:
            if t.parent_id == id:
                t.parent_id = None
    return tasks


def child_set(tasks, n, p):
    p = int(p) - 1
    if tasks[p].parent_id is None:
        tasks = parent_set(tasks, p)
    tasks[n].child_id = tasks[p].parent_id
    return tasks


def child_unset(tasks, n):
    child_id = tasks[n].child_id
    tasks[n].child_id = None
    tasks = parent_check_empty(tasks, child_id)
    return tasks


def clean_orphans(tasks, id):
    for t in tasks:
        if t.child_id == id:
            t.child_id = None


def contract(tasks, n):
    tasks[n].contracted = True
    return tasks


def expand(tasks, n):
    tasks[n].contracted = True
    return tasks


def future_find_last_num(tasks):
    for i in range(len(tasks)-1, -1, -1):
        if tasks[i].future is not None:
            return int(tasks[i].future)
    return 0000000


def future_redistribute(tasks):
    last = 0
    for t in tasks:
        if t.future is not None:
            last = last + 10000
            t.future = last
    return tasks


def future_set(tasks, n):
    tasks[n].due = None
    return tasks


def order_after(tasks, n, p):
    pivot_i = int(p)-1
    if tasks[n].due != tasks[pivot_i].due:
        print('Can\'t order tasks with different due dates against each other')
        return tasks
    if pivot_i > n:
        pivot_i -= 1
    moved = tasks.pop(n)
    tasks.insert(pivot_i+1, moved)
    return tasks


def order_before(tasks, n, p):
    pivot_i = int(p)-1
    if tasks[n].due != tasks[pivot_i].due:
        print('Can\'t order tasks with different due dates against each other')
        return tasks
    if pivot_i > n:
        pivot_i -= 1
    moved = tasks.pop(n)
    tasks.insert(pivot_i, moved)
    return tasks


def repeat_unset(tasks, n):
    tasks[n].repeat = None
    return tasks


def repeat_set(tasks, n, s):
    t = tasks[n]
    if t.created is None:
        t.created = datetime.date.today()
    if re.match('a\d{1,2}$', s):
        t.repeat = s
    elif re.match('e\d{1,2}$', s):
        t.repeat = s
        if t.created is not None and t.due is not None:
            t.repeat = t.repeat + 'c' + str((t.due - t.created).days)
        else:
            t.repeat += 'c0'
    elif re.match('[mtwrfsu]{1,7}', s):
        t.repeat = ''.join(c for c in "mtwrfsu" if c in s)
    else:
        print('Error: Not a valid recur format')
    return tasks


def repeat_recycle(tasks, n):
    t = tasks[n]
    td = datetime.date.today()

    t_done = copy.deepcopy(t)
    t_done.x = 'x'
    t_done.done = td
    tasks.append(t_done)

    if 'a' in t.repeat:
        interval = t.repeat[1:]
        t.due += datetime.timedelta(interval)
    elif 'e' in t.repeat:
        nums = t.repeat[1:].split('c')
        interval = int(nums[0])
        # date it should have been done on ([-1] to use correction if there)
        intended_date = t.created + datetime.timedelta(int(nums[-1]))
        t.due = intended_date + datetime.timedelta(interval)
        while t.due < td:
            t.due += datetime.timedelta(interval)
        t.repeat = 'e' + str(interval)
        # set correction if today wasn't due day
        if t.due != td + datetime.timedelta(interval):
            t.repeat += 'c' + str((t.due - td).days)
    else:
        interval = 1
        i = td.weekday() + 1
        while i != td.weekday():
            if i > 6:
                i = 0
            if weekdays[i] in t.repeat:
                break
            i += 1
            interval += 1
        t.due = td + datetime.timedelta(interval)

    # now turn existing task into recurred version
    t.created = td
    t.priority = None
    return tasks


def catch(tasks):
    for i, t in enumerate(tasks):
        if t.sort_field < datetime.date.today() and \
                t.x is None and t.future is None:
            sched = input('{}\nNew due date (blank for future): '.format(
                t.text))
            if sched == '':
                tasks = future_set(tasks, i)
            else:
                t.due = code_to_datetime(sched)
    return tasks


def collect_tasks():
    tasks = [Task(l) for l in sorted(file)]
    bins = []
    bin = []
    prev = None
    for t in tasks:
        if t.due == prev:
            bin.append(t)
        else:
            prev = t.due
            bins.append(sorted(bin, key=lambda x: x.order if x.order
                        else 9**9))
            bin = [t]
    bins.append(sorted(bin, key=lambda x: x.order if x.order
                else 9**9))
    tasks = [t for b in bins for t in b]
    for i, t in enumerate(tasks):
        t.num = i+1
    return tasks


def write_tasks(tasks):
    lines = [t.compose_line(False, ['n'], i+1) for i, t in enumerate(tasks)]
    with open(todolist, "w") as f:
        for line in lines:
            f.write(line + '\n')


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
    ('c', (set_contexts, 1, 9)),
    ('uc', (unset_contexts, 1, 1)),
    ('pr', (set_projects, 1, 9)),
    ('upr', (unset_projects, 1, 1)),
    ('sub', (child_set, 1, 1)),
    ('usub', (child_unset, 0, 0)),
    ('cn', (contract, 0, 0)),
    ('ex', (expand, 0, 0)),
    ('f', (future_set, 0, 0)),
    ('mb', (order_before, 1, 1)),
    ('ma', (order_after, 1, 1)),
    ('re', (repeat_set, 1, 1)),
    ('ure', (repeat_unset, 0, 0)),
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

    tasks = collect_tasks()

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


def assemble_action_command_list(args, target):
    command_list = []
    task_text = False
    i = 0
    while i < len(args):
        arg = args[i]
        if task_text is False:
            if arg in list(action_commands.keys()):
                command_args = (arg, [])
                command_list.append(command_args)
                # set to grab task text if command is a
                task_text = arg == 'a'
                # manually grab args for some commands because they're
                # also sometimes commands
                if arg == 'p':
                    i += 1
                    if args[i].isdigit():
                        command_list[-1][1].append(args[i])
                        i += 1
                    command_list[-1][1].append(args[i])
                elif arg in ['s', 're']:
                    i += 1
                    if args[i].isdigit():
                        command_list[-1][1].append(args[i])
                        i += 1
                        if target is not None:
                            continue
                    if args[i].isdigit or args[i] in weekdays:
                        command_list[-1][1].append(args[i])
            else:
                try:
                    command_list[-1][1].append(arg)
                except:
                    print('{} is not a command'.format(arg))
        else:
            if arg == ',':
                task_text = False
            else:
                try:
                    command_list[-1][1].append(arg)
                except:
                    print('{} is not a command'.format(arg))
        i += 1
    return command_list


def prepare_single_action(command_list):
    target = None
    if len(command_list) > 1:
        print("Error: may not combine multiple commands without specifying"
              " a target as the very first argument or unless a task is being"
              " added")
    elif len(command_list[0][1]) < 1 or not command_list[0][1][0].isdigit():
        print("Error: command requires a target")
    else:
        target = int(command_list[0][1][0]) - 1
        command_list[0][1].pop(0)
    return command_list, target


def verify_action_command_list(command_list):
    for command_args in command_list:
        command, args = command_args
        min = action_commands[command][1]
        max = action_commands[command][2]
        if len(args) < min:
            if min != max:
                print("Error: '{}' takes at least {} argument{plural} "
                      "in addition to the target".format(
                          command, min, plural='' if min == 1 else 's'))
            else:
                print("Error: '{}' takes {} argument{plural} "
                      "in addition to the target".format(
                          command, min, plural='' if min == 1 else 's'))
            return False
        elif len(args) > max:
            surplus = args[max]
            if min != max:
                print("Error: '{}' takes at most {} argument{plural} "
                      "in addition to the target, and '{}' is not a "
                      "command".format(
                          command, max, surplus,
                          plural='' if max == 1 else 's'))
            else:
                print("Error: '{}' takes {} argument{plural} "
                      "in addition to the target, and '{}' is not a "
                      "command".format(
                          command, max, surplus,
                          plural='' if max == 1 else 's'))
            return False
    return True


def execute_action_command_list(command_list, target, lines):
    for command_args in command_list:
        command, args = command_args
        if not args:
            lines = action_commands[command][0](lines, target)
        else:
            lines = action_commands[command][0](lines, target, *args)
    return lines


def get_action_target(args):
    target = None
    if args[0].isdigit():
        target = int(args[0]) - 1
        args = args[1:]
    return args, target


def extract_task_addition(command_list):
    addition = None
    i = 0
    remaining = len(command_list)
    while i < remaining:
        command, args = command_list[i]
        if command == 'a':
            addition = ' '.join(args)
            command_list.pop(i)
            break
        i += 1
    return command_list, addition


def handle_action_commands(args):
    tasks = collect_tasks()

    # if first arg is an int, extract it as target
    args, target = get_action_target(args)
    # make command list out of args
    command_list = assemble_action_command_list(args, target)
    # get addition from command list if exists else none
    command_list, addition = extract_task_addition(command_list)

    # if there's an addition, fail if also target, else add addition
    # and make it the target
    if addition is not None:
        if target:
            print("Error: can't specify a target task and add"
                  " a task at the same time")
            return
        elif addition == '':
            print("Error: new task must contain text")
            return
        else:
            tasks = add(tasks, addition)
            target = len(tasks) - 1

    if not target:
        command_list, target = prepare_single_action(command_list)

    # return if target None or if int out of range
    if target is None:
        print("Error: No target specified")
        return
    elif target > len(tasks):
        print("Error: task number supplied is {}, but only"
              " {} tasks in list".format(target, len(tasks)))
        return

    if verify_action_command_list(command_list):
        tasks = execute_action_command_list(command_list, target, tasks)
    write_tasks(tasks)


def handle_general_commands(arg):
    tasks = collect_tasks()
    tasks = general_commands[arg](tasks)
    write_tasks(tasks)


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
