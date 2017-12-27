#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import os
import os.path as path
import socketserver
import sys
import xml.etree.ElementTree as ET


class EchoHandler(socketserver.DatagramRequestHandler):
    xml_dicc = {}

    def confxml(self):
        tree = ET.parse('ua1.xml')
        root = tree.getroot()
        for child in root:
            self.xml_dicc[str(child.tag)] = child.attrib
        return (self.xml_dicc)

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
            # Leyendo línea a línea lo que nos envía el cliente

        self.confxml()
        for line in self.rfile:
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                print(line.decode('utf-8'))
                messagelist = (line.decode('utf-8').split())
                newline = ''
                if messagelist[0] == 'INVITE':
                    newline = 'SIP/2.0 ' + '100 ' + 'Trying'
                    self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
                    newline = 'SIP/2.0 ' + '180 ' + 'Ringing'
                    self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')
                    newline = 'SIP/2.0 ' + '200 ' + 'OK'
                elif messagelist[0] == 'BYE':
                    newline = 'SIP/2.0 ' + '200 ' + 'OK'
                elif messagelist[0] == 'ACK':
                    rtp = 'mp32rtp -i 127.0.0.1 -p 23032 < ' + sys.argv[3]
                    os.system(rtp)
                elif messagelist[0] != ('INVITE' and 'BYE'):
                    newline = 'SIP/2.0 ' + '405 ' + 'Method Not Allowed'
                elif messagelist[2] != 'SIP/2.0':
                    newline = 'SIP/2.0 ' + '400 ' + ' Bad Request'

                self.wfile.write(bytes(newline, 'utf-8') + b'\r\n\r\n')


if __name__ == "__main__":

    serv = socketserver.UDPServer(('', int(sys.argv[2])), EchoHandler)
    # Errores: Entrada de linea de comandos.
    try:
        if path.exists(sys.argv[3]) and len(sys.argv) == 4:
            print("Starting...")
        else:
            raise IndexError
    except IndexError:
        sys.exit("Usage: python3 server.py IP port audio_file")
    # Creamos servidor de eco y escuchamos
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
