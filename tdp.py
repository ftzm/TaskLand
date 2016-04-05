#!/usr/bin/python

"""
File: tdp.py
Author: Matthew Fitzsimmons
Email: fitz.matt.d@gmail.com
Github: https://github.com/ftzm
Description: cli todolist program
"""


import sys
import os
import collections
import datetime
import config
import parse
import views
import actions
import utils

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


defaults = {
    'list_location': 'todo.txt',
    'default_command': 'h',
    'default_view': 'hide o p_id c_id',
    'archive_location': 'archive.txt',
    'archive_automatically': 'true',
    'archive_delay': '2'
    }

settings = config.process_config(__location__, defaults)


def open_list():
    """open and read the task list file"""
    try:
        with open(settings['list_location'], 'r') as f:
            file = f.readlines()
    except FileNotFoundError:
        with open(settings['list_location'], 'w+') as f:
            file = f.readlines()
    return file


def print_projects():
    """print all projects represented in the task list"""
    tasks = collect_tasks()
    print('\n'.join(utils.projects_get(tasks)))


def print_contexts():
    """print all contexts represented in the task list"""
    tasks = collect_tasks()
    print('\n'.join(utils.contexts_get(tasks)))


def collect_tasks():
    """parse task list file into task objects, order, and return in a list"""
    todolist = open_list()
    tasks = [parse.Task(l) for l in sorted(todolist)]

    # archive tasks that are too old
    if settings['archive_automatically'] == 'true':
        delay = datetime.timedelta(int(settings['archive_delay']))
        tasks = archive_done(tasks, delay)
        write_tasks(tasks)

    # sort finished tasks to the bottom
    unfinished, finished = [], []
    for t in tasks:
        (unfinished, finished)[t.x == 'x'].append(t)
    tasks = unfinished

    taskbins = []
    taskbin = []
    prev = None
    for t in tasks:
        if t.due == prev:
            taskbin.append(t)
        else:
            prev = t.due
            taskbins.append(sorted(taskbin, key=lambda x: x.order if x.order
                                   else 9**9))
            taskbin = [t]
    taskbins.append(sorted(taskbin, key=lambda x: x.order if x.order
                           else 9**9))
    tasks = [t for b in taskbins for t in b]
    tasks += finished

    for i, t in enumerate(tasks):
        t.num = i+1

    return tasks


def write_tasks(tasks):
    """write the list of task objects to the task list file"""
    lines = [t.compose_line(False, ['n'], i+1) for i, t in enumerate(tasks)]
    with open(settings['list_location'], "w") as f:
        for line in lines:
            f.write(line + '\n')


def archive_done(tasks, delay):
    """remove tasks marked done from the task list and write to archive file"""
    to_go = [t for t in tasks if t.done and datetime.date.today() >=
             t.done + datetime.timedelta(delay)]
    to_stay = [t for t in tasks if t not in to_go]
    to_go_lines = [t.compose_line(False, ['n']) for t in to_go]
    with open(settings['archive_location'], "a") as f:
        for line in to_go_lines:
            f.write(line + '\n')
    return to_stay


def archive_all(tasks):
    tasks = archive_done(tasks, 0)
    return tasks


def shellmode(args):
    while True:
        handle_view_commands(args)
        commands = input("Input Command: ")
        if commands == '':
            print("Shell mode exited")
            break
        else:
            handle_action_commands(commands.split(' '))

view_commands = collections.OrderedDict([
    ('bc', (views.view_by_context, False)),
    ('bp', (views.view_by_project, False)),
    ('vc', (views.filter_contexts, True)),
    ('vp', (views.filter_projects, True)),
    ('any', (views.filter_include_any, True)),
    ('all', (views.filter_include_all, True)),
    ('excl', (views.filter_exclude, True)),
    ('next', (views.view_next, False)),
    ('today', (views.view_today, False)),
    ('week', (views.view_week, False)),
    ('until', (views.view_until_cli, True)),
    ('reverse', (views.view_reversed, False)),
    ('hide', ('hide', True)),
    ('nocolor', ('nocolor', False)),
    ('nest', (views.nest, False)),
    ('h', (views.date_headers, False)),
    ])

action_commands = collections.OrderedDict([
    ('add', (actions.add, True)),  # 'a' has numbers for show atm
    ('edit', (actions.edit, False)),
    ('rm', (actions.remove, False)),
    ('do', (actions.complete, False)),
    ('undo', (actions.undo, False)),
    ('sc', (actions.schedule, True)),
    ('usc', (actions.unschedule, False)),
    ('pr', (actions.prioritize, True)),
    ('upr', (actions.unprioritize, False)),
    ('c', (actions.set_context, True)),
    ('uc', (actions.unset_context, True)),
    ('p', (actions.set_project, True)),
    ('up', (actions.unset_project, True)),
    ('sub', (actions.child_set, True)),
    ('usub', (actions.child_unset, False)),
    ('con', (actions.contract, False)),
    ('exp', (actions.expand, False)),
    ('fut', (actions.future_set, False)),
    ('setabove', (actions.order_before, True)),
    ('setbelow', (actions.order_after, True)),
    ('rep', (actions.repeat_set, True)),
    ('urep', (actions.repeat_unset, False)),
    ])

