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


def add(lines, s):
    created = datetime.date.today().strftime("%Y-%m-%d")
    task = "%s %s\n" % (created, s)
    lines.append(task)
    return lines


def remove_task(lines, linenum):
    followthrough = input('Task: {}\nDelete? (Y/n)'.format(
        lines[linenum].strip()))
    if followthrough == '' or followthrough.lower() == 'y':
        removed = lines.pop(linenum)
        print('Removed: ' + removed.strip())
    return lines


def prefill_input(prompt, prefill):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        result = input(prompt)
    finally:
        readline.set_startup_hook()
    return result


def edit(lines, linenum):
    task = lines[linenum].rstrip()
    task_parts = task.split(' ')
    pre = []
    desc = []
    while len(task_parts) > 0:
        if task_parts[0].startswith(('(', '2', '3')):
            pre.append(task_parts.pop(0))
        else:
            break
    while len(task_parts) > 0:
        if not task_parts[0].startswith(('+', '@', 'P:', 'C:', 'R:')):
            desc.append(task_parts.pop(0))
        else:
            break
    post = task_parts

    desc = prefill_input('Edit task: ', ' '.join(desc))

    task = ' '.join(pre + [desc] + post) + '\n'

    lines[linenum] = task
    return lines


def do(lines, linenum):
    if 'P:' in lines[linenum]:
        id = re.search('P:(\d)', lines[linenum]).group(1)
        lines = unset_parent(lines, linenum)
        lines = clean_orphans(lines, id)
    if 'R:' in lines[linenum]:
        lines = recur_recycle(lines, linenum)
    else:
        lines = mark_done(lines, linenum)
    return lines


def mark_done(lines, linenum):
    if lines[linenum].startswith('('):
        lines = unprioritize(lines, linenum)
    completed = datetime.date.today().strftime("%Y-%m-%d")
    lines[linenum] = "x %s %s" % (completed, lines[linenum])
    return lines


def undo(lines, linenum):
    task = lines[linenum]
    if task.startswith('x '):
        lines[linenum] = task[13:]
    else:
        print('This task was never completed')
    return lines


def unschedule(lines, linenum):
    task = lines[linenum]
    dates = re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}', task)
    if dates:
        lines[linenum] = task[:dates.start()] + task[dates.start()+11:]
    return lines


def assign_duedate(lines, linenum, due):
    # returns unchanged if not scheduled
    task = unschedule(lines, linenum)[linenum]
    if task.startswith('('):  # insert behind priority if one is set
        lines[linenum] = '%s%s %s' % (task[:4], due, task[4:])
    else:
        lines[linenum] = '%s %s' % (due, task)
    return lines


def schedule(lines, linenum, date):
    task = lines[linenum]

    this_year_month_lengths = month_lengths[:]
    if today[0] % 4 == 0:
        this_year_month_lengths[1] += 1

    future_num = re.search('3\d{7}\s', task)
    if future_num:
        lines = future_unset(lines, linenum)

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
    elif date in ('today', 'n'):
        year, month, day = tuple([int(i) for i in today_string.split('-')])
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

    lines = assign_duedate(lines, linenum, due)
    return lines


def catch(lines):
    linenums = []
    for i, line in enumerate(lines):
        date = re.search('\d{4}-\d{2}-\d{2}', line)
        if date:
            if date.group() < today_string:
                linenums.append(i)
    for linenum in linenums:
        new_due = input('Task: {}Due:  '.format(lines[linenum]))
        lines = schedule(lines, linenum, new_due)
    return lines


def unprioritize(lines, linenum):
    task = lines[linenum]
    if re.match('\([A-Z]\)\s', task):
        lines[linenum] = task[4:]
    else:
        print('Task not prioritized')
    return lines


def prioritize(lines, linenum, priority='A'):
    if re.match('\([A-Z]\)\s', lines[linenum]):
        unprioritize(lines, linenum)
    if not priority.isalpha() or len(priority) > 1:
        print("Not a valid priority")
    else:
        priority = priority.upper()
        lines[linenum] = '({}) {}'.format(priority, lines[linenum])
    return lines


def get_contexts(lines):
    contexts = set([])
    for line in lines:
        for c in re.findall('@\w+', line):
            contexts.add(c)
    return contexts


def set_context(lines, linenum, *contexts):
    task = lines[linenum]
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
    lines[linenum] = task
    return lines


