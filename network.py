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
        self.account = []
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
                data = client.recv(10000)
                data = data.decode()
                commands = data.split(" ")
                if not data:
                    character = None
                    for char in self.model.characters:
                        if char.nickname == self.nick_to_client[client]:
                            character = char
                    exist = False
                    for account in self.account:
                        nick,cli,char = account
                        if nick == self.nick_to_client[client]:
                            exist = True
                    if not exist:
                        self.account.append([self.nick_to_client[client], client, character])
                    action = ["#del", self.model.characters]
                    if character != None:
                        self.model.kill_character(self.nick_to_client[client])
                    self.clients.remove(client)
                    del self.nick_to_client[client]
                    self.send_all(self.clients,pickle.dumps(action))
                if (commands[0] == "#nickname"):
                    exist = False
                    for character in self.model.characters:
                        if character.nickname == commands[1]:
                            exist = True
                    if not exist:
                        found = False
                        for account in self.account:
                            nick,cli,char = account
                            print(char)
                            if nick == commands[1]:
                                if char != None:
                                    self.model.characters.append(char)
                                self.nick_to_client[client] = commands[1]
                                action = ["#add", self.model.characters, self.model.map, self.model.fruits, self.model.bombs]
                                self.send_all(self.clients,pickle.dumps(action))
                                found = True
                    else:
                        found = True
                    if not found:
                        self.nick_to_client[client] = commands[1]
                        self.model.add_character(commands[1], isplayer = False)
                        action = ["#add", self.model.characters, self.model.map, self.model.fruits, self.model.bombs]
                        self.send_all(self.clients,pickle.dumps(action))
                    if exist and found:
                        self.clients.remove(client)
                        client.close()
                if (commands[0] == "#die"):
                    for character in self.model.characters:
                        if character.nickname == commands[1]:
                            self.model.kill_character(commands[1])
                    if (self.model.characters == []):
                        for player in self.clients:
                            self.model.add_character(self.nick_to_client[player], isplayer = False)
                        self.model.load_map(self.map_name)
                        self.model.fruits = []
                        self.model.bombs = []
                        print(self.model.map)
                        for i in range(10): self.model.add_fruit()
                        action = ["#rematch", self.model.characters, self.model.map, self.model.fruits, self.model.bombs]
                        self.send_all(self.clients,pickle.dumps(action))
                    if len(self.model.characters) == 1:
                        character = self.model.characters[0]
                        cli = None
                        for client in self.clients:
                            if character.nickname == self.nick_to_client[client]:
                                cli = client
                        if cli != None:
                            action = ["#winner", "You can be proud of you because you beat all players GG, YOU WIN , if you want to restart with your friends kill yourself"]
                            cli.send(pickle.dumps(action))
                if (commands[0] == "#give_me_map"):
                    data = pickle.dumps(self.model)
                    client.send(data)
                if (commands[0] == "#move"):
                    action = ["#move", self.model.characters]
                    self.model.move_character(commands[1], int(commands[2]))
                    self.send_all(self.clients,pickle.dumps(action))
                if (commands[0] == "#bomb"):
                    self.model.drop_bomb(commands[1])
                    action = ["#bomb", self.model.bombs]
                    self.send_all(self.clients,pickle.dumps(action))
        return True

################################################################################
#                          NETWORK CLIENT CONTROLLER                           #
################################################################################

class NetworkClientController:

    def __init__(self, host, port, nickname):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.model = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        data = "#nickname " + nickname
        self.socket.send(data.encode())
        data = self.socket.recv(10000)
        if not data:
            self.socket.close()
            self.socket = None
            print("Pseudo already exist")
        else:
            data = pickle.loads(data)
            if data[0] == "#add":
                self.model = Model(self)
                self.model.map = data[2]
                self.model.characters = data[1]
                self.model.fruits = data[3]
                self.model.bombs = data[4]
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

    #call when you die
    def die(self):
        print("We are sorry you loose.....")
        data = "#die " + self.nickname
        self.socket.send(data.encode())

    # time event
    def tick(self, dt):
        if self.socket == None:
            return False
        self.socket.setblocking(0)
        try:
            data = self.socket.recv(10000)
            if not data:
                print("Server error, bye bye")
                return False
            try:
                data = pickle.loads(data)
                if data[0] == "#bomb":
                    self.model.bombs = data[1]
                if data[0] == "#move" or data[0] == "#add" or data[0] == "#del" or data[0] == "#rematch":
                    self.model.characters = data[1]
                if data[0] == "#rematch":
                    self.model.map = data[2]
                    self.model.fruits = data[3]
                    self.model.bombs = data[4]
                if data[0] == "#winner":
                    print(data[1])
                for char in self.model.characters:
                    if (char.nickname == self.nickname):
                        self.model.player = char
            except EOFError:
                return True;
        except socket.error:
            return True
        return True
