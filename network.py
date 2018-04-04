# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
import socket
import select
import pickle

################################################################################
#                          NETWORK SERVER CONTROLLER                           #
################################################################################

class NetworkServerController:

    def __init__(self, model, port, map_file):
        self.model = model
        self.port = port
        self.map_name = map_file
        self.clients = []
        self.nick_to_client = {}
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', port))
        self.s.listen(1)

    # time event
    def send_all(self, clients, data):
        for client in clients:
            client.send(data)

    def tick(self, dt):
        demande, b, c = select.select([self.s] + self.clients,[],[],1)
        for client in demande:
            if client == self.s:
                co, addr = self.s.accept()
                self.clients.append(co)
            else:
                data = client.recv(1500)
                data = data.decode()
                commands = data.split(" ")
                if not data:
                    self.clients.remove(client)
                    self.model.kill_character(self.nick_to_client[client])
                    del self.nick_to_client[client]
                    client.close()
                if (commands[0] == "#nickname"):
                    self.nick_to_client[client] = commands[1]
                    self.model.add_character(commands[1], isplayer = False)
                    self.send_all(self.clients,pickle.dumps(self.model))
                if (commands[0] == "#give_me_map"):
                    data = pickle.dumps(self.model)
                    client.send(data)
                if (commands[0] == "#move"):
                    self.model.move_character(commands[1], int(commands[2]))
                    self.send_all(self.clients,pickle.dumps(self.model))
                if (commands[0] == "#bomb"):
                    self.model.drop_bomb(commands[1])
                    self.send_all(self.clients,pickle.dumps(self.model))
        return True

################################################################################
#                          NETWORK CLIENT CONTROLLER                           #
################################################################################

class NetworkClientController:

    def __init__(self, host, port, nickname):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', port))
        self.s.listen(1)
        data = "#nickname " + nickname
        self.socket.send(data.encode())
        data = self.socket.recv(1500)
        self.model = pickle.loads(data)
        for char in self.model.characters:
            if (char.nickname == self.nickname):
                self.model.player = char

    # keyboard events

    def keyboard_quit(self):
        print("=> event \"quit\"")
        return False

    def keyboard_move_character(self, direction):
        print("=> event \"keyboard move direction\" {}".format(DIRECTIONS_STR[direction]))
        if not self.model.player: return True
        data = "#move {} {}".format(self.nickname, direction)
        self.socket.send(data.encode())
        return True

    def keyboard_drop_bomb(self):
        print("=> event \"keyboard drop bomb\"")
        if not self.model.player: return True
        data = "#bomb {}".format(self.nickname)
        self.socket.send(data.encode())
        return True

    # time event

    def tick(self, dt):
        demande, b, c = select.select([self.socket],[],[],1)
        for client in demande:
            if client == self.socket:
                co, addr = self.socket.accept()
            else:
                try:
                    data = self.socket.recv(1500)
                    try:
                        self.model = pickle.loads(data)
                        for char in self.model.characters:
                            if (char.nickname == self.nickname):
                                self.model.player = char
                    except EOFError:
                        return True;
                except socket.error:
                    return True
        return True
