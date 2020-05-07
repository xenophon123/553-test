#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread
from collections import deque


QUEUE_LENGTH = 10
SEND_BUFFER = 4096
SONG_INFO = []

# per-client struct
class Client:
    def __init__(self, conn):
        self.lock = Lock()
        self.conn = conn
        self.data_queue = deque()
        self.song_id = -1
        self.music_file = None
        self.already_sent = 0
        self.is_updated = False


# Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client):
    while True:
        client.lock.acquire()
        while len(client.data_queue) != 0:
            try:
                client.conn.sendall(client.data_queue.popleft())
            except:
                print "Server Error in Sending Data to Client"
                print "Close the write thread"
                return
        client.lock.release()

        client.lock.acquire()
        if client.is_updated:
            client.is_updated = False
            f = open(SONG_INFO[2] + "/" + SONG_INFO[0][client.song_id], "r")
            client.music_file = f.read()
            client.already_sent = 0
            f.close()
        if client.music_file != None:
            if client.already_sent >= len(client.music_file):
                client.music_file = None
            else:
                header = "TYPE:RES/OK\nCOMMAND:PLAYING\n\n"
                body_len = SEND_BUFFER - len(header)
                data = client.music_file[client.already_sent:client.already_sent+body_len]
                client.already_sent += body_len
                client.data_queue.append(header + data)
        client.lock.release()
        
# Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client):
    while True:
        data = client.conn.recv(SEND_BUFFER)
        if data == "":
            print "Server Error in Receiving Data from Client"
            print "Close the read thread"
            break
        print "\nserver receives: \n", data
        data_lst = data.split("\n")
        if len(data_lst) < 4:
            print "Invalid Framing"
            continue
        try:
            _, command = data_lst[1].split(":")
        except ValueError:
            print "Invalid Framing for COMMAND"
            continue
        if command == "LIST":
            client.lock.acquire()
            client.data_queue.appendleft("TYPE:RES/OK\nCOMMAND:LIST\n\n" + SONG_INFO[1])
            client.lock.release()
        elif command == "STOP":
            client.lock.acquire()
            client.music_file = None 
            client.data_queue.append("TYPE:RES/OK\nCOMMAND:STOP\n\n")
            client.lock.release()
        elif command == "PLAY":
            song_id = -1
            try:
                song_id = int(data_lst[2].split(":")[1])
            except ValueError:
                print "Invalid Framing for PARAMETER"
                continue
            if song_id >= len(SONG_INFO[0]) or song_id < 0:
                print "Invalid Song ID"
                continue
            client.lock.acquire()
            client.data_queue.append("TYPE:RES/OK\nCOMMAND:PLAY\n\n")
            client.song_id = song_id
            client.is_updated = True
            client.lock.release()

def get_mp3s(musicdir):
    print("Reading music files...")
    songs = []
    for filename in os.listdir(musicdir):
        if not filename.endswith(".mp3"):
            continue
        songs.append(filename)
    songs_str = []
    for i in range(len(songs)):
        song_str = "[" + str(i) + "] " + songs[i]
        songs_str.append(song_str)
    print("Found {0} song(s)!".format(len(songs)))
    return songs, "\n".join(songs_str)

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python server.py [port] [musicdir]")
    if not os.path.isdir(sys.argv[2]):
        sys.exit("Directory '{0}' does not exist".format(sys.argv[2]))

    port = int(sys.argv[1])
    songs, songs_str = get_mp3s(sys.argv[2])
    SONG_INFO.append(songs)
    SONG_INFO.append(songs_str)
    SONG_INFO.append(sys.argv[2])
    threads = []

    # Create a socket and accept incoming connections
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", port))
    s.listen(QUEUE_LENGTH)

    while True:
        conn, _ = s.accept()
        client = Client(conn)
        t = Thread(target=client_read, args=(client,))
        threads.append(t)
        t.start()
        t = Thread(target=client_write, args=(client,))
        threads.append(t)
        t.start()
    s.close()


if __name__ == "__main__":
    main()