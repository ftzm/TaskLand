#!/usr/bin/python
import sys
import datetime
import re
import readline
import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "config.rc"), "r") as f:
    todolist = f.readlines()[0].strip()

with open(todolist, "r") as f:
    file = f.readlines()

weekdays = ['u', 'm', 't', 'w', 'r', 'f', 's']
today = datetime.date.today().strftime("%Y %m %d %w")
today = [int(i) for i in list(filter(None, today.split(' ')))]
today_string = '{}-{:0=2d}-{:0=2d}'.format(today[0], today[1], today[2])
month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def add(words):
    created = datetime.date.today().strftime("%Y-%m-%d")
    s = ' '.join(words)
    task = "%s %s\n" % (created, s)
    file.append(task)


def remove_task(task, linenum):
    followthrough = input('Task: {}\nDelete? (Y/n)'.format(task.strip()))
    if followthrough == '' or followthrough.lower() == 'y':
        removed = file.pop(linenum)
        print('Removed: ' + removed.strip())


def prefill_input(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        result = input(prompt)
    finally:
        readline.set_startup_hook()
    return result


def edit(task):
    task = prefill_input('Edit task: ', task.strip())
    return task + '\n'


def do(task):
    completed = datetime.date.today().strftime("%Y-%m-%d")
    return "x %s %s" % (completed, task)


def undo(task):
    if task.startswith('x '):
        return task[13:]
    else:
        print('This task was never completed')
        return task


def unschedule(task):
    dates = re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}', task)
    if dates:
        return task[:dates.start()] + task[dates.start()+11:]
    else:
        return task


def assign_duedate(task, due):
    task = unschedule(task)  # returns unchanged if not scheduled
    if task.startswith('('):  # insert behind priority if one is set
        return '%s%s %s' % (task[:4], due, task[4:])
    else:
        return '%s %s' % (due, task)


def schedule(task, date):

    this_year_month_lengths = month_lengths[:]
    if today[0] % 4 == 0:
        this_year_month_lengths[1] += 1

    future_num = re.search('3\d{7}\s', task)
    if future_num:
        task = future_unset(task)

    # catch various date formats, set them up for processing
    if re.match('\d{1,2}$', date):
        year, month, day = None, None, int(date)
    elif re.match('\d{1,2}-\d{1,2}$', date):
        year, month, day = None, tuple([int(i) for i in date.split('-')])
    elif re.match('\d{4}-\d{1,2}-\d{1,2}$', date):
        year, month, day = tuple([int(i) for i in date.split('-')])
    elif date in weekdays:
        year, month = None, None
        daynum = weekdays.index(date)
        if daynum > today[3]:
            offset = daynum - today[3]
        else:
            offset = 7 - (today[3] - daynum)
        day = today[2] + offset
        if day > month_lengths[today[1]-1]:
            day -= month_lengths[today[1]-1]
    else:
        print('invalid date format')
        return task

    # increment month if day is lower than today
    if day < today[2] and month is None:
        month = today[1] + 1
        if month > 12:
            month = 1

    # set unset months and years
    if not month:
        month = today[1]
    if not year:
        year = today[0]

    # if month lower than today's, due next year.
    if month < today[1]:
        year = today[0] + 1

    # handle edge cases where impossible dates are entered.
    if month > 12:
        print("Month must be 12 or below")
        return task
    if day > month_lengths[month-1]:
        print("Not that many days in the month")
        return task

    due = '{}-{:0=2d}-{:0=2d}'.format(year, month, day)

    return assign_duedate(task, due)


def unprioritize(task):
    if re.match('\([A-Z]\)\s', task):
        return task[4:]
    else:
        print('Task not prioritized')
        return task


def prioritize(task, priority='A'):
    if re.match('\([A-Z]\)\s', task):
        unprioritize(task)
    return '({}) {}'.format(priority, task)


def get_contexts():
    contexts = set([])
    for line in file:
        for c in re.findall('@\w+', line):
            contexts.add(c)
    return contexts


