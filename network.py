# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
import socket
import select

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
        self.str_fruits = []
        for fruit in self.model.fruits:
            self.str_fruits.append([fruit.pos, fruit.kind])
        self.str_character = []
        for fruit in self.model.characters:
            self.str_character.append([self.model.characters.pos, self.model.characters.kind])
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', port))
        self.s.listen(1)

    # time event

    def tick(self, dt):
        demande, b, c = select.select([self.s] + self.clients,[],[],1)
        for client in demande:
            if client == self.s:
                co, addr = self.s.accept()
                self.clients.append(co)
                data = self.map_name
                data = data.encode()
                co.send(data)
                data = co.recv(1500)
                data = data.decode()
                if data == "ok":
                    data = str(self.str_fruits)
                    data = data.encode()
                    co.send(data)
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
                    self.model.add_character(commands[1], isplayer = True)
        return True

################################################################################
#                          NETWORK CLIENT CONTROLLER                           #
################################################################################

class NetworkClientController:

    def __init__(self, host, port, nickname):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        data = self.socket.recv(1500)
        data = data.decode()
        self.model = Model()
        self.model.load_map(data)
        data = "ok"
        self.socket.send(data.encode())
        data = self.socket.recv(1500)
        data = data.decode()
        data = data[2:-2]
        fruits = data.split("], [")
        for fruit in fruits:
            fruit = fruit.replace("(", "")
            fruit = fruit.replace(")", "")
            fruit = fruit.replace(",", "")
            value_fruit = fruit.split(" ")
            dic ={}
            dic[X] = int(value_fruit[0])
            dic[Y] = int(value_fruit[1])

            self.model.add_fruit(int(value_fruit[2]), dic)


        data = "#nickname " + nickname
        self.socket.send(data.encode())

    # keyboard events

    def keyboard_quit(self):
        print("=> event \"quit\"")
        return False

    def keyboard_move_character(self, direction):
        print("=> event \"keyboard move direction\" {}".format(DIRECTIONS_STR[direction]))
        # ...
        return True

    def keyboard_drop_bomb(self):
        print("=> event \"keyboard drop bomb\"")
        # ...
        return True

    # time event

    def tick(self, dt):
        # ...
        return True
