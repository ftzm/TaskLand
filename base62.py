#!/usr/bin/python

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(BASE62)


def encode(num, numerals=BASE62):
    """encode a decimal number to base62"""
    if num == 0:
        return numerals[0]
    # add handling for negative numbers. maybe
    result = ''
    while num:
        result = numerals[num % BASE] + result
        num = num // BASE
    return result


def decode(s, numerals=BASE62):
    """decode a base62 number to a decimal"""
    strlen = len(s)
    num = 0
    idx = 0
    for char in s:
        power = strlen - (idx + 1)
        num += numerals.index(char) * BASE ** power
        idx += 1
    return num