def set_context(task, contexts):
    for context in contexts:
        if '@' + context in task:
            print("Context @{} is already assigned".format(context))
            break
        insert_before = re.search('P:|C:|R:', task)
        if insert_before:
            task = '{}@{} {}'.format(task[:insert_before.start()],
                                     context, task[insert_before.start():])
        else:
            task = task[:-1] + ' @' + context + task[-1:]
    return task


def unset_context(task, num=1):
    contexts = [m for m in re.finditer('@\w+', task)]
    if num > len(contexts):
        print("Not that many contexts")
        return task
    start = contexts[num-1].start()
    end = contexts[num-1].end()
    return task[:start-1] + task[end:]


def get_projects():
    projects = set([])
    for line in file:
        for p in re.findall('\+\w+', line):
            projects.add(p)
    return projects


def print_projects():
    projects = get_projects()
    for project in projects:
        print(project.replace('+', ''))


def set_project(task, project):
    if '+' + project in task:
        print("That project is already assigned")
        return task
    insert_before = re.search('@\w+|P:|C:|R:', task)
    if insert_before:
        return '{}+{} {}'.format(task[:insert_before.start()],
                                 project, task[insert_before.start():])
    else:
        return task[:-1] + ' +' + project + task[-1:]


def unset_project(task, num=1):
    projects = [m for m in re.finditer('\+\w+', task)]
    if num > len(projects):
        print("Not that many projects")
        return task
    start = projects[num-1].start()
    end = projects[num-1].end()
    return task[:start-1] + task[end:]


def reorder():
    """Placeholder for complex reorder op"""
    file.sort()


def fetch_lines():
    output_lines = ['%d %s' % (i, l) for i, l in enumerate(file)]
    return output_lines


def view_including(lines, args):
    """Filter function. prints only lines including first argument"""
    output_lines = []
    for line in lines:
        for s in args:
            if s in line:
                output_lines.append(line)
    return output_lines


def view_excluding(lines, args):
    """Filter function. prints only lines excluding argument"""
    output_lines = []
    for line in lines:
        for s in args:
            if s not in line:
                output_lines.append(line)
    return output_lines


def view_until(lines, date):
    date_int = int(date.replace('-', ''))
    output_lines = []
    for line in lines:
        due = re.search('\d{4}-\d{2}-\d{2}', line)
        if due:
            due_int = int(due.group().replace('-', ''))
            if due_int <= date_int:
                output_lines.append(line)
    return output_lines


def view_today(lines):
    return view_until(lines, today_string)


def view_this_week(lines):
    return view_until(lines, add_days(today_string, 7))


def view_by_project(lines):
    """For every project, returns every task containing that tag"""
    output_lines = []
    projects = sorted(list(get_projects()))
    for project in projects:
        for line in lines:
            if project in line:
                output_lines.append(line)
    return output_lines


def view_by_context(lines):
    """For every context, returns every task containing that tag"""
    output_lines = []
    contexts = sorted(list(get_projects()))
    for context in contexts:
        for line in lines:
            if context in line:
                output_lines.append(line)
    return output_lines


def view_projects(lines, args):
    filter_projects = ['+' + p for p in args]
    output_lines = []

    # verify filter projects
    existing_projects = get_projects()
    remaining_filter_projects = len(filter_projects)
    i = 0
    while i > remaining_filter_projects:
        if filter_projects[i] not in existing_projects:
            print("{} is not an existing project".format(filter_projects[i]))
            filter_projects.pop(i)
            remaining_filter_projects -= 1
        else:
            i += 1

    for line in lines:
        for project in filter_projects:
            if project in line:
                output_lines.append(line)
                break

    return output_lines


def view_contexts(lines, args):
    filter_contexts = ['@' + p for p in args]
    output_lines = []

    # verify filter contexts
    existing_contexts = get_contexts()
    remaining_filter_contexts = len(filter_contexts)
    i = 0
    while i > remaining_filter_contexts:
        if filter_contexts[i] not in existing_contexts:
            print("{} is not an existing context".format(filter_contexts[i]))
            filter_contexts.pop(i)
            remaining_filter_contexts -= 1
        else:
            i += 1

    for line in lines:
        for context in filter_contexts:
            if context in line:
                output_lines.append(line)
                break

    return output_lines


