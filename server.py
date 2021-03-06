#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, TCP_NODELAY, SO_KEEPALIVE
from threading import Thread
from datetime import datetime
import time
import signal
import sys
import logging

logging.basicConfig(filename="server.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def sigterm_handler(_signo, _stack_frame):
    print("Exiting...")
    logging.info("Exited.")
    SERVER.close()
    sys.exit(0)
signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)
active = []

def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        logging.info("%s:%s has connected." % client_address)
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):  # Takes client socket as argument.
    """
    Handles a single client connection.
    Active holds all currently non-closed tasks.
    """

    name = client.recv(BUFSIZ).decode("utf8").lstrip(",|1234567890")
    clients[client] = name
    for elem in active:
        client.send(bytes(elem))
    while True:
        msgsraw = client.recv(BUFSIZ)
        msgs = filter(None,msgsraw.decode("utf8").split("&&"))
        for msg in msgs:
            msg = bytes(msg, "utf8")
            if not bytes("!quit", "utf8") in msg:
                broadcast(msg, name)
            else:
                try:
                    client.send(bytes("!quit", "utf8"))
                    del clients[client]
                    client.close()
                    print("%s has left the chat." % name)
                    logging.info("%s has left the chat." % name)
                    sys.exit(0)
                except ConnectionResetError as e:
                    print(e)
                    sys.exit(0)


def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    try:
        for sock in clients:
            try:
                sock.send(bytes(prefix+"||", "utf8")+msg+bytes("||"+current_time+"&&", "utf8"))
            except Exception as e:
                print("Cut connection with sock. He threw an exception!", e)
                del clients[sock]
        logging.info(bytes(prefix+"||", "utf8")+msg+bytes("||"+current_time, "utf8"))
        smsg = msg.decode("utf8")
        if(smsg.startswith("!rm")):
            smsgdate = smsg.split(" ")[1]
            [active.remove(elem) for elem in active if smsgdate+"&&" == elem.decode("utf8").split("||")[3]]
        else:
            active.append(bytes(prefix+"||", "utf8")+msg+bytes("||"+current_time+"&&", "utf8"))
    except BrokenPipeError as e:
        #print("BrokenPipe.. This probably shouldn't have happened...")
        print(e)
        pass

clients = {}
addresses = {}

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
SERVER.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
SERVER.bind(ADDR)
if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections, daemon=True)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()