def unset_context(lines, linenum, num=1):
    num = int(num)
    task = lines[linenum]
    contexts = [m for m in re.finditer('@\w+', task)]
    if num > len(contexts):
        print("Not that many contexts")
    else:
        start = contexts[num-1].start()
        end = contexts[num-1].end()
        task = task[:start-1] + task[end:]
        lines[linenum] = task
    return lines


def get_projects(lines):
    projects = set([])
    for line in lines:
        for p in re.findall('\+\w+', line):
            projects.add(p)
    return projects


def print_projects(lines):
    projects = get_projects(lines)
    for project in projects:
        print(project.replace('+', ''))


def set_project(lines, linenum, *projects):
    task = lines[linenum]
    for project in projects:
        if '+' + project in task:
            print("That project is already assigned")
            return lines
        insert_before = re.search('@\w+|P:|C:|R:', task)
        if insert_before:
            lines[linenum] = '{}+{} {}'.format(
                task[:insert_before.start()], project,
                task[insert_before.start():])
        else:
            lines[linenum] = task[:-1] + ' +' + project + task[-1:]
    return lines


def unset_project(lines, linenum, num=1):
    num = int(num)
    task = lines[linenum]
    projects = [m for m in re.finditer('\+\w+', task)]
    if num > len(projects):
        print("Not that many projects")
    else:
        start = projects[num-1].start()
        end = projects[num-1].end()
        lines[linenum] = task[:start-1] + task[end:]
    return lines


def reorder(lines):
    """Placeholder for complex reorder op"""
    lines.sort()
    return lines


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
    lines = [l for l in lines if ' x ' not in l[:10]]
    for line in lines:
        due = re.search('\d{4}-\d{2}-\d{2}', line)
        if due:
            due_int = int(due.group().replace('-', ''))
            if due_int < date_int:
                output_lines.append(line)
    return output_lines


def view_today(lines):
    return view_until(lines, add_days(today_string, 1))


def view_this_week(lines):
    return view_until(lines, add_days(today_string, 8))


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
                line = '+ ' + line
            else:
                line = '- ' + line
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
            '\d{4}-\d{2}-\d{2}\s|3\d{7}|P:\w+|C:\w+|R:\w+', '', line))
    return output_lines


def date_headers(lines):
    i = 0
    remaining = len(lines)
    previous_date = ''
    while i < remaining:
        date = re.search('\d{4}-\d{2}-\d{2}', lines[i])
        if date and date.group() != previous_date:
            lines.insert(i, '   _{}_'.format(date.group()))
            previous_date = date.group()
            i += 1
            remaining += 1
        i += 1
    return lines


def get_console_size():
    """returns rows and columns as 2 tuple"""
    return [int(i) for i in os.popen('stty size', 'r').read().split()]


def color(lines):
    color_prefix = '\x1b[38;5;{}m'
    color_unset = '\x1b[0m'
    red = color_prefix.format(1)
    green = color_prefix.format(2)
    yellow = color_prefix.format(3)
    blue = color_prefix.format(4)
    # magenta = color_prefix.format(5)
    # cyan = color_prefix.format(6)
    # white = color_prefix.format(15)
    orange = color_prefix.format(16)
    gray = color_prefix.format(19)

    background = '\x1b[48;5;18m'

    for i in range(len(lines)):
        task = lines[i]
        if re.match('\s*\d+\sx\s', task):
            task = '{}{}{}\n'.format(gray, task.rstrip(), color_unset)
            lines[i] = task
            continue
        task = re.sub('^(\s*\+*\s*)(\d+)', '\g<1>{}\g<2>{}'.format(gray,
                      color_unset), task)
        task = re.sub('\([A-Z]\)', '{}\g<0>{}'.format(red, color_unset), task)
        task = re.sub('\+\w+', '{}\g<0>{}'.format(blue, color_unset), task)

        task = re.sub('^\s*\+', '{}\g<0>{}'.format(red, color_unset), task)
        task = re.sub('@\w+', '{}\g<0>{}'.format(yellow, color_unset), task)
        task = re.sub('(?:P:|C:|R:)\w+', '{}\g<0>{}'
                      .format(gray, color_unset), task)

        dates = [m for m in re.finditer('\d{4}-\d{2}-\d{2}\s{1}', task)]
        j = len(dates) - 1
        while j > -1:
            if len(dates) > 1 and j == 0:
                color = orange
            else:
                color = green
            s = dates[j].start()
            e = dates[j].end()
            task = task[:s]+color+task[s:e]+color_unset+task[e:]
            j -= 1

        rows, columns = get_console_size()
        pad = columns - len(task) + 1
        task = re.sub('.*_(.*)_', '{}    {}\g<1>{}{}'.format(
            background, gray, ' '*pad, color_unset), task)

        lines[i] = task
    return lines