def nest(lines):

    output_lines = []
    # make list of parent nums and line stings tuples
    parents = []
    for line in lines:
        parent = re.search('P:\d+', line)
        if parent:
            num = line[parent.start()+2:parent.end()]
            parents.append((num, line))

    # sort parents so that they are dealt with top to bottom,
    # with child-parents coming after their parents so they aren't moved
    # after their children in the next sorting step.

    # put top level parents at top
    insert_point = 0
    i = 0
    while i < len(parents):
        if 'C:' not in parents[i][1]:
            parents.insert(insert_point, parents.pop(i))
            insert_point += 1
        i += 1
    sorted_parents = insert_point  # number of entries from top that are sorted

    # iterate over sorted tasks, looking for all unsorted children parents
    # put each child parent under its parent

    i = 0
    while i < sorted_parents:
        child_tag = 'C:' + str(parents[i][0])
        insert_point = i + 1
        j = sorted_parents
        while j < len(parents):
            if child_tag in parents[j][1]:
                parents.insert(insert_point, parents.pop(j))
                sorted_parents += 1
                insert_point += 1
            j += 1
        i += 1

    # rearrange children to follow their parents
    for id, line in parents:
        # pop children from lines
        children = []
        list_length = len(lines)
        i = 0
        while i < list_length:
            if 'C:'+id in lines[i]:
                children.append(lines.pop(i))
                list_length -= 1
            else:
                i += 1
        # find where to insert and insert all children
        insert_point = lines.index(line) + 1
        for child in children:
            lines.insert(insert_point, child)
            insert_point += 1

    # pretty indented print
    hierarchy = []
    closed_id = 0
    latest_parent_id = 0
    for line in lines:
        orphan = False
        # closed/open indicator, set switch to hide following tasks
        parent_tag = re.search('P:\w+', line)
        if parent_tag:
            latest_parent_id = parent_tag.group().replace('c', '')[2:]
            if 'c' not in parent_tag.group():
                line = '\033[31m+\033[39m ' + line
            else:
                line = '\033[31m-\033[39m ' + line
                closed_id = latest_parent_id
        # align non plus or minused tasks
        else:
            line = '  ' + line
        # calc indent level based on degree of nested child tags
        child_code = re.search('C:\w+', line)
        if child_code:
            child_code = child_code.group()[2:]
            if child_code not in hierarchy:
                # necessary to check if child is orphan
                if child_code == latest_parent_id:
                    hierarchy.append(child_code)
                else:
                    hierarchy = []
                    orphan = True
            else:
                hierarchy = hierarchy[:hierarchy.index(child_code)+1]
            if not orphan:
                indents = hierarchy.index(child_code)+1
            else:
                indents = 0
            line = "   " * indents + line
        else:
            hierarchy = []
        # if the closed_id is in the hierarchy, then the task will be hidden
        if closed_id not in hierarchy:
            output_lines.append(line)

    return output_lines


def clean(lines):
    output_lines = []
    for line in lines:
        output_lines.append(re.sub(
            '\d{4}-\d{2}-\d{2}\s|3\d{7}|P:\w|C:\w|R:\w', '', line))
    return output_lines


def unset_parent(task):
    """takes task string argument, return string without parent tag"""
    tag = re.search('P:\d+', task)
    start = tag.start()
    end = tag.end()
    return task[:start-1] + task[end:]


def set_parent(task):
    if 'P:' in task:
        print("Already set as parent")
    parent_ids = []
    for line in file:
        for c in re.findall('P:\d+', line):
            parent_ids.append(int(c[2:]))
    parent_id = 0
    i = 1
    while parent_id == 0:
        if i not in parent_ids:
            parent_id = i
        else:
            i += 1
    insert_before = re.search('R:', task)
    if insert_before:
        return '{}P:{} {}'.format(task[:insert_before.start()],
                                  parent_id, task[insert_before.start():])
    else:
        return task[:-1] + ' P:' + str(parent_id) + task[-1:], parent_id


