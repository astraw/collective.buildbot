# -*- coding: utf-8 -*-

def split_option(options, key, splitter='\n'):
    value = options.get(key, '')
    value = value.strip()
    if splitter not in value:
        return value and [value] or []
    value = value.split(splitter)
    return [v.strip() for v in value if v.strip()]