def unset_parent(lines, linenum):
    """takes task string argument, return string without parent tag"""
    task = lines[linenum]
    tag = re.search('P:\d+', task)
    if tag:
        start = tag.start()
        end = tag.end()
        lines[linenum] = task[:start-1] + task[end:]
    return lines


def set_parent(lines, linenum, return_id=False):
    linenum = int(linenum)
    task = lines[linenum]
    if 'P:' in task:
        print("Already set as parent")
    parent_ids = []
    for line in lines:
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
        lines[linenum] = '{}P:{} {}'.format(
            task[:insert_before.start()], parent_id,
            task[insert_before.start():])
    else:
        lines[linenum] = task[:-1] + ' P:' + str(parent_id) + task[-1:]
    if return_id:
        return lines, parent_id
    else:
        return lines


def evaluate_parent(lines, id):
    """check for children matching the parent id,
    if none then remove parent tag.
    """
    children = 0
    for line in lines:
        if 'C:' + str(id) in line:
            children += 1
            # because func is called from child tag removal method before line
            # written, there will be at least 1 child remaining in the lines.
            # that's why the loop returns on >1 instead of >0
            if children > 1:
                return lines
    for i, line in enumerate(lines):
        if "P:" + str(id) in line:
            lines = unset_parent(lines, i)
            break
    return lines


def unset_child(lines, linenum):
    task = lines[linenum]
    tag = re.search('C:\d+', task)
    if tag:
        start = tag.start()
        end = tag.end()
        id = task[start+2:end]
        lines = evaluate_parent(lines, id)
        lines[linenum] = task[:start-1] + task[end:]
    return lines


def clean_orphans(lines, parent_id):
    print(parent_id)
    for line in lines:
        parent_tag = 'P:' + parent_id
        if parent_tag in line:
            return lines
    for i in range(len(lines)):
        child_tag = 'C:' + parent_id
        if child_tag in lines[i]:
            print(1)
            lines = unset_child(lines, i)
    return lines


def set_child(lines, linenum, parent_linenum):

    task = lines[linenum]

    # get parent line from linenum
    parent = lines[int(parent_linenum)]

    # get if parent is already parent get id, else set as parent
    parent_tag = re.search('P:\d+', parent)
    if parent_tag:
        parent_id = parent[parent_tag.start()+2:parent_tag.end()]
    else:
        lines, parent_id = set_parent(lines, parent_linenum, True)

    child_tag = 'C:' + str(parent_id)
    if child_tag in task:
        return lines
    if 'C:' in task:
        task = unset_child(lines, linenum)[linenum]
    insert_before = re.search('P:|C:', task)
    if insert_before:
        lines[linenum] = '{}{} {}'.format(
            task[:insert_before.start()],
            child_tag, task[insert_before.start():])
    else:
        lines[linenum] = task[:-1] + ' ' + child_tag + task[-1:]
    return lines


def contract(lines, linenum):
    task = lines[linenum]
    parent_tag = re.search('P:\d+(?!c)', task)
    if parent_tag:
        lines[linenum] = task[:parent_tag.end()]+'c'+task[parent_tag.end():]
    return lines


def expand(lines, linenum):
    task = lines[linenum]
    parent_tag = re.search('P:\d+c', task)
    if parent_tag:
        lines[linenum] = task[:parent_tag.end()-1]+task[parent_tag.end():]
    else:
        lines[linenum] = task
    return lines


def future_unset(lines, linenum):
    task = lines[linenum]
    future_num = re.search('3\d{7}\s', task)
    if future_num:
        start = future_num.start()
        end = future_num.end()
        lines[linenum] = task[:start] + task[end:]
    return lines


def future_find_last_num(lines):
    for i in range(len(lines)-1, -1, -1):
        last_future_num = re.search('3\d{7}\s', lines[i])
        if last_future_num:
            return int(last_future_num.group()[1:])
    return None


