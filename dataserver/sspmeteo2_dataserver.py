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
import threading
import request
from datetime import datetime

class Datos:
    ahora = datetime.now()
    datos = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'

    @classmethod
    def es_cambio_de_dia(cls): #TODO comprobar cambio de dia  para el proximo intervalo ,estudiar esto
        este_momento = datetime.now()
        if este_momento.day != cls.ahora.day:
            respuesta = b'\x01'
        else:
            respuesta = b'\x00'
        cls.ahora = este_momento
        return respuesta

    @classmethod
    def salvar(cls):
        # Forma la estructura de directorios para los datos
        data_dir = cls.ahora.strftime('datos/%Y/%Y-%m/')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        fname = data_dir + cls.ahora.strftime('%Y-%m-%d.dat')
        with open(fname, 'a') as f:
           f.write(cls.ahora.strftime('%c, ') + cls.datos + '\n')

    @Classmethod
    def enviar_a_wunder(cls):
        url = 'https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
        try:
            v = [float(x) for x in cls.datos.split(', ')]
            params = {  'action':       'updateraw',
                        'ID':           'ICOMUNID54',
                        'PASSWORD':     'laura11',
                        'dateutc':      'now'
                        'tempf':        str(v[0] * 1.8 + 32),
                        'humidity':     str(v[2]),
                        'dewptf':       str(v[4] * 1.8 + 32),
                        'baromin':      str(v[5] * 0.0295299830714),
                        'dailyrainin':  str(v[6] / 25.4),
                        'rainin':       str(v[7] / 25.4),
                        'windspeedmph': str(v[8] * 0.621371192),
                        'windgustmph':  str(v[9] * 0.621371192),
                        'winddir':      str(int(v[10])) }
            respuesta = requests.get(url, params = params)
        except:
            return


def procesar():
    Datos.salvar()
    Datos.enviar_a_wunder()

class MiTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        req = self.request.recv(256).decode()
        if 'Q' in req:
            # Responde enviando el cambio de día
            self.request.sendall(es_cambio_de_dia())
            # Procesa los datos en otro thread
            Datos.datos = req.replace('Q','')
            threading.Thread(target=procesar).start()
        elif 'GET_DATOS' in req:
            self.request.sendall(Datos.datos.encode())

if __name__ == "__main__":
    Datos.ahora = datetime.now()
    HOST, PORT = "", 1234
    server = socketserver.TCPServer((HOST, PORT), MiTCPHandler)
    server.serve_forever()
