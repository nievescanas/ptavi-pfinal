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
        ip_server = self.xml_dicc['uaserver']['ip']
        username = self.xml_dicc['account']['username']
        puerto_rtp = self.xml_dicc['rtpaudio']['puerto']
        reg_ip = self.xml_dicc['regproxy']['ip']
        reg_puerto = self.xml_dicc['regproxy']['puerto']

        if sys.argv[2] == 'INVITE':
            newline = sys.argv[2] + ' sip:' + sys.argv[3] + ' SIP/2.0\r\n'
            newline += 'Content-Type: application/sdp\r\n\r\n'
            newline += 'v=0\r\n'
            newline += 'o=' + username + ' ' + '192.168.56.1' + '\r\n'
            newline += 't=0\r\n'
            newline += 'm=audio ' + puerto_rtp + ' RTP\r\n'
        elif sys.argv[2] == 'REGISTER':
            newline = sys.argv[2] + ' sip:' + username + ip_server + 'SIP/2.0\r\n'
            newline += 'Expires: ' + sys.argv[3] + '\r\n'
        elif sys.argv[2] == 'BYE':
            newline = sys.argv[2] + ' sip:' + sys.argv[3] + 'SIP/2.0\r\n'

        return(newline)

if __name__ == "__main__":

    client = Uaclient()
    xml = client.confxml()
    ip_proxy = str(xml['regproxy']['ip'])
    puerto_proxy = int(xml['regproxy']['puerto'])

#Condicionamos la entrada de parámetros
    method = {'REGISTER', 'INVITE', 'BYE'}
    if int(len(sys.argv)) == 4:
        if not (path.exists(sys.argv[1]) and sys.argv[2] in method):
            sys.exit("Usage: python uaclient.py config method option")
    else:
        sys.exit("Usage: python uaclient.py config method option")

# Creamos el socket, lo configuramos, lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Conecta el socket en el puerto del servidor que esté escuchando
        my_socket.connect((ip_proxy, puerto_proxy))

        message = client.message_sip()
        my_socket.send(bytes(message, 'utf-8') + b'\r\n')
        date = time.strftime("%Y%m%d%H%M%S")

        #La cantidad máxima de datos que se recibirán a la vez: 1024 bytes
        try:
            data = my_socket.recv(1024)
        except(ConnectionResetError):
            sys.exit(date + ' Error: No server listening at ' + ip_proxy + ' port ' + str(puerto_proxy))

        # Condicionamos los mensajes ACK.
        if data.decode('utf-8') != '':
            message_serv = (data.decode('utf-8').split())
            if 'Trying'in message_serv and 'Ringing'in message_serv:
                if 'OK' in message_serv:
                    line = 'ACK' + ' sip:' + sys.argv[2]
                    line += ' SIP/2.0\r\n'
                my_socket.send(bytes(line, 'utf-8') + b'\r\n')
            elif '401' in message_serv:
                line = message
                line += 'Authorization: Digest response="154933336112"\r\n'
                my_socket.send(bytes(line, 'utf-8') + b'\r\n')
        print(data.decode('utf-8'))