def future_assign_num(lines, linenum, num):
    task = lines[linenum]
    future_num = re.search('3\d{7}\s', task)
    if future_num:
        task = future_unset(lines, linenum)[linenum]
    if task.startswith('('):  # insert behind priority if one is set
        lines[linenum] = '{}3{:0=7d} {}'.format(task[:4], num, task[4:])
    else:
        lines[linenum] = '3{:0=7d} {}'.format(num, task)
    return lines


def future_set(lines, linenum):
    if re.search('\d{4}-\d{1,2}-\d{1,2}\s\d{4}-\d{1,2}-\d{1,2}',
                 lines[linenum]):
        lines = unschedule(lines, linenum)
    last_future_num = future_find_last_num(lines)
    if last_future_num:
        future_num = last_future_num + 10000
        if last_future_num < 9999999:
            lines = future_assign_num(lines, linenum, future_num)
    else:
        lines = future_assign_num(lines, linenum, 10000)
    return lines


def future_redistribute(lines):
    lines.sort()
    last_num = 0
    for i, line in enumerate(lines):
        future_num = re.search('3\d{7}\s', line)
        if future_num:
            num = last_num + 10000
            lines = future_assign_num(lines, i, num)
            last_num = num
    return lines


def future_get_num(task):
    num = re.search('3\d{7}\s', task)
    if num:
        return int(num.group()[1:])
    else:
        return None


def future_order_after(lines, linenum, pivot_index):
    # get num of target (pivot) task
    pivot_index = int(pivot_index)
    pivot_num = future_get_num(lines[pivot_index])
    if not pivot_num:
        print('pivot task not scheduled in fuzzy future')
        return

    # check if there is another line after pivot task
    if pivot_index + 1 < len(lines):
        # if there is a line, check for future num.
        adjacent_num = future_get_num(lines[pivot_index+1])
        # if there is a future num, make num half the difference with pivot
        if adjacent_num:
            half_diff = (adjacent_num - pivot_num) // 2
            num = pivot_num + half_diff
        # if no adjacent number then the pivot task is final future task
        else:
            num = pivot_num + 10000
    else:
        num = pivot_num + 10000

    lines = future_assign_num(lines, linenum, num)

    # redistribute if the gap between tasks becomes too small
    # in the rare event the num reaches > 9999999, redist
    if num != pivot_num + 10000 or num > 9999999:
        lines = future_redistribute(lines)
    return lines


def future_order_before(lines, linenum, pivot_index):
    # get num of target (pivot) task
    pivot_index = int(pivot_index)
    pivot_num = future_get_num(lines[pivot_index])
    if not pivot_num:
        print('task number {} has a due-date, and so can\'t be ordered against'
              .format(pivot_index))
        return lines
    adjacent_num = 0
    if pivot_index != 1:
        adjacent_num = future_get_num(lines[pivot_index-1])
        if not adjacent_num:
            adjacent_num = 0
    half_diff = (pivot_num - adjacent_num) // 2
    num = pivot_num - half_diff

    lines = future_assign_num(lines, linenum, num)

    # redistribute if the gap between tasks becomes too small
    # in the rare event the num reaches > 9999999, redist
    if pivot_num - adjacent_num < 4:
        future_redistribute(lines)
    return lines


def recur_unset(lines, linenum):
    task = lines[linenum]
    tag = re.search('R:\w+', task)
    if tag:
        start = tag.start()
        end = tag.end()
        lines[linenum] = task[:start-1] + task[end:]
    return lines


def recur_set(lines, linenum, days):
    task = lines[linenum]
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
        lines = recur_unset(lines, linenum)

    insert_before = re.search('P:|C:', task)
    if insert_before:
        lines[linenum] = '{}{} {}'.format(
            task[:insert_before.start()], tag, task[insert_before.start():])
    else:
        lines[linenum] = task[:-1] + ' ' + tag + task[-1:]
    return lines


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
    task = ' '.join(task)
    return task


def recur_recycle(lines, linenum):
    task = lines[linenum]

    # append duplicate and do it
    lines.append(task)
    lines = mark_done(lines, len(lines)-1)

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

    # now turn existing task into recurred version
    task = strip_prefixes(task)
    lines[linenum] = '{} {}'.format(today_string, task)
    lines = assign_duedate(lines, linenum, due)

    return lines


