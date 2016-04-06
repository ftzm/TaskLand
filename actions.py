#!/usr/bin/python
"""functions for making changes to a tasks or the task list"""
import sys
import datetime
import readline
import re
import copy
import utils
import parse


def add(tasks, text):
    """add a task"""
    task = parse.Task(text)
    task.added = datetime.date.today()
    task.due = datetime.date.today()
    tasks.append(task)
    return tasks


def prefill_input(prompt, prefill):
    """prompt for input with supplied prefill text"""
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        result = input(prompt)
    finally:
        readline.set_startup_hook()
    return result


def edit(tasks, num):
    """edit a tasks's text"""
    tasks[num].text = prefill_input('Edit: ', tasks[num].text)
    return tasks


def remove(tasks, num):
    """remove a task"""
    followthrough = input('Task: {}\nDelete? (Y/n)'.format(
        tasks[num].compose_line()))
    if followthrough == '' or followthrough.lower() == 'y':
        removed = tasks.pop(num)
        print('Removed: ' + removed.compose_line())
    return tasks


def complete(tasks, num):
    """mark a task as completed"""
    tasks[num].priority = None
    if tasks[num].parent_id is not None:
        tasks[num].parent_id = None
        tasks = clean_orphans(tasks, tasks[num].parent_id)
    if tasks[num].repeat is not None:
        tasks = repeat_recycle(tasks, num)
    else:
        tasks[num].x = 'x'
        tasks[num].done = datetime.date.today()
    return tasks


def undo(tasks, num):
    """unmark a task as completed"""
    tasks[num].x = ''
    tasks[num].done = None
    return tasks


def schedule(tasks, num, string):
    """schedule a task as due a certain date using date string"""
    date = utils.code_to_datetime(string)
    tasks[num].due = date
    return tasks


def unschedule(tasks, num):
    """remove due date from a task"""
    tasks[num].due = None
    return tasks


def prioritize(tasks, num, priority='A'):
    """asign a priority (A-Z) to a task"""
    if not priority.isalpha() or len(priority) > 1:
        print("Not a valid priority")
    else:
        priority = priority.upper()
        tasks[num].priority = '({})'.format(priority)
    return tasks


def unprioritize(tasks, num):
    """remove a priority from a task"""
    tasks[num].priority = None
    return tasks


def set_context(tasks, num, *contexts):
    """add contexts to a task"""
    for context in contexts:
        if context not in tasks[num].contexts:
            tasks[num].contexts.append(context)
    return tasks


def unset_context(tasks, num, i):
    """remove the n context from a task"""
    try:
        tasks[num].contexts.pop(i-1)
    except IndexError:
        sys.exit("Error: invalid context number")
    return tasks


def set_project(tasks, num, *projects):
    """add a project to a task"""
    for project in projects:
        if project not in tasks[num].projects:
            tasks[num].projects.append(project)
    return tasks


def unset_project(tasks, num, i=1):
    """remove a project from a task"""
    try:
        tasks[num].projects.pop(int(i)-1)
    except IndexError:
        sys.exit("Error: invalid project number")
    return tasks


def parent_set(tasks, num):
    """
    mark a task as a parent such that other tasks can become its children.

    finds all other parent ids in task list and assigns a new one.
    """
    parent_ids = [t.parent_id for t in tasks if t.parent_id is not None]
    for i in range(1, len(parent_ids)+2):
        if str(i) not in parent_ids:
            new_id = i
            break
    tasks[num].parent_id = str(new_id)
    return tasks


def parent_unset(tasks, num):
    """
    remove a parent id from a task.
    """
    tasks[num].parent_id = None
    return tasks


def parent_check_empty(tasks, id_num):
    """
    removes parent id if no corresponding children.

    checks if any task possesses a given child id, and if not, finds
    the task with the corresponding parent id and removes that id.
    """
    if not any(t.child_id == id_num for t in tasks):
        for t in tasks:
            if t.parent_id == id_num:
                t.parent_id = None
    return tasks


def child_set(tasks, num, parent):
    """make a task the child of another task."""
    parent = int(parent) - 1
    if tasks[parent].parent_id is None:
        tasks = parent_set(tasks, parent)
    tasks[num].child_id = tasks[parent].parent_id
    return tasks


def child_unset(tasks, num):
    """remove child id from task, checks if parent childless"""
    child_id = tasks[num].child_id
    tasks[num].child_id = None
    tasks = parent_check_empty(tasks, child_id)
    return tasks


def clean_orphans(tasks, id_num):
    """remove child id from all tasks"""
    for t in tasks:
        if t.child_id == id_num:
            t.child_id = None
    return tasks


def contract(tasks, num):
    """set a task as contracted so its children are hidden in nest view"""
    tasks[num].contracted = True
    return tasks


def expand(tasks, num):
    """expand a contracted task so that its children show in nest view"""
    tasks[num].contracted = True
    return tasks


def order_after(tasks, num, pivot):
    """place a task after another in the list"""
    pivot_i = int(pivot)-1
    if tasks[num].due != tasks[pivot_i].due:
        print('Can\'t order tasks with different due dates against each other')
        return tasks
    if pivot_i > num:
        pivot_i -= 1
    moved = tasks.pop(num)
    tasks.insert(pivot_i+1, moved)
    return tasks


def order_before(tasks, num, pivot):
    """place a task before another in the list"""
    pivot_i = int(pivot)-1
    if tasks[num].due != tasks[pivot_i].due:
        print('Can\'t order tasks with different due dates against each other')
        return tasks
    if pivot_i > num:
        pivot_i -= 1
    moved = tasks.pop(num)
    tasks.insert(pivot_i, moved)
    return tasks


def repeat_unset(tasks, num):
    """remove the repeat tag from a task"""
    tasks[num].repeat = None
    return tasks


def repeat_set(tasks, num, string):
    """set a task as repeating, specify repeat type and details in tag"""
    t = tasks[num]
    if t.added is None:
        t.added = datetime.date.today()
    if re.match(r'a\d{1,2}$', string):
        t.repeat = string
    elif re.match(r'e\d{1,2}$', string):
        t.repeat = string
        if t.added is not None and t.due is not None:
            t.repeat = t.repeat + 'c' + str((t.due - t.added).days)
        else:
            t.repeat += 'c0'
    elif re.match('[mtwrfsu]{1,7}', string):
        t.repeat = ''.join(c for c in "mtwrfsu" if c in string)
    else:
        print('Error: Not a valid recur format')
    return tasks


def repeat_recycle(tasks, num):
    """on completion of repeating task, make new due date and update tag"""
    t = tasks[num]
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
    """iterate over all tasks due before today and ask for new duedate"""
    for i, t in enumerate(tasks):
        if t.due and t.due < datetime.date.today() and t.x is None:
            sched = input('{}\nNew due date (blank for future): '.format(
                t.text))
            if sched == '':
                tasks = unschedule(tasks, i)
            else:
                t.due = utils.code_to_datetime(sched)
    return tasks
