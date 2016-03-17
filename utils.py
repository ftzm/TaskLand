#!/usr/bin/python
"""general utility functions that don't fit thematically elsewhere"""
import datetime
import re


weekdays = ['m', 't', 'w', 'r', 'f', 's', 'u']


def projects_get(tasks):
    """return list of all projects in list"""
    return sorted({p for t in tasks for p in t.projects},
                  key=lambda s: s.lower())


def contexts_get(tasks):
    """return list of all contexts in list"""
    return sorted({p for t in tasks for p in t.contexts},
                  key=lambda s: s.lower())


def weekday_to_datetime(string):
    """convert a weekday code to datetime object"""
    daynum = weekdays.index(string)
    offset = daynum - int(datetime.date.today().weekday())
    if offset < 1:
        offset += 7
    date = datetime.date.today() + datetime.timedelta(offset)
    return date


def date_to_datetime(s):
    """converts to datetime a string in various formats"""
    date = None
    td = datetime.date.today()
    td = [td.year, td.month, td.day]
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if td[0] % 4 == 0:
        month_lengths[1] = 29
    if re.match('\d{1,2}$', s):
        year, month, day = None, None, int(s)
    elif re.match(r'\d{1,2}-\d{1,2}$', s):
        year, month, day = None, tuple([int(i) for i in s.split('-')])
    elif re.match(r'\d{4}-\d{1,2}-\d{1,2}$', s):
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
    elif s[0] == 'n':
        date = datetime.date.today()
    elif s[0].isdigit():
        date = date_to_datetime(s)
    else:
        print('Error: Not a valid date format')
    return date


def colorize(string, color):
    colors = {
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 13,
        'cyan': 6,
        'orange': 9,
        'gray': 10,
        'white': 14,
        }
    return '\x1b[38;5;{}m{}\x1b[0m'.format(colors[color], string)


def string_to_datetime(string):
    """convert dd-mm-yyyy string to datetime"""
    return datetime.date(*map(int, string.split('-')))
