
import tempfile
import os
import re
import pickle

pjoin = os.path.join


class NoDefault:
    pass


class DiskCache:
    def __init__(self, cache_id):
        if not re.match("^[a-zA-Z0-9-_]+$", cache_id):
            raise ValueError("Invalid cache id: {}".format(cache_id))

        self.cache_dir = pjoin(tempfile.gettempdir(), cache_id)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

    def _get_path_for_key(self, key):
        return pjoin(self.cache_dir, key)

    def haskey(self, key):
        try:
            return os.path.getsize(self._get_path_for_key(key)) > 0
        except FileNotFoundError:
            return False

    def get(self, key, default=None):
        if self.haskey(key):
            with open(self._get_path_for_key(key), "rb") as infile:
                retval = pickle.load(infile)
        else:
            return default

        return retval

    def set(self, key, value):
        with open(self._get_path_for_key(key), "wb") as outfile:
            pickle.dump(value, outfile)

    def keys(self):
        for item in os.listdir(self.cache_dir):
            yield item

    def values(self):
        for key in self.keys():
            yield self[key]

    def clear(self):
        for key in list(self.keys()):
            del self[key]

    def remove(self, key):
        if key not in self:
            raise KeyError(key)
        os.unlink(self._get_path_for_key(key))

    def __getitem__(self, key):
        nodefault = NoDefault()
        retval = self.get(key, nodefault)
        if retval is nodefault:
            raise KeyError(key)
        return retval

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        self.remove(key)

    def __contains__(self, key):
        return self.haskey(key)
