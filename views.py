#!/usr/bin/python
import os
import utils
import datetime


def view_by_project(tasks):
    return [t for p in utils.projects_get(tasks) for t in tasks
            if p in t.projects]


def view_by_context(tasks):
    return [t for p in utils.contexts_get(tasks) for t in tasks
            if p in t.contexts]


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
    date = utils.code_to_datetime(s)
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
            if t.due == datetime.date.today():
                title = 'Today'
            else:
                title = t.due.strftime('%Y-%m-%d')
        else:
            title = 'Future'
        if title != previous_title:
            previous_title = title
            buff = get_console_size()[1] - len(title)
            print('\x1b[48;5;0m{}{}\x1b[0m'.format(title, ' '*buff))
        print(t.compose_line(color, trimmings))
