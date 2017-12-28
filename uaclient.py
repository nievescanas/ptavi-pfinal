#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""
import sys
import socket
import os.path as path
import time
import xml.etree.ElementTree as ET

class Uaclient():
    xml_dicc = {}
    try:
        path.exists(sys.argv[1])
    except IndexError:
        print("Usage: python3 uaclient.py config method option")

    def confxml(self):
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for child in root:
            self.xml_dicc[str(child.tag)] = child.attrib
        return(self.xml_dicc)

    def registerlog(self, acction='', message=''):
        date = time.strftime("%Y%m%d%H%M%S")
        dicc = self.xml_dicc['log']
        pathlog = dicc['path'] + "\log.txt"

        if path.exists(pathlog):
            with open(pathlog, "a") as log:
                log.write(date + acction + message + '\r\n')
        else:
            log = open(pathlog, 'w')
            log.write(date + " Starting..." + '\r\n')
            log.write(date + acction + message + '\r\n')

    def message_sip(self):
        self.confxml()
        uaserver = self.xml_dicc['uaserver']
        server_ip = uaserver['ip']
        account = self.xml_dicc['account']
        username = account['username']
        rtp_audio = self.xml_dicc['rtpaudio']
        puerto_rtp = rtp_audio['puerto']

        if sys.argv[2] == 'INVITE':
            newline = sys.argv[2] + ' sip:' + sys.argv[3] + ' SIP/2.0\r\n'
            newline += 'Content-Type: application/sdp\r\n\r\n'
            newline += 'v=0\r\n'
            newline += 'o=' + username + ' ' + '192.168.56.1' + '\r\n'
            newline += 't=0\r\n'
            newline += 'm=audio ' + puerto_rtp + ' RTP\r\n\r\n'
        elif sys.argv[2] == 'REGISTER':
            newline = sys.argv[2] + ' sip:' + username + ':5555' + 'SIP/2.0\r\n'
            newline += 'Expires: ' + sys.argv[3] + '\r\n\r\n'
        elif sys.argv[2] == 'BYE':
            newline = sys.argv[2] + ' sip:' + sys.argv[3] + 'SIP/2.0\r\n\r\n'

        return(newline)

if __name__ == "__main__":
# Creamos el socket, lo configuramos, lo atamos a un servidor/puerto

    client = Uaclient()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect(('192.168.56.1', 5555))

        message = client.message_sip()
        date = time.strftime("%Y%m%d%H%M%S")
        my_socket.send(bytes(message, 'utf-8'))

        # Conecta el socket en el puerto cuando el servidor esté escuchando
        data = my_socket.recv(1024)

        # Condicionamos los mensajes ACK.
        if data.decode('utf-8') != '':
            message_serv = (data.decode('utf-8').split())
            if 'Trying'in message_serv:
                if 'Ringing'in message_serv:
                    if 'OK' in message_serv:
                        line = 'ACK' + ' sip:'
                        line += sys.argv[2]
                        line += ' SIP/2.0\r\n'
                my_socket.send(bytes(line, 'utf-8') + b'\r\n')
        print(data.decode('utf-8'))
