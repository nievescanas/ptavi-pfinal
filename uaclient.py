#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""
import sys
import os
import socket
import os.path as path
import time
import xml.etree.ElementTree as ET


class Uaclient:
    xml_dicc = {}
    """
    Envia rtp
    """
    def rtp_shipment(self, ip='', port='', name=''):
        aEjecutar = './mp32rtp -i ' + ip + ' -p ' + port
        aEjecutar += ' < ' + 'cancion.mp3'
        os.system(aEjecutar)

    """
    Lee ficheros xml y guarda la informacion en un diccionario
    """
    def confxml(self):
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for child in root:
            self.xml_dicc[str(child.tag)] = child.attrib
        return self.xml_dicc

    """
    Registra lo que sucede en log.txt
    """
    def registerlog(self, acction='', ip='', puerto='', message=''):
        date = time.strftime("%Y%m%d%H%M%S")
        dicc = self.xml_dicc['log']
        pathlog = dicc['path'] + "\log.txt"
        message = message.split('\r\n')
        message = ' '.join(message)
        if path.exists(pathlog):
            with open(pathlog, "a") as log:
                if acction != ' Sent to ' and acction != ' Received from ':
                    log.write(date + ' ' + acction + message + '\r\n')
                else:
                    log.write(date + acction + ip + ':' + puerto + ': ' + message + '[...]' + '\r\n')
        else:
            log = open(pathlog, 'w')
            if acction == ' Starting...':
                log.write(date + acction + '\r\n')
            else:
                log.write(date + acction + ip + ':' + puerto + ': ' + message + '[...]' + '\r\n')

    # Contruye mensaje sip
    def message_sip(self):
        newline = ''
        self.confxml()
        puerto_server = self.xml_dicc['uaserver']['puerto']
        username = self.xml_dicc['account']['username']
        puerto_rtp = self.xml_dicc['rtpaudio']['puerto']

        if sys.argv[2] == 'INVITE':
            newline = sys.argv[2] + ' sip:' + sys.argv[3] + ' SIP/2.0\r\n'
            newline += 'Content-Type: application/sdp\r\n\r\n'
            newline += 'v=0\r\n'
            newline += 'o=' + username + ' ' + '192.168.56.1' + '\r\n'
            newline += 't=0\r\n'
            newline += 'm=audio ' + puerto_rtp + ' RTP\r\n'
        elif sys.argv[2] == 'REGISTER':
            newline = sys.argv[2] + ' sip:' + username + ':' + puerto_server + ' SIP/2.0\r\n'
            newline += 'Expires: ' + sys.argv[3] + '\r\n'

        elif sys.argv[2] == 'BYE':
            newline = sys.argv[2] + ' sip:' + sys.argv[3] + ' SIP/2.0\r\n'
        return newline


if __name__ == "__main__":
    # Condiciona la entrada de parámetros
    method = {'REGISTER', 'INVITE', 'BYE'}
    if int(len(sys.argv)) == 4:
        if not (path.exists(sys.argv[1]) and sys.argv[2] in method):
            sys.exit("Usage: python uaclient.py config method option")
    else:
        sys.exit("Usage: python uaclient.py config method option")

    client = Uaclient()
    xml = client.confxml()
    ip_proxy = str(xml['regproxy']['ip'])
    puerto_proxy = int(xml['regproxy']['puerto'])
    passwd = xml['account']['passwd']

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        # Conecta el socket en el puerto del servidor que esté escuchando
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip_proxy, puerto_proxy))
        message = client.message_sip()
        my_socket.send(bytes(message, 'utf-8') + b'\r\n')
        date = time.strftime("%Y%m%d%H%M%S")
        client.registerlog(' Sent to ', ip_proxy, str(puerto_proxy), message)

        # Escucha, construye y envia los mensajes
        try:
            data = my_socket.recv(puerto_proxy)
            if data.decode('utf-8') != '':
                line = ''
                message_serv = (data.decode('utf-8').split())
                client.registerlog(' Received from ', ip_proxy, str(puerto_proxy), data.decode('utf-8'))
                if 'Trying'in message_serv and 'Ringing'in message_serv:
                    if 'OK' in message_serv:
                        line = 'ACK' + ' sip:' + sys.argv[3]
                        line += ' SIP/2.0\r\n'
                    client.registerlog(' Sent to ', ip_proxy, str(puerto_proxy), line)
                    my_socket.send(bytes(line, 'utf-8') + b'\r\n')
                    # Envio rtp
                    ip_server = message_serv[13]
                    port_rtp = message_serv[16]
                    audio_path = str(xml['audio']['path'])
                    client.rtp_shipment(ip_server, port_rtp)
                    client.registerlog(' Sent to ', ip_server, str(port_rtp), 'RTP')
                elif '401' in message_serv:
                    line = message
                    line += 'Authorization: Digest response=' + passwd + '\r\n'
                    client.registerlog(' Sent to ', ip_proxy, str(puerto_proxy), line)
                    my_socket.send(bytes(line, 'utf-8') + b'\r\n')
                    data = my_socket.recv(puerto_proxy)
            print(data.decode('utf-8'))
        except ConnectionResetError:
            date = time.strftime("%Y%m%d%H%M%S")
            line = 'Error: No server listening at ' + ip_proxy + ' port ' + str(puerto_proxy)
            client.registerlog(line)
            sys.exit(line)