import time

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from spreadsheet.models import BrowserClient
from spreadsheet.serverclient import BClient, clients
from spreadsheet.forms import *

# Create your views here.

def createClient():
    try:
        c = BClient()
        clients[id(c)] = c
        return id(c)

    except Exception as e:
        return str(e)


def sendData(cid, method, params=None):
    if params is None:
        params = []
    try:
        c = clients[cid]
        c.send(method, params)
        r = c.recv()
        return r

    except Exception as e:
        print(str(e))
        return str(e)


def parsecsv(csv: str) -> list:
        if not len(csv):
            return []
        parsed = csv.split('\n')
        for i, cols in enumerate(parsed):
            parsed[i] = cols.split(',')
        return parsed

def encodeadr(col: int) -> str:
    figures = []
    while col >= 0 or not len(figures):
        figures.insert(0, chr((col % 26) + 65))
        col = int(col/26) - 1
    return "".join(figures)

def parseaddr(addr: str) -> tuple:
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

def getdiff(cells, cells2):
    rows = []
    cols = []
    contents = []
    for i in range(len(cells)):
        for j in range(len(cells[0])):
            if cells[i][j] != cells2[i][j]:
                rows.append(i)
                cols.append(j)
                contents.append(cells2[i][j])
    return {'rows': rows, 'cols': cols, 'contents': contents}



def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def encodeJSON(request, i, j):
    encoded = encodeadr(int(j)) + str(int(i)+1)
    return JsonResponse({'result:': 'Success', 'encoded': encoded})


lastCells = []

@login_required
def index(request):
    r = 'Fill in the required fields!'
    try:

        if request.POST['submit'] == 'Submit':  # form submitted, process it

            user = User.objects.get(username=request.user)
            if BrowserClient.objects.filter(user=user).exists():
                bc = BrowserClient.objects.get(user=user)
            else:
                cid = createClient()
                bc = BrowserClient.objects.create(user=user, cid=cid)

            if request.POST['type'] == 'create':
                if request.POST['row'] and request.POST['col']:
                    row = int(request.POST['row'])
                    col = int(request.POST['col'])
                    r = sendData(bc.cid, 'constructor', ['NEW', row, col])
                else:
                    return render(request, 'index.html', {'response': r})

            elif request.POST['type'] == 'attach':
                if request.POST['sid']:
                    sid = int(request.POST['sid'])
                    r = sendData(bc.cid, 'constructor', [sid])
                else:
                    return render(request, 'index.html', {'response': r})

            else:
                return redirect(index)

            # render(request, 'control.html', context)
            return redirect('/control', {'response': r})

        elif request.POST['submit'] == 'Cancel':
            return redirect(index)  # redirect to home page
        else:
            return render(request, 'error.html', {'message': 'Invalid request'})
    except KeyError:  # form not submitted yet, show it
        return render(request, 'index.html')


def createJSON(request, op):

    jump = 0

    if op == 'create' and request.POST['row'] and request.POST['col']:
        jump = 1

    elif op == 'attach' and request.POST['sid']:
        jump = 2

    if not jump:
        return JsonResponse({'result': 'Fail', 'response': 'Fill in the required fields!'})

    user = User.objects.get(username=request.user)
    if BrowserClient.objects.filter(user=user).exists():
        bc = BrowserClient.objects.get(user=user)
        cid = bc.cid
    else:
        cid = createClient()
        bc = BrowserClient.objects.create(user=user, cid=cid)

    if jump == 1:
        row = int(request.POST['row'])
        col = int(request.POST['col'])
        r = sendData(bc.cid, 'constructor', ['NEW', row, col])

    else:
        sid = int(request.POST['sid'])
        r = sendData(bc.cid, 'constructor', [sid])

    sid = int(sendData(cid, "getId").partition(':')[2])
    sname = sendData(cid, "getName").partition(':')[2]
    cells = parsecsv(sendData(cid, 'getCells'))
    global lastCells
    lastCells = cells
    cellcolls = []
    for c in range(len(cells[0])):
        cellcolls.append(encodeadr(c))
    context = {'result': "Success", 'sid': sid, 'sname': sname,
               'cells': cells, 'cellcolls': cellcolls, 'response': r}

    return JsonResponse(context)



