#!/usr/bin/env python

def html_escape(string):
    string = string.replace("&", "&amp;")
    string = string.replace("<", "&lt;")
    string = string.replace(">", "&gt;")
    return string

class escape_html_meta(type):
    """Metaclass that wraps method to html_escape string arguments."""
    def __new__(cls, name, bases, dict):
        def wrap(method):
            def wrapped(*args, **kwargs):
                escaped_args = []
                for arg in args:
                    if isinstance(arg, types.StringTypes):
                        arg = html_escape(arg)
                    escaped_args.append(arg)
                escaped_kwargs = {}
                for key, value in kwargs.items():
                    if isinstance(arg, types.StringTypes):
                        value = html_escape(value)
                    escaped_kwargs[key] = value
                return method(*escaped_args, **escaped_kwargs)
            return wrapped

        for (method_name, method) in dict.items():
            if not isinstance(method, types.FunctionType):
                continue
            dict[method_name] = wrap(method)

        return super(escape_html_meta, cls).__new__(cls, name, bases, dict)