def evaluate_parent(id):
    """check for children matching the parent id,
    if none then remove parent tag.
    """
    children = 0
    for line in file:
        if 'C:' + str(id) in line:
            children += 1
            # because func is called from child tag removal method before line
            # written, there will be at least 1 child remaining in the file.
            # that's why the loop returns on >1 instead of >0
            if children > 1:
                return
    for i, line in enumerate(file):
        if "P:" + str(id) in line:
            task = unset_parent(line)
            linenum = i
            break
    file[linenum] = task


def unset_child(task):
    tag = re.search('C:\w+', task)
    start = tag.start()
    end = tag.end()
    id = task[start+2:end]
    evaluate_parent(id)
    return task[:start-1] + task[end:]


def set_child(task, parent_linenum):

    # get parent line from linenum
    parent = file[int(parent_linenum)]

    # get if parent is already parent get id, else set as parent
    parent_tag = re.search('P:\d+', parent)
    if parent_tag:
        parent_id = parent[parent_tag.start()+2:parent_tag.end()]
    else:
        file[int(parent_linenum)], parent_id = set_parent(parent)

    child_tag = 'C:' + str(parent_id)
    if child_tag in task:
        return task
    if 'C:' in task:
        task = unset_child(task)
    insert_before = re.search('P:|C:', task)
    if insert_before:
        return '{}{} {}'.format(task[:insert_before.start()],
                                child_tag, task[insert_before.start():])
    else:
        return task[:-1] + ' ' + child_tag + task[-1:]


def contract(task):
    parent_tag = re.search('P:\d+(?!c)', task)
    if parent_tag:
        return task[:parent_tag.end()]+'c'+task[parent_tag.end():]
    return task


def expand(task):
    parent_tag = re.search('P:\d+c', task)
    if parent_tag:
        return task[:parent_tag.end()-1]+task[parent_tag.end():]
    else:
        return task


def future_unset(task):
    future_num = re.search('3\d{7}\s', task)
    if future_num:
        start = future_num.start()
        end = future_num.end()
        return task[:start] + task[end:]
    else:
        return task


def future_find_last_num():
    for i in range(len(file)-1, -1, -1):
        last_future_num = re.search('3\d{7}\s', file[i])
        if last_future_num:
            return int(last_future_num.group()[1:])
    return None


def future_assign_num(task, num):
    future_num = re.search('3\d{7}\s', task)
    if future_num:
        task = future_unset(task)
    if task.startswith('('):  # insert behind priority if one is set
        return '{}3{:0=7d} {}'.format(task[:4], num, task[4:])
    else:
        return '3{:0=7d} {}'.format(num, task)


def future_set(task):
    if re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}', task):
        task = unschedule(task)
    last_future_num = future_find_last_num()
    if last_future_num:
        future_num = last_future_num + 10000
        if last_future_num < 9999999:
            return future_assign_num(task, future_num)
    else:
        return future_assign_num(task, 10000)


def future_redistribute():
    file.sort()
    last_num = 0
    for i, line in enumerate(file):
        future_num = re.search('3\d{7}\s', line)
        if future_num:
            num = last_num + 10000
            file[i] = future_assign_num(line, num)
            last_num = num


def future_get_num(task):
    num = re.search('3\d{7}\s', task)
    if num:
        return int(num.group()[1:])
    else:
        return None


def future_order_after(moved_index, pivot_index):
    # get num of target (pivot) task
    pivot_num = future_get_num(file[pivot_index])
    if not pivot_num:
        print('pivot task not scheduled in fuzzy future')
        return

    # check if there is another line after pivot task
    if pivot_index + 1 < len(file):
        # if there is a line, check for future num.
        adjacent_num = future_get_num(file[pivot_index+1])
        # if there is a future num, make num half the difference with pivot
        if adjacent_num:
            half_diff = (adjacent_num - pivot_num) // 2
            num = pivot_num + half_diff
        # if no adjacent number then the pivot task is final future task
        else:
            num = pivot_num + 10000
    else:
        num = pivot_num + 10000

    file[moved_index] = future_assign_num(file[moved_index], num)

    # redistribute if the gap between tasks becomes too small
    # in the rare event the num reaches > 9999999, redist
    if adjacent_num - pivot_num < 4 or num > 9999999:
        future_redistribute()