def write_changes(lines):
    lines = reorder(lines)
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
    'until': (view_until, 1, 1),
    'clean': (clean, 0, 0),
    'color': (color, 0, 0),
    'nest': (nest, 0, 0),
    'h': (date_headers, 0, 0),
    }

# mins and maxes here exclude lines and target linenum,
# as they never factor into comparisons
action_commands = {
    'a': (add, 1, 100),  # except 'a', which has numbers for show atm
    'ed': (edit, 0, 0),
    'rm': (remove_task, 0, 0),
    'do': (do, 0, 0),
    'undo': (undo, 0, 0),
    's': (schedule, 1, 1),
    'us': (unschedule, 0, 0),
    'p': (prioritize, 1, 1),
    'up': (unprioritize, 0, 0),
    'c': (set_context, 1, 9),
    'uc': (unset_context, 1, 1),
    'pr': (set_project, 1, 9),
    'upr': (unset_project, 1, 1),
    'sub': (set_child, 1, 1),
    'usub': (unset_child, 0, 0),
    'cn': (contract, 0, 0),
    'ex': (expand, 0, 0),
    'f': (future_set, 0, 0),
    'mb': (future_order_before, 1, 1),
    'ma': (future_order_after, 1, 1),
    're': (recur_set, 1, 1),
    'ure': (recur_unset, 0, 0),
    }


general_commands = {
    'catch': catch,
    }


def assemble_view_command_list(args):
    """
    Given a list of args, scan for names corresponding to functions,
    return a list of tuples, where the first item is a found command name
    the second is a list of the arguments the followed.
    tuples containing 'nest' or 'clean' commands are moved to end of list.
    """
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
    i = 0
    while i < len(command_list):
        if command_list[i][0] == 'color':
            command_list.append(command_list.pop(i))
        i += 1

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
    # number lines differently depending on display type
    commands = [c for c, a in command_list]
    if 'nest' in commands:
        lines = ["{} {}".format(i, t) for i, t in enumerate(file)]
    else:
        lines = ["{:>3} {}".format(i, t) for i, t in enumerate(file)]

    for command_args in command_list:
        command, args = command_args
        if not args:
            lines = view_commands[command][0](lines)
        else:
            lines = view_commands[command][0](lines, *args)
    for line in lines:
        print(line.rstrip())


def handle_view_commands(args):
    command_list = assemble_view_command_list(args)
    if verify_view_command_list(command_list):
        execute_view_command_list(command_list)


def get_action_target(args):
    target = None
    if args[0].isdigit():
        target = int(args[0])
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


def assemble_action_command_list(args):
    command_list = []
    task_text = False
    i = 0
    while i < len(args):
        arg = args[i]
        if task_text is False:
            if arg in action_commands.keys():
                command_args = (arg, [])
                command_list.append(command_args)
                # set to grab task text if command is a
                task_text = arg == 'a'
                # manually grab args for some commands because they're
                # also sometimes commands
                if arg in ['s', 'p']:
                    i += 1
                    if args[i].isdigit():
                        command_list[-1][1].append(args[i])
                        i += 1
                    if args[i] in ['a', 'f', 's', 'c']:
                        command_list[-1][1].append(args[i])
                    else:
                        i -= 1
            else:
                command_list[-1][1].append(arg)
        else:
            if arg == ',':
                task_text = False
            else:
                command_list[-1][1].append(arg)
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
        target = int(command_list[0][1][0])
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


def handle_action_commands(args):
    lines = file[:]

    # if first arg is an int, extract it as target
    args, target = get_action_target(args)

    # make command list out of args
    command_list = assemble_action_command_list(args)

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
            lines = add(lines, addition)
            target = len(lines) - 1

    # if there's no initial integer or added task, it must be
    # a single command with target as first arg. check for validity
    # and process
    if not target:
        command_list, target = prepare_single_action(command_list)

    # return if target None or if int out of range
    if target is None:
        print("Error: No target specified")
        return
    elif target >= len(lines):
        print("Error: task number supplied is {}, but only"
              " {} tasks in list".format(target, len(lines)))
        return

    if verify_action_command_list(command_list):
        lines = execute_action_command_list(command_list, target, lines)

    write_changes(lines)


def handle_general_commands(arg):
    lines = file[:]
    lines = general_commands[arg](lines)
    write_changes(lines)


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
