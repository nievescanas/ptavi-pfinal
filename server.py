#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import os
import socketserver
from uaclient import Uaclient

class EchoHandler(socketserver.DatagramRequestHandler, Uaclient):

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
            # Leyendo línea a línea lo que nos envía el cliente
        self.confxml()
        for line in self.rfile:
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                print(line.decode('utf-8'))
                message = line.decode('utf-8')[:line.decode('utf-8').rfind('\r')]
                self.registerlog(' Received from ', message)

                messagelist = (line.decode('utf-8').split())
                newline = ''
                if messagelist[0] == 'INVITE':
                    newline = 'SIP/2.0 ' + '100 ' + 'Trying'
                    self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
                    self.registerlog(' Sent to ', newline)
                    newline = 'SIP/2.0 ' + '180 ' + 'Ringing'
                    self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
                    self.registerlog(' Sent to ', newline)
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
                self.registerlog(' Sent to ', newline)


if __name__ == "__main__":

    serv = socketserver.UDPServer(('', 5555), EchoHandler)

    # Creamos servidor de eco y escuchamos
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
