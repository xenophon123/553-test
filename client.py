#!/usr/bin/env python

import ao
import mad
import readline
import socket
import struct
import sys
import threading
from time import sleep

SEND_BUFFER = 4096

# The Mad audio library we're using expects to be given a file object, but
# we're not dealing with files, we're reading audio data over the network.  We
# use this object to trick it.  All it really wants from the file object is the
# read() method, so we create this wrapper with a read() method for it to
# call, and it won't know the difference.
# NOTE: You probably don't need to modify this class.
class mywrapper(object):
    def __init__(self):
        self.mf = None
        self.data = ""

    # When it asks to read a specific size, give it that many bytes, and
    # update our remaining data.
    def read(self, size):
        result = self.data[:size]
        self.data = self.data[size:]
        return result


# Receive messages.  If they're responses to info/list, print
# the results for the user to see.  If they contain song data, the
# data needs to be added to the wrapper object.  Be sure to protect
# the wrapper with synchronization, since the other thread is using
# it too!
def recv_thread_func(wrap, cond_filled, sock):
    while True:
        data = sock.recv(SEND_BUFFER)
        if data is None or len(data) == 0:
            print "Client Error in Receiving Data from Server"
            print "Close the recv thread"
            break
        data_lst = data.split("\n")
        if len(data_lst) < 4:
            print "Invalid Framing"
            continue
        try:
            _, status = data_lst[0].split(":")
            _, command = data_lst[1].split(":")
        except ValueError:
            print "Invalid Framing for TYPE/COMMAND"
            continue
        if status == "RES/INVALID":
            print "Invalid ", command
            continue
        if command == "LIST":
            if data_lst[3] == "":
                print "Empty Song List"
                continue
            print "Song List:"
            for i in range(3, len(data_lst)):
                print data_lst[i]
        elif command == "STOP":
            print "Stop playing the song"
            cond_filled.acquire()
            wrap.data = ""
            wrap.mf = None
            cond_filled.release()
        elif command == "PLAY":
            print "Begin playing the song"
            cond_filled.acquire()
            wrap.data = ""
            wrap.mf = mad.MadFile(wrap)
            cond_filled.notify()
            cond_filled.release()
        elif command == "PLAYING":
            cond_filled.acquire()
            wrap.data += "\n".join(data_lst[3:])
            cond_filled.release()


# If there is song data stored in the wrapper object, play it!
# Otherwise, wait until there is.  Be sure to protect your accesses
# to the wrapper with synchronization, since the other thread is
# using it too!
def play_thread_func(wrap, cond_filled, dev):
    while True:
        buf = None
        cond_filled.acquire()
        if wrap.mf is None:
            cond_filled.wait()
        buf = wrap.mf.read()
        cond_filled.release()
        if buf is None:
            continue
        dev.play(buffer(buf), len(buf))


def send_list_command(socket):
    data = "TYPE:REQ\nCOMMAND:LIST\n\n"
    try:
        socket.sendall(data)
    except:
        print "Client Error in Sending Data to Server"
        print "Client Quit"
        sys.exit(2)


def send_play_command(socket, song_id):
    data = "TYPE:REQ\nCOMMAND:PLAY\nPARAMETER:{0}\n\n".format(song_id)
    try:
        socket.sendall(data)
    except:
        print "Client Error in Sending Data to Server"
        print "Client Quit"
        sys.exit(2)


def send_stop_command(socket):
    data = "TYPE:REQ\nCOMMAND:STOP\n\n"
    try:
        socket.sendall(data)
    except:
        print "Client Error in Sending Data to Server"
        print "Client Quit"
        sys.exit(2)


def main():
    if len(sys.argv) < 3:
        print 'Usage: %s <server name/ip> <server port>' % sys.argv[0]
        sys.exit(1)

    # Create a pseudo-file wrapper, condition variable, and socket.  These will
    # be passed to the thread we're about to create.
    wrap = mywrapper()

    # Create a condition variable to synchronize the receiver and player threads.
    # In python, this implicitly creates a mutex lock too.
    # See: https://docs.python.org/2/library/threading.html#condition-objects
    cond_filled = threading.Condition()

    # Create a TCP socket and try connecting to the server.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((sys.argv[1], int(sys.argv[2])))

    # Create a thread whose job is to receive messages from the server.
    recv_thread = threading.Thread(
        target=recv_thread_func,
        args=(wrap, cond_filled, sock)
    )
    recv_thread.daemon = True
    recv_thread.start()

    # Create a thread whose job is to play audio file data.
    dev = ao.AudioDevice('pulse')
    play_thread = threading.Thread(
        target=play_thread_func,
        args=(wrap, cond_filled, dev)
    )
    play_thread.daemon = True
    play_thread.start()

    # Enter our never-ending user I/O loop.  Because we imported the readline
    # module above, raw_input gives us nice shell-like behavior (up-arrow to
    # go backwards, etc.).
    while True:
        line = raw_input('>> ')

        if ' ' in line:
            cmd, args = line.split(' ', 1)
        else:
            cmd = line

        # Send messages to the server when the user types things.
        if cmd in ['l', 'list']:
            send_list_command(sock)
            print 'The user asked for list.'

        if cmd in ['p', 'play']:
            send_play_command(sock, args) # TODO: 1) play the same song twice 
            print 'The user asked to play:', args

        if cmd in ['s', 'stop']:
            send_stop_command(sock)
            print 'The user asked for stop.'

        if cmd in ['quit', 'q', 'exit']:
            sys.exit(0)

if __name__ == '__main__':
    main()
