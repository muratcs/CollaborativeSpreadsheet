from .spreadsheet import *

loggerss = logging.getLogger()
loggerss.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(module)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)


class SSController:
    def __init__(self, sid='NEW', rows=0, cols=0):
        if sid == 'NEW' and rows != 0 and cols != 0:
            s = SpreadSheet(rows, cols)
        else:
            assert SpreadSheet._instances.__contains__(sid)
            s = SpreadSheet._getinstance(sid)
        self._name = "Unnamed_Controller"
        self._buffer = bytearray(0)
        self.peer = None

        # self.c = threading.Condition()
        self.logs = []
        self.condition = False
        self.log = None

        s.register(self)
        self._attached = s

    def setClientAddr(self, addr):
        self.peer = addr

    def setObsName(self, name: str):
        self._name = name

    def update(self, subj, message):
        # with self._attached.mutex:

        loggerss.info("%s -- %s has notified.", message, self.peer)
        # self.logs.append(message)
        self.log = message
        self.condition = True
        # print("{} -- {} has notified.".format(message, self._name))

    def printlogs(self):
        print("---Printing the logs of {}---".format(self._name))
        for log in self.logs:
            print(log)
        print("***Printing the logs of {} has finished***".format(self._name))

    def _parsecsv(self, csv: str) -> list:
        if not len(csv):
            return []
        parsed = csv.split('\n')
        for i, cols in enumerate(parsed):
            parsed[i] = cols.split(',')
        return parsed

    def upload(self, csvfile: str, isfile=True):
        """
        Assumes that csvcontent has a newline at the end
        """
        if isfile:
            with (open(csvfile)) as f:
                csvcontent = f.read()
        else:
            csvcontent = csvfile
        parsed = self._parsecsv(csvcontent)
        rown = len(parsed) - 1 if not len(parsed) == 0 else 0
        coln = len(parsed[0]) if rown else 0

        s = SpreadSheet(rown, coln)
        for r in range(rown):
            for c in range(coln):
                cell = s._getcellat(r, c)
                cell._setcontent(parsed[r][c])
        self._attached.unregister(self)
        s.register(self)
        self._attached = s

    def getCell(self, addr: str) -> tuple:
        return self._attached.getCell(addr)

    def getCells(self, rangeaddr='ALL') -> str:
        return self._attached.getCells(rangeaddr)

    def setCellValue(self, addr: str, content: (int, float, str)):
        # self._attached.notify("Cell content changed by {}".format(self._name))
        # print("setcell called from", self._name)
        self._attached.setCellValue(addr, content, self.peer)

    def setCellFormula(self, addr: str, formulastr: str):
        # self._attached.notify("Cell formula changed by {}".format(self._name))
        # print("setcellformula called from", self._name)
        self._attached.setCellFormula(addr, formulastr, self.peer)

    def getId(self) -> int:
        return self._attached.getId()

    def getName(self) -> str:
        return self._attached.getName()

    def setName(self, name: str):
        # self._attached.notify("Sheet name changed by {}".format(self._name))
        # print("setname called from", self._name)
        self._attached.setName(name, self.peer)

    def evaluate(self, iterations=10):
        # self._attached.notify("Evaluate called from {}".format(self._name))
        self._attached.evaluate(iterations, self.peer)

    def copyRange(self, rangeaddr: str):
        parsedrange = self.getCells(rangeaddr)
        self._buffer = bytearray(parsedrange, "UTF-8")

    def cutRange(self, rangeaddr: str):
        self.copyRange(rangeaddr)
        self._attached.setCellValue(rangeaddr, "", self.peer)

    def pasteRange(self, topleftcelladdr: str):
        if len(self._buffer):
            parsed = self._parsecsv(self._buffer.decode())
            rown, coln = len(parsed), len(parsed[0])
            s = self._attached
            beginr, beginc = SpreadSheet.parserangeaddr(topleftcelladdr)
            endr, endc = rown + beginr, coln + beginc
            assert s._maxrows >= endr and s._maxcols >= endc
            for i in range(beginr, endr):
                for j in range(beginc, endc):
                    self._attached.setCellValue(SpreadSheet.encodeaddr(i, j),
                                      parsed[i - beginr][j - beginc], self.peer)
