#!/usr/bin/python
import parse
import datetime
import readline
import re
import copy
import utils


def add(tasks, s):
    task = parse.Task(s)
    task.added = datetime.date.today()
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
    date = utils.code_to_datetime(s)
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
    tasks[n].projects.pop(int(i)-1)
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
    if t.added is None:
        t.added = datetime.date.today()
    if re.match('a\d{1,2}$', s):
        t.repeat = s
    elif re.match('e\d{1,2}$', s):
        t.repeat = s
        if t.added is not None and t.due is not None:
            t.repeat = t.repeat + 'c' + str((t.due - t.added).days)
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
        interval = int(t.repeat[1:])
        t.due = datetime.date.today() + datetime.timedelta(interval)
    elif 'e' in t.repeat:
        nums = t.repeat[1:].split('c')
        interval = int(nums[0])
        # date it should have been done on ([-1] to use correction if there)
        intended_date = t.added + datetime.timedelta(int(nums[-1]))
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
            if utils.weekdays[i] in t.repeat:
                break
            i += 1
            interval += 1
        t.due = td + datetime.timedelta(interval)

    # now turn existing task into recurred version
    t.added = td
    t.priority = None
    return tasks


def catch(tasks):
    for i, t in enumerate(tasks):
        if t.due < datetime.date.today() and \
                t.x is None and t.due is not None:
            sched = input('{}\nNew due date (blank for future): '.format(
                t.text))
            if sched == '':
                tasks = future_set(tasks, i)
            else:
                t.due = utils.code_to_datetime(sched)
    return tasks