@login_required
def controlJSON(request, op):
    user = User.objects.get(username=request.user)
    bc = get_object_or_404(BrowserClient, user=user)
    cid = bc.cid
    sid = int(sendData(cid, "getId").partition(':')[2])
    r = 'Fill in the required fields!'
    context = {'result': "Success", 'sid': sid}


    try:
        if op == 'setName':
            if request.POST['setNameForm']:
                name = request.POST['setNameForm']
                r = sendData(cid, 'setName', [name])

        elif op == 'setCellValue':
            if request.POST['setCellAddr'] and request.POST['setCellContent']:
                addr = request.POST['setCellAddr']
                content = request.POST['setCellContent']
                try:
                    content = int(content)
                except:
                    pass
                cells = parsecsv(sendData(cid, 'getCells'))
                r = sendData(cid, 'setCellValue', [addr, content])
                r = r + " " + sendData(cid, 'evaluate')
                cells2 = parsecsv(sendData(cid, 'getCells'))
                context.update(getdiff(cells, cells2))
                # row, col = parseaddr(addr)
                # sendData(cid, 'getCell', [addr])[0]

        elif op == 'getCell':
            if request.POST['getCellForm']:
                addr = request.POST['getCellForm']
                r = 'Cell at ' + addr + ': '
                r = r + str(sendData(cid, 'getCell', [addr]))

        elif op == 'getCells':
            addr = 'ALL'
            if request.POST['getCellsForm']:
                addr = request.POST['getCellsForm']
            r = sendData(cid, 'getCells', [addr])
            r = parsecsv(r).__repr__()

        elif op == 'evaluate':
            iters = 10
            if request.POST['evaliters']:
                iters = int(request.POST['evaliters'])
            cells = parsecsv(sendData(cid, 'getCells'))
            r = sendData(cid, 'evaluate', [iters])
            cells2 = parsecsv(sendData(cid, 'getCells'))
            context.update(getdiff(cells, cells2))

        elif op == 'list':
            r = sendData(cid, 'list').__repr__()

        elif op == 'listmem':
            dirty = False
            if request.POST.getlist('listdirty') == ["1"]:
                dirty = True
            r = sendData(cid, 'listmem', [dirty]).__repr__()

        elif op == 'cutRange':
            if request.POST['cutAddr']:
                addr = request.POST['cutAddr']
                cells = parsecsv(sendData(cid, 'getCells'))
                r = sendData(cid, 'cutRange', [addr])
                cells2 = parsecsv(sendData(cid, 'getCells'))
                context.update(getdiff(cells, cells2))

        elif op == 'copyRange':
            if request.POST['copyAddr']:
                addr = request.POST['copyAddr']
                r = sendData(cid, 'copyRange', [addr])

        elif op == 'pasteRange':
            if request.POST['pasteAddr']:
                addr = request.POST['pasteAddr']
                cells = parsecsv(sendData(cid, 'getCells'))
                r = sendData(cid, 'pasteRange', [addr])
                cells2 = parsecsv(sendData(cid, 'getCells'))
                context.update(getdiff(cells, cells2))

        elif op == 'save':
            saveid = sid
            if request.POST['saveid']:
                saveid = int(request.POST['saveid'])
            r = sendData(cid, 'save', [saveid])

        elif op == 'load':
            loadid = sid
            if request.POST['loadid']:
                loadid = int(request.POST['loadid'])
            cells = parsecsv(sendData(cid, 'getCells'))
            r = sendData(cid, 'load', [loadid])
            cells2 = parsecsv(sendData(cid, 'getCells'))
            context.update(getdiff(cells, cells2))

        elif op == 'delete':
            deleteid = sid
            if request.POST['deleteid']:
                deleteid = int(request.POST['deleteid'])
            r = sendData(cid, 'delete', [deleteid])
            issame = True if (deleteid == sid) else False
            context['issame'] = issame
            if issame:
                return JsonResponse(context)


        elif op == 'uploadCSV':
            if request.POST['csv']:
                csv = request.POST['csv']
                csv = csv.replace(' ', '\n')
                r = sendData(cid, 'upload', [csv, False])

        if sendData(cid, 'getId') == 'Invalid operation.':
            return redirect(index)

        sname = sendData(cid, "getName").partition(':')[2]
        context['sname'] = sname
        context['response'] = r

        return JsonResponse(context)
    except:
        return JsonResponse({'result': 'Fail', 'response': 'Fill in the required fields.'})



