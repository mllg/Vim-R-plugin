
import sys
import socket
import os
import re

VimComPort = 0
PortWarn = 0
VimComFamily = None

def DiscoverVimComPort():
    global PortWarn
    global VimComPort
    global VimComFamily
    HOST = "localhost"
    VimComPort = 10000
    repl = "NOTHING"
    vii = os.getenv("VIMINSTANCEID")
    if vii is None:
        print "call RWarningMsg('VIMINSTANCEID not found by nvimcom.py.')\n"
        sys.stdout.flush()
        return
    scrt = os.getenv("VIMRPLUGIN_SECRET")
    if scrt is None:
        print "call RWarningMsg('VIMRPLUGIN_SECRET not found by nvimcom.py.')\n"
        sys.stdout.flush()
        return

    while repl.find(scrt) < 0 and VimComPort < 10049:
        VimComPort = VimComPort + 1
        for res in socket.getaddrinfo(HOST, VimComPort, socket.AF_UNSPEC, socket.SOCK_DGRAM):
            af, socktype, proto, canonname, sa = res
            try:
                sock = socket.socket(af, socktype, proto)
                sock.settimeout(0.1)
                sock.connect(sa)
                if sys.hexversion < 0x03000000:
                    sock.send("\001" + vii + " What port [Python 2]?")
                    repl = sock.recv(1024)
                else:
                    sock.send("\001" + vii + " What port [Python 3]?".encode())
                    repl = sock.recv(1024).decode()
                sock.close()
                if repl.find(scrt):
                    VimComFamily = af
                    break
            except:
                sock = None
                continue

    if VimComPort >= 10049:
        VimComPort = 0
        if not PortWarn:
            PortWarn = True
            print "let g:rplugin_vimcomport = 0\n"
            sys.stdout.flush()
            print "call RWarningMsg('VimCom port not found.')\n"
            sys.stdout.flush()
        return
    else:
        print "let g:rplugin_vimcomport = " + str(VimComPort) + "\n"
        sys.stdout.flush()
        PortWarn = False
        if repl.find("1.0-5") != 0:
            print "call RWarningMsg('This version of Vim-R-plugin requires vimcom 1.0-5.')\n"
            sys.stdout.flush()
        return


def SendToVimCom(aString):
    HOST = "localhost"
    global VimComPort
    global VimComFamily
    if VimComPort == 0:
        DiscoverVimComPort()
        if VimComPort == 0:
            return "NoPort"
    received = None

    sock = socket.socket(VimComFamily, socket.SOCK_DGRAM)
    sock.settimeout(3.0)

    try:
        sock.connect((HOST, VimComPort))
        if sys.hexversion < 0x03000000:
            sock.send(aString)
            received = sock.recv(5012)
        else:
            sock.send(aString.encode())
            received = sock.recv(5012).decode()
    except:
        pass
    finally:
        sock.close()

    if received is None:
        VimComPort = 0
        return "NOANSWER"
    else:
        received = received.replace("'", "' . \"'\" . '")
        return received

while True:
    line = raw_input()
    if line.find("SendToVimCom") != -1:
        line = line.replace("SendToVimCom ", "")
        if line.find("I\002") != -1:
            line = line.replace("I\002", "")
            printreply = False
        else:
            printreply = True
        rpl = SendToVimCom(line)
        if printreply:
            print "let g:rplugin_lastrpl = '" + rpl + "'\n"
    else:
        if line.find("DiscoverVimComPort") != -1:
            DiscoverVimComPort()
        else:
            print "call RWarningMsg('nvimcom.py: Unknown command: '" + line + "'.\n"
    sys.stdout.flush()

