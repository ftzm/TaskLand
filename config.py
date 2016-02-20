#!/usr/bin/python
import os

defaults = {
        'list_location': 'todo.txt',
        'default_command': 'h',
        'archive_location': 'archive.txt',
        }

def dict2lines(d):
    """return dictionary as list of 'key=value' strings"""
    return ["{}={}".format(k, v) for k, v in d.items()]

def write_config(f):
    f.writelines(dict2lines(defaults))

def parse(lines, d):
    for l in lines:
        try:
            k, v = l.split("=", 1)
        except:
            continue
        if k in list(d.keys()) and v is not None:
            d[k] = v
    return d

def process_config():
    """open config file and read contents, or create one with defaults"""
    with open(os.path.join(__location__, "config.rc"), "r+") as f:
        lines = f.readlines()
        if len(lines) == 0:
            write_config(f)
            lines = dict2lines(defaults)
        settings = parse(lines)
    return settings