def getUpdatesJSON(request):
    try:
        user = User.objects.get(username=request.user)
        bc = get_object_or_404(BrowserClient, user=user)
        cid = bc.cid
        # sid = int(sendData(cid, "getId").partition(':')[2])
        # sname = sendData(cid, "getName").partition(':')[2]
        update = sendData(cid, 'recvUpdates')
        # cells = parsecsv(sendData(cid, 'getCells'))
        # cellcolls = []
        # for c in range(len(cells[0])):
        #     cellcolls.append(encodeadr(c))
        context = {'result': "Success", 'updates': update}
        if not len(update):
            context['result'] = "Fail"

        else:
            global lastCells
            if(len(lastCells)):
                cells2 = parsecsv(sendData(cid, 'getCells'))
                context.update(getdiff(lastCells, cells2))
                lastCells = cells2
            context['sname'] = sendData(cid, 'getName').partition(':')[2]

        return JsonResponse(context)
    except:
        return JsonResponse({'result': 'Fail'})


def uploadJSON(request):
    user = User.objects.get(username=request.user)
    bc = get_object_or_404(BrowserClient, user=user)
    cid = bc.cid

    if request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        filename = './media/' + filename
        r = sendData(cid, 'upload', [filename])
        sendData(cid, 'evaluate')

        sid = int(sendData(cid, "getId").partition(':')[2])
        sname = sendData(cid, "getName").partition(':')[2]
        cells = parsecsv(sendData(cid, 'getCells'))
        cellcolls = []
        for c in range(len(cells[0])):
            cellcolls.append(encodeadr(c))
        context = {'result': "Success", 'sid': sid, 'sname': sname,
                   'cells': cells, 'cellcolls': cellcolls}

        return JsonResponse(context)
    else:
        return JsonResponse({'result': 'Fail'})