def future_order_before(moved_index, pivot_index):
    # get num of target (pivot) task
    pivot_num = future_get_num(file[pivot_index])
    if not pivot_num:
        print('pivot task not scheduled in fuzzy future')
        return
    adjacent_num = 0
    if pivot_index != 1:
        adjacent_num = future_get_num(file[pivot_index-1])
        if not adjacent_num:
            adjacent_num = 0
    half_diff = (pivot_num - adjacent_num) // 2
    num = pivot_num - half_diff

    file[moved_index] = future_assign_num(file[moved_index], num)

    # redistribute if the gap between tasks becomes too small
    # in the rare event the num reaches > 9999999, redist
    if pivot_num - adjacent_num < 4:
        future_redistribute()


def recur_unset(task):
    tag = re.search('R:\w+', task)
    start = tag.start()
    end = tag.end()
    return task[:start-1] + task[end:]


def recur_set(task, days):
    # makes recur tag
    if re.match('e\d{1,2}$|a\d{1,2}$', days):
        tag = 'R:' + days
    elif re.match('[mtwrfsu]{1,7}', days):
        tag = 'R:'
        for c in "mtwrfsu":
            if c in days:
                tag += c
    else:
        print('Not a valid recur format')
        return task

    dates = re.findall('\d{4}-\d{2}-\d{2}', task)
    if len(dates) == 2:
        due, created = dates
        correction = get_days_diff(due - created)
        tag += 'c' + correction
    elif len(dates) == 1:
        tag += 'c0'
    else:
        print('This task needs a due date')
        return task

    # remove old recur tag
    if 'R:' in task:
        task = recur_unset(task)

    insert_before = re.search('P:|C:', task)
    if insert_before:
        return '{}{} {}'.format(task[:insert_before.start()],
                                tag, task[insert_before.start():])
    else:
        return task[:-1] + ' ' + tag + task[-1:]


def add_days(date, num):
    year, month, day = date.split('-')
    year, month, day = int(year), int(month)-1, int(day)
    day += num
    while day > month_lengths[month]:
        day -= month_lengths[month]
        month += 1
        if month > 11:
            year += 1
            month = 0
    return '{}-{:0=2d}-{:0=2d}'.format(year, month+1, day)


def days_since_2000(date):
    date = [int(n) for n in date.split('-')]
    date_yeardays = (date[0]-2000) * 365 + (date[0]-2001) // 4
    date_monthdays = sum([month_lengths[n] for n in range(date[1]-1)])
    if date[1] > 2 and date[0] % 4 == 0:
        date_monthdays += 1
    return date_yeardays + date_monthdays + date[2]


def get_days_diff(date1, date2):
    return days_since_2000(date1) - days_since_2000(date2)


def strip_prefixes(task):
    task = task.split(' ')
    start = 0
    while True:
        if task[start].startswith('(') or re.match('3\d{7}', task[start]) \
                or re.match('\d{4}-\d{2}-\d{2}', task[start]):
            start += 1
        else:
            break
    return ' '.join(task[start:])


def recur_recycle(task):

    # fix first run of e10, so doing it doesnt schedule 20 days later
    # could add c0 to first run
    # allow creation of e tasks on any day, correct to compensate

    tag = re.search('R:\w+', task)
    days = tag.group()[2:]
    if 'a' in days:
        offset = int(days[1:])
        due = add_days(today_string, offset)
    elif 'e' in days:
        days = days[1:].split('c')  # split by / in case /n appended
        created = re.findall('\d{4}-\d{1,2}-\d{1,2}', task)[-1]
        offset = int(days[0])

        # get date task should have been done on (as it may not be today)
        base_date = add_days(created, int(days[-1]))

        # assign due off of base date, make sure after today
        due = add_days(base_date, offset)
        while get_days_diff(due, today_string) < 1:
            due = add_days(base_date, offset)

        # figure out correction offset if today wasn't the due day
        # apply to tag
        if due != add_days(today_string, offset):
            correction = get_days_diff(due, today_string)
            task = '{}R:e{}c{}{}'.format(task[:tag.start()], offset,
                                         correction, task[tag.end():])
        # if we are aligned, and there is a correction offset, remove it
        elif len(days) > 1:
            task = '{}R:e{}{}'.format(task[:tag.start()], offset,
                                      task[tag.end():])

    else:
        offset = 1
        i = today[3] + 1
        while i != today[3]:
            if i > 6:
                i = 0
            if weekdays[i] in days:
                break
            i += 1
            offset += 1
        due = add_days(today_string, offset)

    removed = do(task)
    fresh_task = strip_prefixes(task)
    fresh_task = '{} {}'.format(today_string, fresh_task)
    fresh_task = assign_duedate(fresh_task, due)

    file.append(removed)
    return fresh_task


