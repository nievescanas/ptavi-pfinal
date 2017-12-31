#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import os
import socketserver
import sys
import os.path as path
from uaclient import Uaclient

class Uaserver(Uaclient):
    def datos(self):
        self.confxml()

class EchoHandler(socketserver.DatagramRequestHandler, Uaserver):

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
            # Leyendo línea a línea lo que nos envía el cliente

        xml = self.confxml()
        client_ip = str(self.client_address[0])
        client_puerto = str(self.client_address[1])
        reg_puerto = xml['regproxy']['puerto']
        reg_ip = xml['regproxy']['ip']
        message = ''
        for line in self.rfile:
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                message += line.decode('utf-8')

        print(message)
        message_log = message[message.rfind('\r')]
        self.registerlog(' Received from ', client_ip, client_puerto, message_log)

        messagelist = (message.split())
        newline = ''
        if messagelist[0] == 'INVITE':
            newline = 'SIP/2.0 ' + '100 ' + 'Trying'
            self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
            self.registerlog(' Sent to ', reg_ip, reg_puerto, newline)
            newline = 'SIP/2.0 ' + '180 ' + 'Ringing'
            self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
            self.registerlog(' Sent to ', reg_ip, reg_puerto, newline)
            newline = 'SIP/2.0 ' + '200 ' + 'OK'
        elif messagelist[0] == 'BYE':
            newline = 'SIP/2.0 ' + '200 ' + 'OK'
        elif messagelist[0] == 'ACK':
            rtp = 'mp32rtp -i 127.0.0.1 -p 23032 < '
            os.system(rtp)
            self.registerlog(' Sent to ', 'rtp')
        elif messagelist[0] != ('INVITE' and 'BYE'):
            newline = 'SIP/2.0 ' + '405 ' + 'Method Not Allowed'
        elif messagelist[2] != 'SIP/2.0':
            newline = 'SIP/2.0 ' + '400 ' + ' Bad Request'

        self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
        self.registerlog(' Sent to ', reg_ip, reg_puerto, newline)


if __name__ == "__main__":

    server = Uaserver()
    xml = server.confxml()
    puerto_server = int(xml['uaserver']['puerto'])

    if int(len(sys.argv)) == 2 and path.exists(sys.argv[1]):
            print('Listening...')
            server.registerlog(' Starting...')
    else:
        sys.exit('Usage: python uaserver.py config')

    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer(('', puerto_server), EchoHandler)

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
