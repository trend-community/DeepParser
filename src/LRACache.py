import collections

#Reference: https://docs.python.org/3/reference/datamodel.html?emulating-container-types#emulating-container-types
# https://stackoverflow.com/questions/3387691/how-to-perfectly-override-a-dict

class LRACache(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""
    def setlimit(self, limit):
        self.limit = limit

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        self.limit = 0

    def __getitem__(self, key):
        #//TODO: add weight to this key, or put it to the latest order.
        return self.store[key]

    def __setitem__(self, key, value):
        if 0 <  self.limit <= len(self.store)  :
            pass    #//TODO: delete last not used limit
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)
if __name__ == "__main__":
    mycache = LRACache()
    mycache["great"] = 1
    mycache['good'] = 3