general_commands = collections.OrderedDict([
    ('catch', (actions.catch)),
    ('archive', (archive_all)),
    ])


def assemble_view_command_list(args):
    """
    parse list of command line args into list of tuples where the first element
    is a task-list command and the second is a list of its arguments
    """
    # bring in default view commands in config
    args += settings['default_view'].split(',')

    command_list = []
    while args:
        arg = args.pop(0)
        try:
            _, takes_arg = view_commands[arg]
            if takes_arg:
                command_arg = args.pop(0)
            else:
                command_arg = None
            command_list.append((arg, [command_arg]))
        except KeyError:
            sys.exit("{} is not a command."
                     "Is a previous command missing an argument?".format(arg))
    command_list.sort(key=lambda x: list(view_commands.keys()).index(x[0]))
    return command_list


def execute_view_command_list(command_list):
    """executes functions corresponding to view commands"""
    # bring in default view commands
    # establish print method
    print_command = views.normal_print
    color = True
    exclusions = []
    i = 0
    x = len(command_list)
    while i < x:
        if command_list[i][0] in ['h', 'nest']:
            # print_command = view_commands[command_list.pop(i)[0]]
            print_command = view_commands[command_list.pop(i)[0]][0]
            x -= 1
        elif command_list[i][0] == 'nocolor':
            command_list.pop(i)
            color = False
            x -= 1
        elif command_list[i][0] == 'hide':
            exclusions = exclusions + command_list.pop(i)[1][0].split(' ')
            x -= 1
        else:
            i += 1

    tasks = collect_tasks()

    for command, args in command_list:
        has_args = view_commands[command][1]
        if has_args:
            tasks = view_commands[command][0](tasks, *args)
        else:
            tasks = view_commands[command][0](tasks)

    print_command(tasks, color, exclusions)


def handle_view_commands(args):
    """
    command coordinating collecting, verifying and executing view commands
    """
    command_list = assemble_view_command_list(args)
    execute_view_command_list(command_list)


def extract_addition(args):
    text = []
    while args:
        arg = args.pop(0)
        if arg != ',':
            text.append(arg)
        else:
            break
    return args, ' '.join(text)


def assemble_action_command_list(args):
    """parses list of cli arg strings into action commands and arguments"""
    command_list = []
    addition = None
    target = None

    # pop first element off as target if is digit
    if args[0].isdigit():
        target = int(args.pop(0)) - 1
        print(target)

    # assemble command list
    while args:
        arg = args.pop(0)
        if arg == "add":
            args, addition = extract_addition(args)
        else:
            try:
                _, takes_arg = action_commands[arg]
                if takes_arg:
                    try:
                        command_arg = args.pop(0)
                    except IndexError:
                        sys.exit("Error: command '{}' takes an argument"
                                 .format(arg))
                else:
                    command_arg = None
                command_list.append((arg, [command_arg]))
            except KeyError:
                command_list[-1][1].append(arg)

    # verify number of arguments, extract target if applicable
    for command, args in command_list:
        if len(args) != action_commands[command][1]:
            if target is None and addition is None and args[0].isdigit():
                target = int(args.pop(0)) - 1
            if len(args) != action_commands[command][1]:
                sys.exit("Error: command '{}' has too many arguments: {}"
                         .format(command, ', '.join(args)))

    return command_list, addition, target


def execute_action_command_list(command_list, target, lines):
    """executes the commands in a command list with args, returns result"""
    for command, args in command_list:
        has_args = action_commands[command][1]
        if not has_args:
            lines = action_commands[command][0](lines, target)
        else:
            lines = action_commands[command][0](lines, target, *args)
    return lines


def handle_action_commands(args):
    """coordinates receiving, parsing, executing action commands"""
    tasks = collect_tasks()
    command_list, addition, target = assemble_action_command_list(args)

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
            tasks = actions.add(tasks, addition)
            target = len(tasks) - 1

    # return if target None or if int out of range
    if target is None:
        print("Error: No target specified")
        return
    elif target > len(tasks):
        print("Error: task number supplied is {}, but only"
              " {} tasks in list".format(target, len(tasks)))
        return

    tasks = execute_action_command_list(command_list, target, tasks)
    write_tasks(tasks)


def handle_general_commands(arg):
    """coordinate collecting tasks, executing the command, and writing tasks"""
    tasks = collect_tasks()
    tasks = general_commands[arg](tasks)
    write_tasks(tasks)


def main(args):
    if len(args) == 0:
        args = settings['default_command'].split(' ')
    if args[0] in view_commands.keys():
        handle_view_commands(args)
    elif args[0] in action_commands.keys() or args[0].isdigit():
        handle_action_commands(args)
    elif args[0] in general_commands.keys():
        handle_general_commands(args[0])
    elif args[0] == 'pp':
        print_projects()
    elif args[0] == 'pc':
        print_contexts()
    elif args[0] == 'shell':
        shellmode(args[1:])
    else:
        print('Error: {} is not a valid command'.format(args[0]))


if __name__ == "__main__":  # why do I use this
    main(sys.argv[1:])
