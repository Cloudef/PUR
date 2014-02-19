#!/usr/bin/env python3
# pylint: disable=line-too-long
'''module for replacing stuff mainly using regex'''

import re
LINKPROTOS = 'https?|ftps?|mailto|ssh|git|hg|bzr|file'
LINKREX = re.compile(r'((({}):\/\/|www\..*\.)[-/.\?=&%()#@~:\w]+)'.format(LINKPROTOS))

# additional bitflag to iter_replace_* functions
# replaces whole string on first match and returns
RA = 1<<42

# CORE

def replace_range(data, start, end, value):
    '''replace range in string with value'''
    return '{}{}{}'.format(data[:start], value, data[end:])

def iter_replace_compiled(rex, data, callback, flags=0):
    '''iterate and replace stuff using compiled regex'''
    offset = 0
    old_data = data
    for expr in rex.finditer(data, flags & ~RA):
        if flags & RA: # replace all and break
            data = callback(expr, 0, len(data), data)
            break
        data = callback(expr, expr.start() + offset, expr.end() + offset, data)
        offset = len(data) - len(old_data)
    return data

def iter_replace(rex, data, callback, flags=0):
    '''iterate and replace stuff using regex'''
    offset = 0
    old_data = data
    for expr in re.finditer(rex, data, flags & ~RA):
        if flags & RA: # replace all and break
            data = callback(expr, 0, len(data), data)
            break
        data = callback(expr, expr.start() + offset, expr.end() + offset, data)
        offset = len(data) - len(old_data)
    return data

def html_unescape(data):
    '''unescape html'''
    try:
        import html
        # pylint: disable=no-member
        data = html.unescape(data)
    except (ImportError, AttributeError):
        from html.parser import HTMLParser
        data = HTMLParser().unescape(data)
    return data

def html_escape(data):
    '''escape html'''
    try:
        import html
        data = html.escape(data)
    except (ImportError, AttributeError):
        import cgi
        data = cgi.escape(data)
    return data

def html_link(url, name=None):
    '''create html link'''
    return '<a href="{}">{}</a>'.format(url, name if name else url)

def html_linkify_and_escape(data, replace_all=False):
    '''escape html data and turn links to html links'''
    return iter_replace_compiled(LINKREX, html_escape(data), replace_link, RA if replace_all else 0)

def syntax(code, lang=None):
    '''syntax highlight code if possible'''
    try:
        # pylint: disable=no-name-in-module
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import TextLexer, get_all_lexers
    except ImportError:
        return '<div class="pygments"><pre>{}</pre></div>'.format(code)

    scode = html_unescape(code)
    lexer = None
    if lang:
        lang = lang.strip().lower()
        for itr in get_all_lexers():
            if lang in itr[1]:
                module = '{}Lexer'.format(itr[0])
                lexer = getattr(__import__("pygments.lexers", fromlist=[module]), module)(stripall=True)
                break
    if not lexer:
        lexer = TextLexer(stripall=True)
    return '<div class="pygments">{}</div>'.format(highlight(scode, lexer, HtmlFormatter(linenos='table')))

# ready HTML callbacks

def replace_link(expr, start, end, data):
    '''replace link found by iter_callback'''
    value = expr.group(0)
    return replace_range(data, start, end, '<a href="{}" target="_blank">{}</a>'.format(value, value))

def replace_block(expr, start, end, data):
    '''replace block found by iter_callback'''
    value = expr.group(1)
    return replace_range(data, start, end, '<div class="block">{}</div>'.format(value))

def replace_strike(expr, start, end, data):
    '''replace strike found by iter_callback'''
    value = expr.group(1)
    return replace_range(data, start, end, '<del>{}</del>'.format(value))

def replace_strong(expr, start, end, data):
    '''replace strong found by iter_callback'''
    value = expr.group(1)
    return replace_range(data, start, end, '<strong>{}</strong>'.format(value))

def replace_italic(expr, start, end, data):
    '''replace italic found by iter_callback'''
    value = expr.group(1)
    return replace_range(data, start, end, '<i>{}</i>'.format(value))

def replace_code(expr, start, end, data):
    '''replace code block found by iter_callback'''
    lang = expr.group(1)
    code = expr.group(2)
    return replace_range(data, start, end, '{}'.format(syntax(code, lang)))

# vim: set ts=8 sw=4 tw=0 :
