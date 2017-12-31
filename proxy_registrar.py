
# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socketserver
import sys
import json
import os.path as path
import time
import socket
import xml.etree.ElementTree as ET


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    c_dicc = {}
    xml_dicc = {}
    usuario = ''
    passwd = ''

    def confxml(self):
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for child in root:
            self.xml_dicc[str(child.tag)] = child.attrib
        return self.xml_dicc

    def registerlog(self, acction='', ip='', puerto='', message=''):
        self.confxml()
        date = time.strftime("%Y%m%d%H%M%S")
        dicc = self.xml_dicc['log']
        pathlog = dicc['path'] + "\log_register.txt"

        if path.exists(pathlog):
            with open(pathlog, "a") as log:
                log.write(date + acction + ip + ':' + puerto + ': ' + message + '\r\n')
        else:
            log = open(pathlog, 'w')
            log.write(date + " Starting..." + '\r\n')
            log.write(date + acction + message + '\r\n')
    """
    Comprueba si existe el fichero y lo utiliza como diccionario
    """
    def json2registered(self):
        if path.exists('registered.json'):
            with open('registered.json') as d_file:
                data = json.load(d_file)
                self.c_dicc = data
    """
    Crea y escribe un fichero json
    """

    def register2json(self, name='registered.json'):
        with open(name, 'w') as outfile:
            json.dump(self.c_dicc, outfile, separators=(',', ':'), indent="")
    """
    Comprueba y borra los usuarios caducados
    """

    def caducidad(self):
        tmp_list = []
        for usuario in self.c_dicc:
            caducidad = self.c_dicc[usuario][2]
            now = time.ctime(time.time())
            if caducidad <= now:
                tmp_list.append(usuario)
        for usuario in tmp_list:
            del self.c_dicc[usuario]

    def connection_serv(self, correo='', message=''):
        print('reenviando')
        ip_server = self.c_dicc[correo][0]
        port_server = self.c_dicc[correo][1]
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        my_socket.connect((ip_server, int(port_server)))
        my_socket.send(bytes(message, 'utf-8') + b'')

        data = my_socket.recv(1024)
        new_message = ''
        message_serv = (data.decode('utf-8').split())
        if 'Trying' in message_serv and 'Ringing' in message_serv:
            if 'OK' in message_serv:
                new_message = data.decode('utf-8')
        elif 'OK' in message_serv:
            new_message = data.decode('utf-8')
        return(new_message)

    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        newline = ''
        message = ''
        if not self.c_dicc:
            self.json2registered()
        for line in self.rfile:
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                message += line.decode('utf-8')

        metodo = message.split()
        print(metodo)
        message = str(message)
        metodos = ['INVITE', 'ACK', 'BYE']
        puerto_client = ''
        ip_client = self.client_address[0]
        self.caducidad()

        if metodo[0] == 'REGISTER' and not 'Authorization:' in metodo:
            newline = 'SIP/2.0 401 Unauthorizad\r\n'
            newline += 'WWW Authenticate: Digest nonce="56321684"\r\n'
            self.passwd = 'falta'

        elif metodo[0] == 'REGISTER' and 'Authorization:' in metodo:
            self.usuario = metodo[1][metodo[1].find(':')+1:metodo[1].rfind(':')]
            puerto_client = metodo[1][metodo[1].rfind(':') + 1:]
            newline = 'SIP/2.0 200 OK\r\n'
            self.passwd = metodo[7][metodo[7].find('"')+1:metodo[7].rfind(':')]

            self.passwd = 'correcta'

        elif metodo[0] in metodos:
            correo_serv = metodo[1][metodo[1].rfind(':')+1:]
            if correo_serv in self.c_dicc:
                newline = self.connection_serv(correo_serv, message)
            else:
                newline = 'SIP/2.0 404 User Not Found\r\n'

        if 'Expires:' in metodo and self.passwd == 'correcta':
            if metodo[4] > '0':
                caducidad = time.ctime(time.time() + int(metodo[4]))
                info = [ip_client, puerto_client, caducidad]
                self.c_dicc[self.usuario] = info
            elif metodo[4] == '0':
                if self.usuario in self.c_dicc:
                    del self.c_dicc[self.usuario]

        self.register2json()
        #self.registerlog(' Received from ', str(ip_client), str(puerto_client), line.decode('utf-8'))
        self.wfile.write(bytes(str(newline), ' utf-8 ') + b'\r\n')
        #self.registerlog(' Sent to ', str(ip_client), str(puerto_client), str(newline))



if __name__ == "__main__":

    if int(len(sys.argv)) == 2 and path.exists(sys.argv[1]):
            print('Server MiServidorBigBang listening at port 5555...')
    else:
        sys.exit('Usage: python proxy_registrar.py config')

    serv = socketserver.UDPServer(('', 5555), SIPRegisterHandler)

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
