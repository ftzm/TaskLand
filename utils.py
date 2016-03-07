#!/usr/bin/python
import datetime
import re


weekdays = ['m', 't', 'w', 'r', 'f', 's', 'u']


def projects_get(tasks):
    return sorted({p for t in tasks for p in t.projects},
                  key=lambda s: s.lower())


def contexts_get(tasks):
    return sorted({p for t in tasks for p in t.contexts},
                  key=lambda s: s.lower())


def weekday_to_datetime(s):
    daynum = weekdays.index(s)
    offset = daynum - int(datetime.date.today().weekday())
    if offset < 1:
        offset += 7
    date = datetime.date.today() + datetime.timedelta(offset)
    return date


def date_to_datetime(s):
    date = None
    td = datetime.date.today()
    td = [td.year, td.month, td.day]
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if td[0] % 4 == 0:
        month_lengths[1] = 29
    if re.match('\d{1,2}$', s):
        year, month, day = None, None, int(s)
    elif re.match('\d{1,2}-\d{1,2}$', s):
        year, month, day = None, tuple([int(i) for i in s.split('-')])
    elif re.match('\d{4}-\d{1,2}-\d{1,2}$', s):
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
        date = datetime.datoday()
    elif s[0].isdigit():
        date = date_to_datetime(s)
    else:
        print('Error: Not a valid date format')
    return date
