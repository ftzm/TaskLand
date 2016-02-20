#!/usr/bin/python
"""functions for reading and writing config file"""
import os


def dict2lines(fromdict):
    """return dictionary as list of 'key=value' strings"""
    return ["{}={}\n".format(k, v) for k, v in fromdict.items()]


def write_config(config, defaults):
    """write a config file from the defaults"""
    with open(config, "w+") as f:
        f.writelines(dict2lines(defaults))


def parse(lines, sets_dict):
    """parse list of lines into dictionary if the fields match"""
    for line in lines:
        try:
            key, value = line.split("=", 1)
        except:
            continue
        if key in list(sets_dict.keys()) and value is not None:
            sets_dict[key] = value.rstrip('\n')
    return sets_dict


def process_config(location, defaults):
    """open config file and read contents, or create one with defaults"""
    config = os.path.join(location, "config.rc")
    try:
        with open(config, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        write_config(config, defaults)
        lines = dict2lines(defaults)
    settings = parse(lines, defaults)
    return settings
