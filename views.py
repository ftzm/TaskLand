#!/usr/bin/python

"""functions for filtering and printing the task list"""

import datetime
import os
import utils


def view_by_project(tasks):
    """return list of tasks sorted by project"""
    return [t for p in utils.projects_get(tasks) for t in tasks
            if p in t.projects]


def view_by_context(tasks):
    """return list of tasks sorted by project"""
    return [t for p in utils.contexts_get(tasks) for t in tasks
            if p in t.contexts]


def filter_contexts(tasks, *strings):
    """return list of tasks whose contexts contain any of supplied strings"""
    return [t for t in tasks if any(s in t.contexts for s in strings)]


def filter_projects(tasks, *strings):
    """return list of tasks whose projects contian any of supplied strings"""
    return [t for t in tasks if any(s in t.projects for s in strings)]


def filter_include_any(tasks, *strings):
    """return list of tasks whose text include any of supplied strings"""
    return [t for t in tasks if any(s in t.text for s in strings)]


def filter_include_all(tasks, *strings):
    """return list of tasks whose text include all of supplied strings"""
    return [t for t in tasks if all(s in t.text for s in strings)]


def filter_exclude(tasks, *strings):
    """return list of tasks whose text include none of supplied strings"""
    return [t for t in tasks if not any(s in t.text for s in strings)]


def view_until(tasks, date):
    """takes datetime object, returns all tasks up to and including date"""
    return [t for t in tasks if t.due and t.due <= date and not t.x]


def view_until_cli(tasks, string):
    """return list of tasks that are due up until the supplied date"""
    date = utils.code_to_datetime(string)
    return view_until(tasks, date)


def view_next(tasks):
    """return the next task in the """
    return [tasks[0]] if tasks else []


def view_today(tasks):
    """return list of tasks that are due up until today"""
    return view_until(tasks, datetime.date.today())


def view_week(tasks):
    """view tasks due within the coming week"""
    return view_until(tasks, datetime.date.today()+datetime.timedelta(7))


def view_reversed(tasks):
    """reverse order of tasks"""
    tasks.reverse()
    return tasks


def normal_print(tasks, color, exclusions):
    """print tasks using basic print method"""
    for t in tasks:
        print(t.compose_line(color, exclusions))


def nest_sort(tasks):
    """sort all children to be under their parents"""
    parent_ids = [t.parent_id for t in tasks if t.parent_id is not None]
    # checks for orphaned children due to invalid list or filtering
    nest_sorted = [t for t in tasks if not t.child_id or
                   t.child_id not in parent_ids]
    remaining = [t for t in tasks if t not in nest_sorted]
    i = 0
    while len(remaining) > 0:
        if nest_sorted[i].parent_id:
            children = [t for t in remaining
                        if t.child_id == nest_sorted[i].parent_id]
            remaining = [t for t in remaining if t not in children]
            nest_sorted = nest_sorted[:i+1] + children + nest_sorted[i+1:]
        i += 1
    return nest_sorted


def nest(tasks, color, trimmings):
    """print tasks in a nested format"""

    tasks = nest_sort(tasks)
    output_lines = []
    hierarchy = []
    closed_id = 0
    latest_parent_id = 0
    for t in tasks:
        orphan = False

        # calc indent level based on degree of nested child tags
        # manage nesting hierarchy
        indents = 0
        if t.child_id is not None:
            if t.child_id not in hierarchy:
                # necessary to check if child is orphan
                if t.child_id == latest_parent_id:
                    hierarchy.append(t.child_id)
                else:
                    hierarchy = []
                    orphan = True
            else:
                hierarchy = hierarchy[:hierarchy.index(t.child_id)+1]
            if not orphan:
                indents = hierarchy.index(t.child_id)+1
        else:
            hierarchy = []

        # closed/open indicator, set switch to hide following tasks
        # set last parent id
        if t.parent_id:
            latest_parent_id = t.parent_id
            if t.contracted:
                closed_id = latest_parent_id
                prefix = '-'
            else:
                prefix = '+'
        else:
            prefix = ' '  # so non-parents stay lined up

        # if the closed_id is in the hierarchy, then the task will be hidden
        if closed_id not in hierarchy:
            line = '   ' * indents + prefix + t.compose_line(color, trimmings)
            output_lines.append(line)

    print('\n'.join(output_lines))


def get_console_size():
    """returns rows and columns as 2 tuple"""
    return [int(i) for i in os.popen('stty size', 'r').read().split()]


def date_headers(tasks, color, trimmings):
    """print lines with date headers"""
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
