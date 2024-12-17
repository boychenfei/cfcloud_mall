import threading
from collections import UserDict


class ThreadSafeDict(UserDict):
    def __init__(self, init_dict=None, /, **kwargs):
        super().__init__(init_dict, **kwargs)
        self._lock = threading.RLock()

    def __len__(self):
        with self._lock:
            return super().__len__()

    def __iter__(self):
        with self._lock:
            return super().__iter__()

    def __getitem__(self, key):
        with self._lock:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        with self._lock:
            return super().__setitem__(key, value)

    def __delitem__(self, key):
        with self._lock:
            return super().__delitem__(key)

    def __or__(self, other):
        with self._lock:
            return super().__or__(other)

    def __ror__(self, other):
        with self._lock:
            return super().__ror__(other)

    def __ior__(self, other):
        with self._lock:
            return super().__ior__(other)

    def pop(self, key, *args):
        with self._lock:
            return self.data.pop(key, *args)

    def clear(self):
        with self._lock:
            return self.data.clear()

    def setdefault(self, key, default=None):
        with self._lock:
            return self.data.setdefault(key, default)

    def popitem(self):
        with self._lock:
            return self.data.popitem()

    def keys(self):
        with self._lock:
            return self.data.keys()

    def values(self):
        with self._lock:
            return self.data.values()

    def get(self, key, default=None):
        with self._lock:
            return super().get(key, default)

    def __contains__(self, key):
        with self._lock:
            return super().__contains__(key)

    def copy(self):
        with self._lock:
            return super().copy()

    def fromkeys(self, iterable, value=None):
        with self._lock:
            return super().fromkeys(iterable, value)

    def __repr__(self):
        with self._lock:
            return self.data.__repr__()

    def __str__(self):
        with self._lock:
            return self.data.__str__()

    def compute(self, key, func):
        with self._lock:
            old_val = self.data.get(key)
            new_val = func(key, old_val)
            if new_val:
                self.data[key] = new_val
                return new_val
            else:
                if old_val:
                    del self.data[key]
                return None

    def compute_if_absent(self, key, func):
        with self._lock:
            old_val = self.data.get(key)
            if not old_val:
                new_val = func()
                if new_val:
                    self.data[key] = new_val
                    return new_val
            return old_val








