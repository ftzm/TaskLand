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
    'archive_location': 'archive.txt',
    }

settings = config.process_config(__location__, defaults)


def open_file():
    try:
        with open(settings['list_location'], 'r') as f:
            file = f.readlines()
    except FileNotFoundError:
        with open(settings['list_location'], 'w+') as f:
            file = f.readlines()
    return file

todolist = open_file()


def print_projects():
    tasks = collect_tasks()
    print('\n'.join(utils.projects_get(tasks)))


def print_contexts():
    tasks = collect_tasks()
    print('\n'.join(utils.contexts_get(tasks)))


def collect_tasks():
    tasks = [parse.Task(l) for l in sorted(todolist)]
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
    for i, t in enumerate(tasks):
        t.num = i+1
    return tasks


def write_tasks(tasks):
    lines = [t.compose_line(False, ['n'], i+1) for i, t in enumerate(tasks)]
    with open(settings['list_location'], "w") as f:
        for line in lines:
            f.write(line + '\n')


def archive_done(tasks):
    to_go = [t for t in tasks if t.done is not None]
    to_stay = [t for t in tasks if t not in to_go]
    to_go_lines = [t.compose_line(False, ['n']) for t in to_go]
    with open(settings['archive_location'], "a") as f:
        for line in to_go_lines:
            f.write(line + '\n')
    return to_stay


view_commands = collections.OrderedDict([
    ('bc', (views.view_by_context, 0, 0)),
    ('bp', (views.view_by_project, 0, 0)),
    ('vc', (views.filter_contexts, 1, 9)),
    ('vp', (views.filter_projects, 1, 9)),
    ('any', (views.filter_include_all, 1, 9)),
    ('all', (views.filter_include_any, 1, 9)),
    ('excl', (views.filter_exclude, 1, 9)),
    ('today', (views.view_today, 0, 0)),
    ('week', (views.view_week, 0, 0)),
    ('until', (views.view_until_cli, 1, 1)),
    ('trim', ('trim', 1, 9)),
    ('nocolor', ('nocolor', 0, 0)),
    ('nest', (views.nest, 0, 0)),
    ('h', (views.date_headers, 0, 0)),
    ])

action_commands = collections.OrderedDict([
    ('a', (actions.add, 1, 100)),  # 'a' has numbers for show atm
    ('ed', (actions.edit, 0, 0)),
    ('rm', (actions.remove, 0, 0)),
    ('do', (actions.complete, 0, 0)),
    ('undo', (actions.undo, 0, 0)),
    ('sc', (actions.schedule, 1, 1)),
    ('usc', (actions.unschedule, 0, 0)),
    ('pr', (actions.prioritize, 1, 1)),
    ('upr', (actions.unprioritize, 0, 0)),
    ('c', (actions.set_context, 1, 9)),
    ('uc', (actions.unset_context, 1, 1)),
    ('p', (actions.set_project, 1, 9)),
    ('up', (actions.unset_project, 1, 1)),
    ('sub', (actions.child_set, 1, 1)),
    ('usub', (actions.child_unset, 0, 0)),
    ('cn', (actions.contract, 0, 0)),
    ('ex', (actions.expand, 0, 0)),
    ('fut', (actions.future_set, 0, 0)),
    ('setabove', (actions.order_before, 1, 1)),
    ('setbelow', (actions.order_after, 1, 1)),
    ('rep', (actions.repeat_set, 1, 1)),
    ('ure', (actions.repeat_unset, 0, 0)),
    ])

general_commands = collections.OrderedDict([
    ('catch', (actions.catch)),
    ('archive', (archive_done)),
    ])


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


def execute_view_command_list(command_list):
    """executes functions corresponding to view commands"""
    # establish print method
    print_command = views.normal_print
    color = True
    exlusions = []
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
        elif command_list[i][0] == 'trim':
            exlusions = command_list.pop(i)[1]
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

    print_command(tasks, color, exlusions)


def handle_view_commands(args):
    command_list = assemble_view_command_list(args)
    if verify_command_list(command_list, view_commands, view_commands):
        execute_view_command_list(command_list)


def assemble_action_command_list(args):
    """parses list of strings into action commands and arguments"""
    command_list = []
    task_text = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == ',':
            task_text = False
        elif task_text is False and arg in list(action_commands.keys()):
            command_list.append((arg, []))
            task_text = arg == 'a'
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
        target = int(command_list[0][1][0]) - 1
        command_list[0][1].pop(0)
    return command_list, target


def verify_command_list(command_list, command_index, action_msg=False):
    """check that list of commands is valid"""
    if action_msg:
        action_text = ", in addition to the target"
    else:
        action_text = ""
    for command_args in command_list:
        command, args = command_args
        minimum = command_index[command][1]
        maximum = command_index[command][2]
        if len(args) < minimum:
            if minimum != maximum:
                print("Error: '{}' takes at least {} argument{pl} "
                      "{}".format(command, minimum, action_text,
                                  pl='' if minimum == 1 else 's'))
            else:
                print("Error: '{}' takes {} argument{pl}"
                      "{}".format(command, minimum, action_text,
                                  pl='' if minimum == 1 else 's'))
            return False
        elif len(args) > maximum:
            surplus = args[maximum]
            if minimum != maximum:
                print("Error: '{}' takes at most {} argument{pl}"
                      "{}, and '{}' is not a "
                      "command".format(
                          command, maximum, surplus, action_text,
                          pl='' if maximum == 1 else 's'))
            else:
                print("Error: '{}' takes {} argument{pl}"
                      "{}, and '{}' is not a command".format(
                          command, maximum, action_text, surplus,
                          pl='' if maximum == 1 else 's'))
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
    i = 0
    target = None
    while i < len(args):
        if args[i].isdigit():
            target = int(args.pop(i)) - 1
        i += 1
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
    """coordinates receiving, parsing, executing action commands"""
    tasks = collect_tasks()

    # if first arg is an int, extract it as target
    args, target = get_action_target(args)
    # make command list out of args
    command_list = assemble_action_command_list(args)
    # get addition from command list if exists else none
    print(command_list)
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
            tasks = actions.add(tasks, addition)
            target = len(tasks) - 1

    if target is None:
        command_list, target = prepare_single_action(command_list)

    # return if target None or if int out of range
    if target is None:
        print("Error: No target specified")
        return
    elif target > len(tasks):
        print("Error: task number supplied is {}, but only"
              " {} tasks in list".format(target, len(tasks)))
        return

    if verify_command_list(command_list, action_commands, True):
        tasks = execute_action_command_list(command_list, target, tasks)
    write_tasks(tasks)


def handle_general_commands(arg):
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
    else:
        print('Error: {} is not a valid command'.format(args[0]))


if __name__ == "__main__":  # why do I use this
    main(sys.argv[1:])
