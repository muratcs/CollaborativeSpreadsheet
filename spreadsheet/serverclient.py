from .spreadsheet import *
from .sscontroller import *
from .sspersistency import *

import threading
import time
import json
import socket
import logging
import multiprocessing
import queue

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(module)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)
clients = {}

class Server(threading.Thread):

    def __init__(self, host='localhost', port=20445):
        super(Server, self).__init__()
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.socket.bind((self.host, self.port))
        self.timeout = None
        self.closed = False
        # self.clients = []

    def run(self):

        logger.info("Server has been started.")
        self.socket.listen()

        while True:
            if self.closed:
                logger.info("Server has been closed.")
                # for c in self.clients:
                #     c.closed = True
                self.socket.close()
                break
            try:
                # time.sleep(0.001)
                ns, peer = self.socket.accept()
                logger.debug("Client %s is connected.", peer)
                t = ClientThread(ns, peer)
                # t.daemon = True
                # self.clients.append(t)
                t.start()
                # t.join()

            except KeyboardInterrupt:
                self.socket.close()
                break
            # finally:
            #     self.socket.close()
            #     break


    def close(self):
        self.closed = True


class BClient:
    def __init__(self, host='localhost', port=20445):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.addr = None
        self.socket.connect((self.host, self.port))
        self.addr = self.socket.getsockname()
        self.closed = False

    def send(self, methodname: str, params=None):
        # self.mutex.acquire()
        if params is None:
            params = []
        data = {'method': methodname, 'params': params}
        serialized = json.dumps(data)
        self.socket.send('{:10d}'.format(len(serialized)).encode())
        self.socket.send(serialized.encode())

    def recv(self):
        response_length = int(self.socket.recv(10).decode())
        response = json.loads(self.socket.recv(response_length).decode())
        logger.debug("Client %s took response: %s", self.addr, response)
        return response

    def closeclient(self):
        logger.info("Client %s is closed.", self.addr)
        self.socket.close()

class Client(threading.Thread):


    def __init__(self, host='localhost', port=20445):
        super(Client, self).__init__()
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.addr = None
        self.socket.connect((self.host, self.port))
        self.addr = self.socket.getsockname()
        self.cmdqueue = queue.Queue()
        self.request = False
        self.closed = False
        self.sendlock = threading.Lock()
        self.recvcondition = threading.Condition(self.sendlock)

    def send(self, methodname: str, params=None):
        # self.mutex.acquire()
        if params is None:
            params = []
        data = {'method': methodname, 'params': params}
        self.cmdqueue.put(data)
        self.request = True

    def close(self):
        self.send('close', [])

    def start(self):
        super(Client, self).start()
        t = threading.Thread(target=self.recvfromserver)
        # t.daemon = True
        t.start()

    def run(self):
        # super(Client, self)._wait_for_tstate_lock()

        while True:
            if self.request:
                data = self.cmdqueue.get()
                self.sendtoserver(data)
                self.request = not self.cmdqueue.empty()
                if data['method'] == 'close':
                    self.closed = True
                    # self.closeclient()
                    break

            # else:
            #     time.sleep(0.001)


    def sendtoserver(self, data):
        try:
            with self.sendlock:
                serialized = json.dumps(data)
                self.socket.send('{:10d}'.format(len(serialized)).encode())
                self.socket.send(serialized.encode())
        except:
            print("Exception occurred")
            pass


    def recvfromserver(self):
        while True:
            if self.closed:
                self.closeclient()
                break

            # time.sleep(0.001)
            if self.recvcondition:
                try:
                    response_length = int(self.socket.recv(10).decode())
                    response = json.loads(self.socket.recv(response_length).decode())
                    logger.debug("Client %s took response: %s", self.addr, response)
                except:
                    print("Exception occurred")
                    # self.closeclient()
                    # break
                    pass


    def closeclient(self):
        logger.info("Client %s is closed.", self.addr)
        self.socket.close()


