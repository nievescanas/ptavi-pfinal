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
    puerto_client = ''

    """
    Lee y guarda en un diccionario el fichero indicado por parámetro
    """
    def confxml(self):
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for child in root:
            self.xml_dicc[str(child.tag)] = child.attrib
        return self.xml_dicc

    """
    Registra en un fichero txt la entrada y salida de mensajes
    """
    def registerlog(self, acction='', ip='', puerto='', message=''):
        self.confxml()
        date = time.strftime("%Y%m%d%H%M%S")
        pathlog = self.xml_dicc['log']['path'] + "\log_registrar.txt"
        message = message.split('\r\n')[0]
        if path.exists(pathlog):
            with open(pathlog, "a") as log:
                if acction != ' Sent to ' and acction != ' Received from ':
                    log.write(date + acction + message + '\r\n')
                else:
                    log.write(date + acction + ip + ':' + puerto + ': ' + message + '[...]' + '\r\n')
        else:
            log = open(pathlog, 'w')
            if acction == ' Starting...':
                log.write(date + acction + '\r\n')
            else:
                log.write(date + acction + ip + ':' + puerto + ': ' + message + '[...]' + '\r\n')

    """
    Lee y comprueba las contraseñas
    """
    def register_passwd(self, passwd=''):
        path_passwd = self.xml_dicc['database']['passwdpath']
        if path.exists(path_passwd):
            with open(path_passwd) as d_file:
                data = json.load(d_file)
                self.passwd_dicc = data
        if passwd in self.passwd_dicc[self.usuario]:
            passwd = 'correcta'
        else:
            passwd = 'falsa'
        return passwd

    """
    Comprueba si existe el fichero y lo utiliza como diccionario
    """
    def json2registered(self):
        path_register = self.xml_dicc['database']['path'] + "\client_registrar.json"
        if path.exists(path_register):
            with open(path_register) as d_file:
                data = json.load(d_file)
                self.c_dicc = data

    """
    Crea y escribe un fichero json
    """
    def register2json(self, name='\client_registrar.json'):
        path_register = self.xml_dicc['database']['path'] + name
        with open(path_register, 'w') as outfile:
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

    """
    Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    """
    def connection_serv(self, correo='', message=''):
        date = time.strftime("%Y%m%d%H%M%S")
        ip_server = self.c_dicc[correo][0]
        port_server = self.c_dicc[correo][1]
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip_server, int(port_server)))
        my_socket.send(bytes(message, 'utf-8') + b'')
        self.registerlog(' Sent to ', str(ip_server), port_server, message)

        # Escucha y devuelve el mensaje
        try:
            data = my_socket.recv(1024)
            if data.decode('utf-8') != '':
                self.registerlog(' Received from ', ip_server, port_server, data.decode('utf-8'))
            new_message = ''
            message_serv = (data.decode('utf-8').split())
            if 'Trying' in message_serv and 'Ringing' in message_serv:
                if 'OK' in message_serv:
                    new_message = data.decode('utf-8')
            elif 'OK' in message_serv:
                new_message = data.decode('utf-8')
            return new_message
        except ConnectionResetError:
            return date + ' Error: No server listening at ' + ip_server + ' port ' + str(port_server)

    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        newline = ''
        message = ''
        mensaje_reenvio = ''
        metodos = ['INVITE', 'ACK', 'BYE']
        self.confxml()
        if not self.c_dicc:
            self.json2registered()
        for line in self.rfile:
            mensaje_reenvio += line.decode('utf-8')
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                message += line.decode('utf-8')

        metodo = message.split()
        ip_client = self.client_address[0]
        self.caducidad()

        if metodo[0] == 'REGISTER' and 'Authorization:' in metodo:
            self.usuario = metodo[1][metodo[1].find(':')+1:metodo[1].rfind(':')]
            self.puerto_client = metodo[1][metodo[1].rfind(':') + 1:]
            passwd = metodo[7][metodo[7].find('=')+1:]
            self.passwd = self.register_passwd(passwd)
            newline = 'SIP/2.0 200 OK\r\n'
            self.registerlog(' Received from ', str(ip_client), self.puerto_client, message)
            self.registerlog(' Sent to ', str(ip_client), self.puerto_client, str(newline))

        elif not('Authorization:' in metodo) and metodo[0] == 'REGISTER':
            self.puerto_client = metodo[1][metodo[1].rfind(':') + 1:]
            newline = 'SIP/2.0 401 Unauthorized\r\n'
            newline += 'WWW Authenticate: Digest nonce="56321684"\r\n'
            self.passwd = 'falta'
            self.registerlog(' Received from ', str(ip_client), self.puerto_client, message)
            self.registerlog(' Sent to ', str(ip_client), self.puerto_client, str(newline))

        if metodo[0] in metodos:
            correo_serv = metodo[1][metodo[1].rfind(':')+1:]
            self.registerlog(' Received from ', str(ip_client), str(self.client_address[1]), message)
            if correo_serv in self.c_dicc:
                newline = self.connection_serv(correo_serv, mensaje_reenvio)
            else:
                newline = 'SIP/2.0 404 User Not Found\r\n'
                self.registerlog(' Sent to ', str(ip_client), str(self.client_address[1]), str(newline))

        if 'Expires:' in metodo and self.passwd == 'correcta':
            if metodo[4] > '0':
                caducidad = time.ctime(time.time() + int(metodo[4]))
                info = [ip_client, self.puerto_client, caducidad]
                self.c_dicc[self.usuario] = info
            elif metodo[4] == '0':
                if self.usuario in self.c_dicc:
                    del self.c_dicc[self.usuario]
        self.register2json()
        if newline != '':
            self.registerlog(' Sent to ', str(ip_client), str(self.client_address[1]), newline)
            self.wfile.write(bytes(str(newline), ' utf-8 ') + b'\r\n')


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
