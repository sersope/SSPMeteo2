"""
  sspmeteo2

  The MIT License (MIT)

  Copyright (c) 2016 Sergio Soriano Peiró

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
"""

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
