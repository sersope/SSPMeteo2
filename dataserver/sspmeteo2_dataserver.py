import socketserver
from sspmeteo2_oled import SSPMeteoOled
from datetime import datetime

class Datos:
    datos = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'

    @classmethod
    def salvaDatos(cls, datos):
        cls.datos = datos
        a = datetime.now()
        fname = a.strftime('datos/%Y-%m-%d.dat')
        with open(fname, 'a') as f:
           f.write(a.strftime('%c, ') + cls.datos + '\n')

class MiTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        req = self.request.recv(256).decode()
        if 'Q' in req:
            datos = req.replace('Q','')
            Datos.salvaDatos(datos)
            SSPMeteoOled.update(datos)
        elif 'GET_DATOS' in req:
            self.request.sendall(Datos.datos.encode())

if __name__ == "__main__":
    SSPMeteoOled.begin()
    HOST, PORT = "", 1234
    server = socketserver.TCPServer((HOST, PORT), MiTCPHandler)
    server.serve_forever()
