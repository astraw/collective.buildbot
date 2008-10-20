# -*- coding: utf-8 -*-


class Registry(object):
    """Registry to run callable.
    """
    
    def __init__(self):
        self.klass = dict()
        self.called = list()
        self.running = list()
        self.order = []

    def add(self, name, item):
        self.order.append(name)
        self.klass[name] = item

    def run(self, name, *args, **kwargs):
        """Call a value called name.
        """
        if name in self.called:
            return
        if name in self.running:
            raise ValueError, "loops have been detected"
        self.running.append(name)
        self.klass[name](*args, **kwargs)
        self.running.remove(name)
        self.called.append(name)

    def runned(self, name, *args, **kwargs):
        """Return a called value.
        """
        if not name in self.called:
            self.run(name, *args, **kwargs)
        return self.klass[name]

    def everyone(self, *args, **kwargs):
        """Call everyone, in ``add`` order.
        """
        order = [m for i, m in enumerate(self.order) if m not in self.order[:i]]
        for name in order:
            self.run(name, *args, **kwargs)



def split_option(options, key, splitter='\n'):
    value = options.get(key, '')
    value = value.strip()
    if splitter not in value:
        return value and [value] or []
    value = value.split(splitter)
    return [v.strip() for v in value if v.strip()]

