import itertools
import re
import math
import Equation
import os
import time
import threading
import logging


# class Instances:
#     __d = {}
#
#     def __init__(self):
#         pass
#
#     @classmethod
#     def getd(cls):
#         return Instances.__d

class SpreadSheet(object):

    class Cell:

        def __init__(self):
            self.value = ""
            self.celltype = "string"
            # self.addr = ""
            self.formulastr = ""

        def getvalue(self):
            return self.value

        def getcelltype(self):
            return self.celltype

        def getformula(self):
            return self.formulastr

        def _setcontent(self, content, evaluate=0):
            if not evaluate:
                self.formulastr = ""
            try:
                self.value = float(content)
                if self.value.is_integer():
                    self.value = int(content)
                self.celltype = "number"
            except ValueError:
                self.value = content
            if isinstance(self.value, (int, float)):
                self.celltype = "number"
            elif len(content) == 0 or content[0] != '=':
                self.celltype = "string"
            else:
                self.celltype = "formula"
                self.formulastr = content[1:]
            if evaluate:
                self.celltype = "formula"

        def isformula(self):
            return self.celltype == "formula"

    __newid = itertools.count(1).__next__

    _instances = {}
    # ins = Instances.getd

    def __init__(self, rows, cols, givenid=None, reduced=False):
        self.mutex = threading.RLock()
        # self.updated = threading.Condition()
        self._maxrows = rows
        self._maxcols = cols
        self._name = "Unnamed"
        self.__cells = [[SpreadSheet.Cell() for _ in range(cols)]
                        for _ in range(rows)]
        if reduced:
            self.__id = givenid
        elif givenid is not None and givenid not in self._instances.keys()\
                and self._notunique(givenid):
            self.__id = givenid
        else:
            nid = SpreadSheet.__newid()
            while nid in self._instances.keys() or self._notunique(nid):
                nid = SpreadSheet.__newid()
            self.__id = nid
        if not reduced:
            self._instances[self.__id] = self
        self._observers = []
        # self.ins()[self.__id] = self

    def register(self, obs):
        if isinstance(obs, list):
            obs = obs.copy()
            for o in obs:
                self._observers.append(o)
                o._attached = self
        elif obs is not None:
            self._observers.append(obs)
            obs._attached = self

    def unregister(self, obs):
        if isinstance(obs, list):
            obs = obs.copy()
            for o in obs:
                self._observers.remove(o)
                o._attached = None
        elif obs is not None:
            self._observers.remove(obs)
            obs._attached = None

    def notify(self, message):
        for o in self._observers:
            o.update(self, message)

    # def __setstate__(self, state):
    #     self.__dict__ = state
    #     self.__dict__.__setitem__('mutex', threading.RLock())

    def __reduce__(self):
        d = self.__dict__.copy()
        d.__delitem__('mutex')
        return (self.__class__,
                (self._maxrows, self._maxcols, self.__id, True), d)

    @classmethod
    def _notunique(cls, sid):
        path = "SavedSheets/" + str(sid) + ".pck"
        return os.path.exists(path)

    @classmethod
    def _getinstance(cls, sid):
        try:
            return SpreadSheet._instances[sid]
        except KeyError:
            return None

    @classmethod
    def _addinstance(cls, instance):
        SpreadSheet._instances[instance.getId()] = instance

    def _equals(self, instance) -> bool:
        # c1 = self.getCells()
        # c2 = instance.getCells()
        return self.getId() == instance.getId() and\
               self.getName() == instance.getName() and\
               self.getCells() == instance.getCells()


    def getId(self) -> int:
        with self.mutex:
            return self.__id

    def setName(self, name: str, caller=None):
        with self.mutex:
            oldname = self._name
            self._name = name
            self.notify("Name of spreadsheet with id {} has changed by {} from {} to {} "
                        .format(self.__id, caller, oldname, name))

    def getName(self) -> str:
        with self.mutex:
            return self._name

    @staticmethod
    def encodeaddr(row: int, col: int) -> str:
        assert row >= 0 and col >= 0
        figures = []
        while col >= 0 or not len(figures):
            figures.insert(0, chr((col % 26) + 65))
            col = int(col/26) - 1
        return "".join(figures) + str(row+1)

    @staticmethod
    def _parseaddr(addr: str) -> tuple:
        assert len(addr) > 0 and addr.isalnum()
        i = 0
        for i, j in enumerate(addr):
            if j.isdigit():
                break

        row = int(addr[i:])

        col = 0
        j = i
        while addr[:i]:
            col += (ord(addr[i - 1]) - ord("@")) * (26 ** (j - i))
            i -= 1

        return row - 1, col - 1

    @staticmethod
    def parserangeaddr(rangeaddr: str) -> tuple:
        if ':' not in rangeaddr:
            return SpreadSheet._parseaddr(rangeaddr)
        addr1, addr2 = rangeaddr.split(':')
        addr1, addr2 = SpreadSheet._parseaddr(addr1), SpreadSheet._parseaddr(addr2)
        return addr1, addr2


    def _getcellat(self, row: int, col: int) -> Cell:
        return self.__cells[row][col]

    def getCell(self, addr: str) -> tuple:
        with self.mutex:
            row, col = self._parseaddr(addr)
            assert row < self._maxrows and col < self._maxcols
            cell = self.__cells[row][col]
            if cell.isformula():
                return cell.getvalue(), cell.getcelltype(), cell.getformula()
            return cell.getvalue(), cell.getcelltype()

    def getCells(self, rangeaddr='ALL') -> str:
        with self.mutex:
            if rangeaddr == 'ALL':
                addr1 = 0, 0
                addr2 = self._maxrows - 1, self._maxcols - 1
            else:
                addr1, addr2 = rangeaddr.split(':')
                addr1, addr2 = self._parseaddr(addr1), self._parseaddr(addr2)
            assert addr1[0] <= addr2[0] <= self._maxrows \
                   and addr1[1] <= addr2[1] <= self._maxcols

            result = ""
            for r in range(addr1[0], addr2[0] + 1):
                for c in range(addr1[1], addr2[1] + 1):
                    cell = self.__cells[r][c]
                    result += str(cell.getvalue()) + ","
                result = result[:-1] + '\n'
            return result[:-1]


    def _setaddrvalue(self, addr: str, content, caller=None):
        row, col = self._parseaddr(addr)
        assert row < self._maxrows and col < self._maxcols
        cell = self._getcellat(row, col)
        oldcontent = cell.getvalue()
        cell._setcontent(content)
        if isinstance(oldcontent, str) and not len(oldcontent):
            oldcontent = '""'
        if isinstance(content, str) and not len(content):
            content = '""'
        self.notify("In spreadsheet with id {}, cell content at {} has changed by {} from {} to {} "
                    .format(self.__id, addr, caller, oldcontent, content))


    def setCellValue(self, rangeaddr: str, content, caller=None):
        with self.mutex:
            # time.sleep(1)
            if ':' not in rangeaddr:
                self._setaddrvalue(rangeaddr, content, caller)
            else:
                rangetupl = SpreadSheet.parserangeaddr(rangeaddr)
                for i in range(rangetupl[0][0], rangetupl[1][0] + 1):
                    for j in range(rangetupl[0][1], rangetupl[1][1] + 1):
                        self._setaddrvalue(SpreadSheet.encodeaddr(i, j), content, caller)


    def setCellFormula(self, addr: str, formulastr: str, caller=None):
        with self.mutex:
            if formulastr[0] != '=':
                formulastr = '=' + formulastr
            self.setCellValue(addr, formulastr, caller)

    @staticmethod
    def _split_semicolon(x: str):
        result = []
        prevpos, pos = 0, 0
        balanced = 0
        while x[pos:]:
            a = x[pos]
            if a == '(':
                balanced += 1
            if a == ')':
                balanced -= 1
            if a == ';' and balanced == 0:
                result.append(x[prevpos:pos].strip())
                prevpos = pos + 1
            pos += 1
        result.append(x[prevpos:].strip())
        return result

    @staticmethod
    def _split_if(s: str):
        balanced = 0
        parts = []
        part = ''
        for c in s:
            part += c
            if c == '(':
                balanced += 1
            elif c == ')':
                balanced -= 1
            elif c in ["<", ">", "="] and balanced == 0:
                if len(part) == 1 and c == '=':
                    parts[1] = parts[1] + part
                else:
                    parts.append(part[:-1].strip())
                    parts.append(part[-1:])
                part = ''
        if len(part):
            parts.append(part.strip())
        return parts

    @staticmethod
    def _split_ops(s: str):
        balanced = 0
        parts = []
        parts2 = []
        part = ''
        for c in s:
            part += c
            if c == '(':
                balanced += 1
            elif c == ')':
                balanced -= 1
            elif c in ['*', '/', '+', '-', '%', '^'] and balanced == 0:
                parts.append(part[:-1].strip())
                parts2.append(part[-1])
                part = ''
        if len(part):
            parts.append(part.strip())
        return parts, parts2

    def _calculate(self, x: str):

        # re_parser = '([^\(;]*\(.*?\)|[^;]*) ?; ?'
        # regex_split = ";(?!(?:[^(]*\([^)]*\))*[^()]*\))"
        x = x.strip()
        splitexp = "[*+%/^-](?!(?:[^(]*\([^)]*\))*[^()]*\))"
        x_exprs = re.split(splitexp, x)
        x_ops = re.findall(splitexp, x)
        splitops = SpreadSheet._split_ops(x)
        x_exprs = splitops[0]
        x_ops = splitops[1]
        if len(x_exprs) > 1 and not [i in x for i in ["<", "=", ">"]].count(True):
            for i, e in enumerate(x_exprs):
                x_exprs[i] = str(self._calculate(e))
            i = 1
            for op in x_ops:
                x_exprs.insert(i, op)
                i = i + 2
            x = "".join(x_exprs)

        if x.startswith("ABS("):
            x = x[4:-1]
            x = SpreadSheet._calculate(self, x)
            assert isinstance(x, (int, float))
            return math.fabs(x)

        elif x.startswith("FLOOR("):
            x = x[6:-1]
            x = SpreadSheet._calculate(self, x)
            assert isinstance(x, (int, float))
            return math.floor(x)

        elif x.startswith("CEILING("):
            x = x[8:-1]
            x = SpreadSheet._calculate(self, x)
            assert isinstance(x, (int, float))
            return math.ceil(x)

        elif x.startswith("SIN("):
            x = x[4:-1]
            x = SpreadSheet._calculate(self, x)
            assert isinstance(x, (int, float))
            return math.sin(x)

        elif x.startswith("COS("):
            x = x[4:-1]
            x = SpreadSheet._calculate(self, x)
            assert isinstance(x, (int, float))
            return math.cos(x)

        elif x.startswith("TAN("):
            x = x[4:-1]
            x = SpreadSheet._calculate(self, x)
            assert isinstance(x, (int, float))
            return math.tan(x)

        elif x.startswith("LOG("):
            x = x[4:-1]
            args_ = SpreadSheet._split_semicolon(x)
            assert 1 <= len(args_) <= 2
            x = args_[0]
            if len(args_) == 2:
                y = args_[1]
            else:
                y = "10"
            x, y = SpreadSheet._calculate(self, x),\
                   SpreadSheet._calculate(self, y)
            assert isinstance(x and y, (int, float))
            return math.log(x, y)

        elif x.startswith("POW("):
            x = x[4:-1]
            args_ = SpreadSheet._split_semicolon(x)
            assert len(args_) == 2
            x = args_[0]
            y = args_[1]
            x, y = SpreadSheet._calculate(self, x),\
                   SpreadSheet._calculate(self, y)
            assert isinstance(x and y, (int, float))
            return math.pow(x, y)

        elif x.startswith("IF("):
            x = x[3:-1]
            args_ = SpreadSheet._split_semicolon(x)
            assert len(args_) == 3
            x = args_[0]
            if x.__contains__('(') and not x.startswith('('):
                x = SpreadSheet._split_if(x)
                x1 = x[0]
                x2 = x[2]
                x1 = SpreadSheet._calculate(self, x1)
                x2 = SpreadSheet._calculate(self, x2)
                x = str(x1) + x[1] + str(x2)
            y = args_[1]
            z = args_[2]
            x = SpreadSheet._calculate(self, x)
            if x:
                state = SpreadSheet._calculate(self, y)
            else:
                state = SpreadSheet._calculate(self, z)
            if state == 1:
                state = "TRUE"
            elif state == 0:
                state = "FALSE"
            return state

        elif x.startswith("SUM("):
            x = x[4:-1]
            args_ = SpreadSheet._split_semicolon(x)
            sum_ = 0
            for arg in args_:
                arg = SpreadSheet._calculate(self, arg)
                assert isinstance(arg, (int, float, tuple))
                if isinstance(arg, tuple):
                    for i in range(arg[0][0], arg[1][0] + 1):
                        for j in range(arg[0][1], arg[1][1] + 1):
                            y = self._getcellat(i, j).getvalue()
                            assert isinstance(y, (int, float))
                            sum_ += y
                else:
                    sum_ += arg
            return sum_

        elif x.startswith("COUNTIF("):
            x = x[8:-1]
            args_ = SpreadSheet._split_semicolon(x)
            assert len(args_) == 2
            x = args_[0]
            y = args_[1]
            x, y = SpreadSheet._calculate(self, x),\
                   SpreadSheet._calculate(self, y)
            assert isinstance(x, tuple) and len(x) == 2
            count = 0
            for i in range(x[0][0], x[1][0] + 1):
                for j in range(x[0][1], x[1][1] + 1):
                    if self._getcellat(i, j).getvalue() == y:
                        count += 1
            return count

        elif x.startswith("AVERAGE("):
            x = x[8:-1]
            args_ = SpreadSheet._split_semicolon(x)
            sum_ = 0
            count = 0
            for arg in args_:
                arg = SpreadSheet._calculate(self, arg)
                assert isinstance(arg, (int, float, tuple))
                if isinstance(arg, tuple):
                    for i in range(arg[0][0], arg[1][0] + 1):
                        for j in range(arg[0][1], arg[1][1] + 1):
                            y = self._getcellat(i, j).getvalue()
                            assert isinstance(y, (int, float))
                            sum_ += y
                            count += 1
                else:
                    sum_ += arg
                    count += 1
            avg = sum_ / max(count, 1)
            # float("%.3f" % avg)
            return round(avg, 3)

        else:
            try:
                return float(x)
            except ValueError:
                pass
            if x.startswith(("'", '"')) and x.endswith(("'", '"')):
                return x[1:-1]
            elif x.__contains__(":"):
                return SpreadSheet.parserangeaddr(x)
            else:
                if x.startswith("(") and x.endswith(")"):
                    x = x[1:-1]
                eqstr = x
                eq = re.sub("[A-Z]+[0-9]+",
                            lambda m: self._convert(m), eqstr)
                eq = eq.replace("SIN(", "sin(")
                eq = eq.replace("COS(", "cos(")
                eq = eq.replace("TAN(", "tan(")
                eq = eq.replace("ABS(", "abs(")
                return Equation.Expression(eq)()


    def _convert(self, addr) -> str:
        tup = self.getCell(addr.group())
        assert tup[1] == "number" or len(tup) == 3
        return str(tup[0])

    def evaluate(self, iterations=10, caller=None):
        with self.mutex:
            flag = 0
            for i, row in enumerate(self.__cells):
                for j, cell in enumerate(row):

                    if cell.isformula():
                        try:
                            value = self._calculate(cell.getformula())
                            if isinstance(value, float):
                                # value = float("%.9f" % value)
                                value = round(value, 9)
                                if value.is_integer():
                                    value = int(value)
                            if cell.getvalue() != value:
                                flag = 1
                            cell._setcontent(value, 1)
                        except:
                            pass
            if flag == 1 and iterations >= 1:
                self.evaluate(iterations - 1)
                self.notify("In spreadsheet with id {}, the formulas are evaluated by {}."
                            .format(self.__id, caller))

