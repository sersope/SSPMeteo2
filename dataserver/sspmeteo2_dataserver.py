"""
  sspmeteo3_dataserver.py

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
import requests
from datetime import datetime, timedelta
import time
import json
from sspmeteo2_oled import SSPMeteoOled

class Wemos:

    KEYS = ['temp', 'temp2', 'humi', 'humi2', 'troc', 'pres', 'llud', 'lluh', 'vven', 'vrac','dven', 'wdog', 'errwif', 'errser', 'durcic']

    def __init__(self, periodo= 5):
        self.periodo = periodo      # Periodo de comunicacion en minutos
        self.hoy = datetime.now().day
        self.sdatos = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
        self.ddatos = {}

    def es_cambio_de_dia(self):
        dema = (datetime.now() + timedelta(minutes= self.periodo)).day
        if dema != self.hoy:
            respuesta = b'Y'
        else:
            respuesta = b'N'
        self.hoy = dema
        return respuesta

    def salvar(self):
        # Forma la estructura de directorios para los datos
        ahora = datetime.now()
        data_dir = ahora.strftime('datos/%Y/%Y-%m/')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        fname = data_dir + ahora.strftime('%Y-%m-%d.dat')
        with open(fname, 'a') as f:
           f.write(ahora.strftime('%c,') + self.sdatos + '\n')

    def enviar_a_wunder(self):
        url = 'https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
        try:
            params = {  'action':       'updateraw',
                        'ID':           'ICOMUNID54',
                        'PASSWORD':     'laura11',
                        'dateutc':      'now',
                        'tempf':        str(self.ddatos['temp'] * 1.8 + 32),
                        'humidity':     str(self.ddatos['humi']),
                        'dewptf':       str(self.ddatos['troc'] * 1.8 + 32),
                        'baromin':      str(self.ddatos['pres'] * 0.0295299830714),
                        'dailyrainin':  str(self.ddatos['llud'] / 25.4),
                        'rainin':       str(self.ddatos['lluh'] / 25.4),
                        'windspeedmph': str(self.ddatos['vven'] * 0.621371192),
                        'windgustmph':  str(self.ddatos['vrac'] * 0.621371192),
                        'winddir':      str(int(self.ddatos['dven'])) }
            respuesta = requests.get(url, params = params)
            if 'success' not in respuesta.text:
                print(datetime.now().strftime('%c'), 'Datos no envíados a Wunder')
                return False
        except:
            print(datetime.now().strftime('%c'), 'Excepción en envío a Wunder')
            return False
        return True

    def procesar(self, respuesta):
        saux = respuesta[1:-1]   # Quita 'I' inicial y 'F' final
        try:
            vals = [float(x) for x in saux.split(',')]
        except:
            print(datetime.now().strftime('%c'), 'Excepción en datos de la estación: No se pudo convertir a float', saux)
            return
        if len(vals) == len(Wemos.KEYS):
            self.sdatos = saux
            self.ddatos = dict(zip(Wemos.KEYS, vals))
            SSPMeteoOled.update(self.sdatos)
            self.salvar()
            self.enviar_a_wunder()
        else:
            print(datetime.now().strftime('%c'), 'Error en datos de la estación: Faltan valores', saux)


class MiServer(socketserver.TCPServer):
    def __init__(self, server_address, req_handler_class, wemos):
        socketserver.TCPServer.__init__(self, server_address, req_handler_class)
        self.wemos = wemos


class MiTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        respuesta = ''
        try:
            respuesta = self.request.recv(256).decode()
        except:
            respuesta = ''
        if len(respuesta) and respuesta[0] == 'I' and respuesta[-1] == 'F':
            # Responde enviando el cambio de día
            self.request.sendall(self.server.wemos.es_cambio_de_dia())
            # Procesa los datos en otro thread
            threading.Thread(target=self.server.wemos.procesar, args= (respuesta,)).start()
        elif 'GET_DATOS' in respuesta:
            self.request.sendall(self.server.wemos.sdatos.encode())
        elif 'GET_JSON' in respuesta:
            self.request.sendall(json.dumps(self.server.wemos.ddatos).encode())
        else:
            self.request.sendall('PERDON?'.encode())


if __name__ == "__main__":
    import locale
    locale.setlocale(locale.LC_ALL, '')
    SSPMeteoOled.begin()
    # Comunicacion con el Wemos
    wemos = Wemos(periodo= 1)
    # Arranca el servidor de datos
    HOST, PORT = "", 3069
    server = MiServer((HOST, PORT), MiTCPHandler, wemos)
    print(datetime.now().strftime('%c'), 'Info: Servidor arrancado')
    server.serve_forever()
