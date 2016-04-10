#!/usr/bin/python

"""
File: taskland.py
Author: Matthew Fitzsimmons
Email: fitz.matt.d@gmail.com
Github: https://github.com/ftzm
Description: cli todolist program
"""


import sys
import os
import time
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
    'default_view': 'hide o p_id c_id a',
    'archive_location': 'archive.txt',
    'archive_automatically': 'false',
    'archive_delay': '2'
    }

settings = config.process_config(__location__, defaults)


def open_list():
    """open and read the task list file"""
    list_location = os.path.dirname(__file__) + "/" + settings['list_location']
    try:
        with open(list_location, 'r') as f:
            file = f.readlines()
    except FileNotFoundError:
        with open(list_location, 'w+') as f:
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
    tasks = [parse.Task(l) for l in todolist]

    # archive tasks that are too old
    if settings['archive_automatically'] == 'true':
        delay = int(settings['archive_delay'])
        tasks = archive_done(tasks, delay)
        write_tasks(tasks)

    tasks = sorted(tasks, key=lambda t: t.order if t.order else 9**9)
    tasks = sorted(tasks, key=lambda t: t.priority if t.priority else 'Z')
    tasks = sorted(tasks, key=lambda t: t.due if t.due else
                   datetime.date(3000, 1, 1))
    tasks = sorted(tasks, key=lambda t: t.done if t.done else
                   datetime.date(1, 1, 1))

    for i, t in enumerate(tasks):
        t.num = i+1

    return tasks


def add_warning(*_):
    print("Error: 'add' must be the first command")
    raise KeyError


def write_tasks(tasks):
    """write the list of task objects to the task list file"""
    list_location = os.path.dirname(__file__) + "/" + settings['list_location']
    lines = [t.compose_line(False, ['n'], i+1) for i, t in enumerate(tasks)]
    with open(list_location, "w") as f:
        for line in lines:
            f.write(line + '\n')


def archive_done(tasks, delay):
    """remove tasks marked done from the task list and write to archive file"""
    archive_location = os.path.dirname(__file__) + "/" + settings['archive_location']
    to_go = [t for t in tasks if t.done and datetime.date.today() >=
             t.done + datetime.timedelta(delay)]
    to_stay = [t for t in tasks if t not in to_go]
    to_go_lines = [t.compose_line(False, ['n']) for t in to_go]
    with open(archive_location, "a") as f:
        for line in to_go_lines:
            f.write(line + '\n')
    return to_stay


def archive_all(tasks):
    tasks = archive_done(tasks, 0)
    return tasks


def shellmode(args):
    while True:
        try:
            os.system('clear')
            handle_view_commands(args[:])
            commands = input("Input Command: ")
            if commands == '':
                print("Shell mode exited")
                break
            else:
                handle_action_commands(commands.split(' '))
        except:
            time.sleep(1)
            continue

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
    ('add', (add_warning, True)),
    ('edit', (actions.edit, False)),
    ('undo', (actions.undo, False)),
    ('sc', (actions.schedule, True)),
    ('usc', (actions.unschedule, False)),
    ('pr', (actions.prioritize, True)),
    ('upr', (actions.unprioritize, False)),
    ('c', (actions.set_context, True)),
    ('uc', (actions.unset_context, False)),
    ('ucn', (actions.unset_context, True)),
    ('p', (actions.set_project, True)),
    ('up', (actions.unset_project, False)),
    ('upn', (actions.unset_project, True)),
    ('sub', (actions.child_set, True)),
    ('usub', (actions.child_unset, False)),
    ('con', (actions.contract, False)),
    ('exp', (actions.expand, False)),
    ('rep', (actions.repeat_set, True)),
    ('urep', (actions.repeat_unset, False)),
    ('do', (actions.complete, False)),
    ('setabove', (actions.order_before, True)),
    ('setbelow', (actions.order_after, True)),
    ('rm', (actions.remove, False)),
    ])

general_commands = collections.OrderedDict([
    ('catch', (actions.catch)),
    ('archive', (archive_all)),
    ])


def make_command_list(args, commands):
    command_list = []
    while args:
        arg = args.pop(0)
        try:
            _, takes_arg = commands[arg]
            if takes_arg:
                try:
                    command_arg = [args.pop(0)]
                except IndexError:
                    print("Error: '{}' is missing an argument".format(arg))
                    raise
            else:
                command_arg = []
            command_list.append((arg, command_arg))
        except KeyError:
            print("Error: {} is not a command.".format(arg))
            raise
    command_list.sort(key=lambda x: list(commands.keys()).index(x[0]))
    return command_list


def execute_command_list(tasks, command_list, commands):
    for command, args in command_list:
        if args:
            tasks = commands[command][0](tasks, *args)
        else:
            tasks = commands[command][0](tasks)
    return tasks


def execute_view_command_list(command_list):
    """executes functions corresponding to view commands"""
    print_command = views.normal_print
    color = True
    exclusions = []
    i = 0
    x = len(command_list)
    while i < x:
        if command_list[i][0] in ['h', 'nest']:
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
    tasks = execute_command_list(tasks, command_list, view_commands)
    print_command(tasks, color, exclusions)


def handle_view_commands(args):
    """
    command coordinating collecting and executing view commands
    """
    args += settings['default_view'].split(',')
    command_list = make_command_list(args, view_commands)
    execute_view_command_list(command_list)


def extract_addition(args):
    text = []
    while args:
        arg = args.pop(0)
        if arg != ',':
            text.append(arg)
        else:
            break
    if not text:
        print("Error: new task must contain text")
        raise
    else:
        return args, ' '.join(text)


def extract_target(args):
    target = None
    i = 0
    while i < len(args):
        if args[i].isdigit():
            target = int(args.pop(i)) - 1
            break
        else:
            i += 1
    return args, target


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
    addition = None

    #  grab addition if exists
    if args[0] == 'add':
        args.pop(0)
        args, addition = extract_addition(args)
        target = len(tasks)
    # or pop first element off as target if is digit
    elif args[0].isdigit():
        target = int(args.pop(0)) - 1
    # if the first arg is neither a target nor "add", the next int
    # has to be the target
    else:
        args, target = extract_target(args)

    command_list = make_command_list(args, action_commands)

    # add the target into the arg list of every command
    if target is not None:
        for _, args in command_list:
            args.insert(0, target)
    else:
        print('Error: you must specify a target')

    # if addition, add task so other commands can act upon it
    if addition:
        tasks = actions.add(tasks, addition)

    try:
        tasks = execute_command_list(tasks, command_list, action_commands)
    except IndexError:
        print("Error: task number is invalid")
        raise

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
        try:
            handle_view_commands(args)
        except:
            sys.exit()
    elif args[0] in action_commands.keys() or args[0].isdigit():
        try:
            handle_action_commands(args)
        except:
            sys.exit()
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
