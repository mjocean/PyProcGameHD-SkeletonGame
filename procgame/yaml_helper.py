import yaml

def value_for_key(data, keypath, default=None, exception_on_miss=False):
    """Returns the value at the given *keypath* within :attr:`values`.
    
    A key path is a list of components delimited by dots (periods).  The components are interpreted
    as dictionary keys within the structure.
    For example, the key path ``'a.b'`` would yield ``'c'`` with the following :attr:`values` dictionary: ::
    
        {'a':{'b':'c'}}
    
    If the key path does not exist *default* will be returned.
    """
    v = data
    for component in keypath.split('.'):
        if v != None and hasattr(v,'has_key') and v.has_key(component):
            v = v[component]
        else:
            if(exception_on_miss):
                raise KeyError, "Could not locate required tag: '%s'" % component
            v = default
    return v

