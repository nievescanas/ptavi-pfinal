
#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socketserver
import sys
import json
import os.path as path
import time
import xml.etree.ElementTree as ET


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    c_dicc = {}
    xml_dicc = {}
    def confxml(self):
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        for child in root:
            self.xml_dicc[str(child.tag)] = child.attrib
        return(self.xml_dicc)

    def registerlog(self, acction='', message=''):
        self.confxml()
        date = time.strftime("%Y%m%d%H%M%S")
        dicc = self.xml_dicc['log']
        pathlog = dicc['path'] + "\log_register.txt"

        if path.exists(pathlog):
            with open(pathlog, "a") as log:
                log.write(date + acction + message + '\r\n')
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
            caducidad = self.c_dicc[usuario][1]
            now = time.ctime(time.time())
            if caducidad <= now:
                tmp_list.append(usuario)
        for usuario in tmp_list:
            del self.c_dicc[usuario]

    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        if not self.c_dicc:
            self.json2registered()
        for line in self.rfile:
            if not line or line.decode('utf-8') == "\r\n":
                continue
            else:
                metodo = (line.decode('utf-8').split())
                print(line.decode('utf-8'))
                ip = self.client_address[0]
                self.caducidad()

                if metodo[0] == 'REGISTER':
                    correo = metodo[1][metodo[1].rfind(':')+1:]
                    newline = 'SIP/2.0 401 Unauthorizad\r\n'
                    newline += 'WWW Authenticate: Digest nonce="56321684"\r\n\r\n'

                elif metodo[0] == 'Expires:':
                    if metodo[1] > '0':
                        caducidad = time.ctime(time.time() + int(metodo[1]))
                        info = [ip, caducidad]
                        self.c_dicc[correo] = info

                    elif metodo[1] == '0':
                        if correo in self.c_dicc:
                            del self.c_dicc[correo]
                elif 'Authorization' in metodo:
                    newline = 'SIP/2.0 200 OK\r\n\r\n'

                self.register2json()
        self.wfile.write(bytes(str(newline), ' utf-8 '))
        self.registerlog(' Received from ', str(newline))


        print(self.client_address)


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