@login_required
def control(request):

    user = User.objects.get(username=request.user)
    bc = get_object_or_404(BrowserClient, user=user)
    cid = bc.cid
    sid = int(sendData(cid, "getId").partition(':')[2].strip())

    r = 'Fill in the required fields!'
    try:

        if request.POST['submit'] == 'getId':
            r = sendData(cid, 'getId')

        elif request.POST['submit'] == 'getName':
            r = sendData(cid, 'getName')

        elif request.POST['submit'] == 'getCell':
            if request.POST['getCellForm']:
                addr = request.POST['getCellForm']
                r = 'Cell at ' + addr + ': '
                r = r + str(sendData(cid, 'getCell', [addr]))

        elif request.POST['submit'] == 'getCells':
            addr = 'ALL'
            if request.POST['getCellsForm']:
                addr = request.POST['getCellsForm']
            r = sendData(cid, 'getCells', [addr])
            r = parsecsv(r)


        elif request.POST['submit'] == 'setName':
            if request.POST['setNameForm']:
                name = request.POST['setNameForm']
                r = sendData(cid, 'setName', [name])

        elif request.POST['submit'] == 'setCellValue':
            if request.POST['setCellAddr'] and request.POST['setCellContent']:
                addr = request.POST['setCellAddr']
                content = request.POST['setCellContent']
                try:
                    content = int(content)
                except:
                    pass
                r = sendData(cid, 'setCellValue', [addr, content])

        elif request.POST['submit'] == 'evaluate':
            iters = 10
            if request.POST['evaliters']:
                iters = int(request.POST['evaliters'])
            r = sendData(cid, 'evaluate', [iters])

        elif request.POST['submit'] == 'list':
            r = sendData(cid, 'list')

        elif request.POST['submit'] == 'listmem':
            dirty = False
            if request.POST.getlist('listdirty') == ["1"]:
                dirty = True
            r = sendData(cid, 'listmem', [dirty])

        elif request.POST['submit'] == 'cutRange':
            if request.POST['cutAddr']:
                addr = request.POST['cutAddr']
                r = sendData(cid, 'cutRange', [addr])

        elif request.POST['submit'] == 'copyRange':
            if request.POST['copyAddr']:
                addr = request.POST['copyAddr']
                r = sendData(cid, 'copyRange', [addr])

        elif request.POST['submit'] == 'pasteRange':
            if request.POST['pasteAddr']:
                addr = request.POST['pasteAddr']
                r = sendData(cid, 'pasteRange', [addr])

        elif request.POST['submit'] == 'save':
            saveid = sid
            if request.POST['saveid']:
                saveid = int(request.POST['saveid'])
            r = sendData(cid, 'save', [saveid])

        elif request.POST['submit'] == 'load':
            loadid = sid
            if request.POST['loadid']:
                loadid = int(request.POST['loadid'])
            r = sendData(cid, 'load', [loadid])

        elif request.POST['submit'] == 'delete':
            deleteid = sid
            if request.POST['deleteid']:
                deleteid = int(request.POST['deleteid'])
            r = sendData(cid, 'delete', [deleteid])

        elif request.POST['submit'] == 'upload':

            if request.FILES['myfile']:
                myfile = request.FILES['myfile']
                fs = FileSystemStorage()
                filename = fs.save(myfile.name, myfile)
                filename = './media/' + filename
                # print(filename)
                r = sendData(cid, 'upload', [filename])

            # deleteid = sid
            # if request.POST['deleteid']:
            #     deleteid = int(request.POST['deleteid'])
            # r = sendData(cid, 'delete', [deleteid])

        elif request.POST['submit'] == 'uploadCSV':
            if request.POST['csv']:
                csv = request.POST['csv']
                csv = csv.replace(' ', '\n')
                r = sendData(cid, 'upload', [csv, False])



        elif request.POST['submit'] == 'Cancel':
            return redirect(index)  # redirect to home page
        else:
            return render(request, 'error.html', {'message': 'Invalid request'})

        if sendData(cid, 'getId') == 'Invalid operation.':
            return redirect(index)
        sid = int(sendData(cid, "getId").partition(':')[2])
        sname = sendData(cid, "getName").partition(':')[2]
        update = sendData(cid, 'recvUpdates')
        cells = parsecsv(sendData(cid, 'getCells'))
        cellcolls = []
        for c in range(len(cells[0])):
            cellcolls.append(encodeadr(c))
        if not len(update):
            update = ["No changes detected."]
        context = {'sid': sid, 'sname': sname, 'update': update,
                   'cells': cells, 'cellcolls': cellcolls}

        context['response'] = r
        return render(request, 'control.html', context)

    except KeyError:  # form not submitted yet, show it
        sname = sendData(cid, "getName").partition(':')[2]
        update = sendData(cid, 'recvUpdates')
        cells = parsecsv(sendData(cid, 'getCells'))
        global lastCells
        lastCells = cells
        cellcolls = []
        for c in range(len(cells[0])):
            cellcolls.append(encodeadr(c))
        if not len(update):
            update = ["No changes detected."]
        context = {'sid': sid, 'sname': sname, 'update': update,
                   'cells': cells, 'cellcolls': cellcolls}
        return render(request, 'control.html', context)