def write_changes(lines):
    reorder()
    with open(todolist, "w") as f:
        for line in lines:
            f.write(line)


view_commands = {
    'bc': (view_by_context, 0, 0),
    'bpr': (view_by_project, 0, 0),
    'vc': (view_contexts, 1, 9),
    'vpr': (view_projects, 1, 9),
    'incl': (view_including, 1, 9),
    'excl': (view_excluding, 1, 9),
    'today': (view_today, 0, 0),
    'week': (view_this_week, 0, 0),
    'until': (view_until, 0, 0),
    'nest': (nest, 0, 0),
    'clean': (clean, 0, 0),
    }

action_commands = {
    'a': (add, 1, 100),
    'rm': (remove_task, 1, 1),
    'do': (do, 1, 1),
    'undo': (undo, 1, 1),
    's': (schedule, 2, 2),
    'us': (unschedule, 1, 1),
    'p': (prioritize, 2, 2),
    'up': (unprioritize, 1, 1),
    'c': (set_context, 2, 9),
    'uc': (unset_context, 1, 1),
    'pr': (set_project, 2, 2),
    'upr': (unset_project, 1, 1),
    'sub': (set_child, 2, 2),
    'usub': (unset_child, 1, 1),
    'cn': (contract, 1, 1),
    'ex': (expand, 1, 1),
    'f': (future_set, 1, 1),
    'mb': (future_order_before, 2, 2),
    'ma': (future_order_after, 2, 2),
    're': (recur_set, 2, 2),
    'ure': (recur_unset, 1, 1),
    }


def assemble_view_command_list(args):
    command_list = []
    for arg in args:
        if arg in view_commands.keys():
            command_args = (arg, [])
            command_list.append(command_args)
        else:
            command_list[-1][1].append(arg)
    i = 0
    while i < len(command_list):
        if command_list[i][0] == 'nest':
            command_list.append(command_list.pop(i))
        i += 1
    i = 0
    while i < len(command_list):
        if command_list[i][0] == 'clean':
            command_list.append(command_list.pop(i))
        i += 1

    return command_list


def assemble_action_command_list(args):
    task_text = False
    for arg in args:
        if task_text == False:
            if arg in view_commands.keys():
                command_args = (arg, [])
                command_list.append(command_args)
                task_text = arg == 'a'
            else:
                command_list[-1][1].append(arg)
        else:
            if arg == ',':
                task_text = False
            else:
                command_list[-1][1].append(arg)

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
    lines = fetch_lines()
    for command_args in command_list:
        command, args = command_args
        if not args:
            lines = view_commands[command][0](lines)
        else:
            lines = view_commands[command][0](lines, args)
    for line in lines:
        print(line.rstrip())

def execute_action_command_list(command_list):
    lines = fetch_lines()
    for command_args in command_list:
        command, args = command_args
        if not args:
            lines = view_commands[command][0](lines)
        else:
            lines = view_commands[command][0](lines, args)
    for line in lines:
        print(line.rstrip())

def main(args):
    if args[0] in view_commands.keys():
        command_list = assemble_view_command_list(args)
        if not verify_view_command_list(command_list):
            return
        execute_view_command_list(command_list)
    elif args[0] in action_commands.keys():
        command_list = assemble_action_command_list(args)
        execute_action_command_list(command_list)
    else:
        pass


if __name__ == "__main__":  # why do I use this
    main(sys.argv[1:])
