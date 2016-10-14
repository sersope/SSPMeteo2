import os
import socketserver
from datetime import datetime
#~ from sspmeteo2_oled import SSPMeteoOled

class Datos:

    datos = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'

    @classmethod
    def salvaDatos(cls, datos):
        cls.datos = datos
        # Forma la estructura de directorios para los datos
        a = datetime.now()
        data_dir = a.strftime('datos/%Y/%Y-%m/')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        fname = data_dir + a.strftime('%Y-%m-%d.dat')
        with open(fname, 'a') as f:
           f.write(a.strftime('%c, ') + cls.datos + '\n')

class MiTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        req = self.request.recv(256).decode()
        if 'Q' in req:
            datos = req.replace('Q','')
            Datos.salvaDatos(datos)
            #~ SSPMeteoOled.update(datos)
        elif 'GET_DATOS' in req:
            self.request.sendall(Datos.datos.encode())

if __name__ == "__main__":
    #~ SSPMeteoOled.begin()
    HOST, PORT = "", 1234
    server = socketserver.TCPServer((HOST, PORT), MiTCPHandler)
    server.serve_forever()