class ClientThread(threading.Thread):
    def __init__(self, ns, addr):
        super(ClientThread, self).__init__()
        self.socket = ns
        self.addr = addr
        self.c = None
        self.p = SSPersistency()
        self.lock = threading.Lock()
        self.sendcond = threading.Condition(self.lock)
        self.t = threading.Thread(target=self.checknotification)
        # self.t.daemon = True
        self.closed = False
        self.updates = []

    def _receive(self):
        length = int(self.socket.recv(10).decode())
        request = self.socket.recv(length).decode()
        return json.loads(request)

    def _send(self, reply):
        with self.lock:
            try:
                response = json.dumps(reply)
                self.socket.send('{:10d}'.format(len(response)).encode())
                self.socket.send(response.encode())
            except:
                print("Exception occurred")
                pass

    def checknotification(self):
        while True:
            if self.closed:
                break
            if self.c and self.c.condition and self.sendcond:
                    # self._send(self.c.log)
                    # print(self.c.log)
                    if not self.c.log.__contains__(str(self.addr)):
                        self.updates.append(self.c.log)
                    self.c.condition = False
            else:
                time.sleep(0.0001)


    def start(self):
        super(ClientThread, self).start()
        self.t.start()

    def run(self):
        while self.socket:
            # time.sleep(0.0001)
            if self.closed:
                time.sleep(0.5)
                self.socket.close()
                break
            try:
                # with self.lock:
                data = self._receive()
                logger.debug("Client %s sent data: %s", self.addr, data)
                self.protocol(data)

            except:
                print("Exception occurred")
                logger.info("Connection to client %s is lost.", self.addr)
                break


    def protocol(self, data: dict):

        try:
            # time.sleep(2)
            method = data['method']
            params = data['params']

            if method == "constructor":
                sid = params[0]
                if sid == 'NEW':
                    row = params[1]
                    col = params[2]
                    self.c = SSController('NEW', row, col)
                    reply = "Controller object created with row={}, col={}".format(row, col)
                else:
                    time.sleep(0.0001)
                    self.c = SSController(sid)
                    reply = "Controller object attached to id={} ".format(sid)
                self.c.setClientAddr(self.addr)

            elif method == "getId":
                reply = self.c.getId()
                reply = "getId outcome: " + str(reply)

            elif method == "setName":
                name = params[0]
                self.c.setName(name)
                reply = "Name change method called."

            elif method == "getName":
                reply = self.c.getName()
                reply = "getName outcome: " + reply

            elif method == "getCell":
                addr = params[0]
                reply = self.c.getCell(addr)

            elif method == "getCells":
                addr = params[0] if len(params) else "ALL"
                reply = self.c.getCells(addr)

            elif method == "setCellValue":
                addr = params[0]
                content = params[1]
                self.c.setCellValue(addr, content)
                reply = "SetCellValue method called."

            elif method == "setCellFormula":
                addr = params[0]
                formula = params[1]
                self.c.setCellFormula(addr, formula)
                reply = "SetCellFormula method called."

            elif method == "evaluate":
                iterations = params[0] if len(params) else 10
                self.c.evaluate(iterations)
                reply = "Evaluate method called."

            elif method == "upload":
                csv = params[0]
                isfile = params[1] if len(params)==2 else True
                self.c.upload(csv, isfile)
                reply = "Upload method called."

            elif method == "cutRange":
                addr = params[0]
                self.c.cutRange(addr)
                reply = "CutRange method called."

            elif method == "copyRange":
                addr = params[0]
                self.c.copyRange(addr)
                reply = "CopyRange method called."

            elif method == "pasteRange":
                addr = params[0]
                self.c.pasteRange(addr)
                reply = "PasteRange method called."

            elif method == "save":
                objid = params[0]
                self.p.save(objid)
                reply = "Save method called."

            elif method == "load":
                objid = params[0]
                self.p.load(objid)
                reply = "Load method called."

            elif method == "list":
                reply = self.p.list()

            elif method == "listmem":
                dirty = params[0] if len(params) else False
                reply = self.p.listmem(dirty)

            elif method == "delete":
                objid = params[0]
                self.p.delete(objid)
                reply = "Delete method called."

            elif method == "recvUpdates":
                reply = self.updates.copy()
                self.updates.clear()

            elif method == 'close':
                self.closed = True
                if self.c and self.c._attached:
                    self.c._attached.unregister(self.c)
                del self.c
                self.c = None
                reply = "Close request taken."

            else:
                reply = "Invalid operation"

            self._send(reply)

        except:
            logger.error("Error occurred during protocol.")
            self._send("Invalid operation.")
            # time.sleep(0.001)
            pass

