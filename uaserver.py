#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os.path as path
from uaclient import Uaclient


class Uaserver(Uaclient):
    # Iniciamos, leemos y guardamos la informacion del xml
    def data_server(self):
        self.confxml()


class EchoHandler(socketserver.DatagramRequestHandler, Uaserver):
    info_client = {}

    def handle(self):
        # Guarda los datos de interes en variables
        xml = self.confxml()
        client_ip = str(self.client_address[0])
        client_puerto = str(self.client_address[1])
        reg_puerto = xml['regproxy']['puerto']
        reg_ip = xml['regproxy']['ip']
        message = ''

        # Read line by line message
        for line in self.rfile:
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                message += line.decode('utf-8')
        # Registry log.txt
        self.registerlog(' Received from ', client_ip, client_puerto, message)

        # Build the answer
        messagelist = (message.split())
        newline = ''
        if messagelist[0] == 'INVITE':
            self.info_client[messagelist[7]] = messagelist[10]
            newline = 'SIP/2.0 ' + '100 ' + 'Trying'
            self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
            self.registerlog(' Sent to ', reg_ip, reg_puerto, newline)
            newline = 'SIP/2.0 ' + '180 ' + 'Ringing'
            self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
            self.registerlog(' Sent to ', reg_ip, reg_puerto, newline)
            newline = 'SIP/2.0 ' + '200 ' + 'OK' + '\r\n'
            newline += 'Content-Type: application/sdp\r\n\r\n'
            newline += 'v=0\r\n'
            newline += 'o=' + xml['account']['username'] + ' ' + '192.168.56.1' + '\r\n'
            newline += 't=0\r\n'
            newline += 'm=audio ' + xml['rtpaudio']['puerto'] + ' RTP'
        elif messagelist[0] == 'BYE':
            newline = 'SIP/2.0 ' + '200 ' + 'OK'
        elif messagelist[0] == 'ACK':
            name_fich = str(xml['audio']['path'][:xml['audio']['path'].rfind('/')])
            port_rtp = self.info_client[self.client_address[0]]
            self.rtp_shipment(self.client_address[0], port_rtp)
            self.registerlog(' Sent to ', self.client_address[0], port_rtp, 'RTP')
        elif messagelist[0] != ('INVITE' and 'BYE'):
            newline = 'SIP/2.0 ' + '405 ' + 'Method Not Allowed'
        elif messagelist[2] != 'SIP/2.0':
            newline = 'SIP/2.0 ' + '400 ' + ' Bad Request'

        # Send answer and Registry log.txt
        if newline != '':
            self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
            self.registerlog(' Sent to ', reg_ip, reg_puerto, newline)


if __name__ == "__main__":
    server = Uaserver()
    xml = server.confxml()
    # Verificamos datos de entrada
    if int(len(sys.argv)) == 2 and path.exists(sys.argv[1]):
            print('Listening...')
            server.registerlog(' Starting...')
    else:
        sys.exit('Usage: python uaserver.py config')
    puerto_server = int(xml['uaserver']['puerto'])

    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer(('', puerto_server), EchoHandler)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        server.registerlog(' Finishing. ')
        print("Finalizado servidor")
