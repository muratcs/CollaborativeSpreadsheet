from .spreadsheet import SpreadSheet
import os
import pickle


def Singleton(cls):
    _instances = {}

    def getinstance():
        if cls not in _instances:
            _instances[cls] = cls()
        return _instances[cls]

    return getinstance


@Singleton
class SSPersistency:

    # def __new__(cls, *args, **kwargs):
    #     if hasattr(cls, '_inst'):
    #         return cls._inst
    #     else:
    #         cls._inst = super().__new__(cls, *args, **kwargs)
    #         return cls._inst

    def __init__(self):
        if not os.path.exists("SavedSheets"):
            os.makedirs("SavedSheets")

    def save(self, sid: int):
        s = SpreadSheet._getinstance(sid)
        assert s is not None
        with open("SavedSheets/" + str(sid) + ".pck", 'wb') as ofp:
            p = pickle.Pickler(ofp)
            p.dump(s)

    def load(self, sid: int):
        s = SpreadSheet._getinstance(sid)
        with open("SavedSheets/" + str(sid) + ".pck", 'rb') as ifp:
            p = pickle.Unpickler(ifp)
            loaded = p.load()
        if s is None:
            SpreadSheet.unregister(loaded, loaded._observers)
            SpreadSheet._addinstance(loaded)
        else:
            SpreadSheet.notify(s, "Sheet has been loaded from file")
            obs = s._observers.copy()
            SpreadSheet.unregister(loaded, loaded._observers)
            SpreadSheet.unregister(s, s._observers)
            SpreadSheet.register(loaded, obs)
            SpreadSheet._instances[sid] = loaded
            del s

    def list(self) -> list:
        path = "SavedSheets/"
        filelist = [x for x in os.listdir(path)
                    if os.path.isfile(os.path.join(path, x))]
        if len(filelist) == 0:
            return filelist
        else:
            result = []
            for f in filelist:
                with open(os.path.join(path, f), "rb") as ifp:
                    loaded = pickle.load(ifp)
                    loaded.unregister(loaded._observers)
                    result.append((loaded.getId(), loaded.getName()))
            return result


    def listmem(self, dirty=False) -> list:
        d = SpreadSheet._instances
        if not dirty:
            result = list(d.values())
            #return list(d.values())
        else:
            result = []
            for sid in d.keys():
                path = "SavedSheets/" + str(sid) + ".pck"
                if os.path.isfile(path):
                    with open(path, "rb") as ifp:
                        loaded = pickle.load(ifp)
                        loaded.unregister(loaded._observers)
                        if not d[sid]._equals(loaded):
                            result.append(d[sid])
            #return result
        memlist= []
        for s in result:
            memlist.append((s.getId(), s.getName()))
        return  memlist


    def delete(self, sid: int):
        path = "SavedSheets/" + str(sid) + ".pck"
        if os.path.isfile(path):
            os.remove(path)
        try:
            SpreadSheet._getinstance(sid).notify("Sheet has been deleted")
            SpreadSheet._getinstance(sid).unregister(SpreadSheet._getinstance(sid)._observers)
            del SpreadSheet._instances[sid]
        except:
            pass