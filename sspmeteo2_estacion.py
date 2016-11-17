"""
  sspmeteo2_estacion.py

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
import sys
import requests
import threading
import time
import socket
from datetime import datetime, timedelta
import logging

oled = True
try:
    from sspmeteo2_oled import SSPMeteoOled
except:
    oled = False

class Estacion:

    KEYS = ['temp', 'temp2', 'humi', 'humi2', 'troc', 'pres', 'llud', 'lluh', 'vven', 'vrac','dven', 'uptime', 'errwif', 'errser', 'durcic']

    def __init__(self, periodo= 5):
        self.periodo = periodo          # Periodo de comunicacion en minutos de la estacion
        self.hoy = datetime.now().day
        self.watchdog = 0               # Vigila que la estación esté activa
        self.uptime_ant = 0
        # Inicializacion de datos
        lceros = ['0' for k in Estacion.KEYS]
        self.sdatos = ','.join(lceros)
        self.ddatos = dict(zip(Estacion.KEYS, lceros))
        self.datos_disponibles= False
        # Pantalla Oled
        if oled:
            SSPMeteoOled.begin()
        else:
            logging.info('Sin pantalla OLED.')

    def es_cambio_de_dia(self):
        dema = (datetime.now() + timedelta(minutes= 2 * self.periodo)).day
        if dema != self.hoy:
            respuesta = b'Y'
        else:
            respuesta = b'N'
        self.hoy = dema
        return respuesta

    def salvar_datos(self):
        # Forma la estructura de directorios para los datos
        ahora = datetime.now()
        data_dir = ahora.strftime('datos/%Y/%Y-%m/')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        fname = data_dir + ahora.strftime('%Y-%m-%d.dat')
        with open(fname, 'a') as f:
           f.write(ahora.strftime('%c,') + self.sdatos + '\n')

    def enviar_datos_a_wunder(self):
        url = 'https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
        try:
            params = {  'action':       'updateraw',
                        'ID':           'ICOMUNID54',
                        'PASSWORD':     'laura11',
                        'dateutc':      'now',
                        'tempf':        str(float(self.ddatos['temp']) * 1.8 + 32),
                        'humidity':     str(self.ddatos['humi']),
                        'dewptf':       str(float(self.ddatos['troc']) * 1.8 + 32),
                        'baromin':      str(float(self.ddatos['pres']) * 0.0295299830714),
                        'dailyrainin':  str(float(self.ddatos['llud']) / 25.4),
                        'rainin':       str(float(self.ddatos['lluh']) / 25.4),
                        'windspeedmph': str(float(self.ddatos['vven']) * 0.621371192),
                        'windgustmph':  str(float(self.ddatos['vrac']) * 0.621371192),
                        'winddir':      str(self.ddatos['dven']) }
            logging.disable(logging.INFO)
            respuesta = requests.get(url, params = params)
            logging.disable(logging.NOTSET)
            if 'success' not in respuesta.text:
                logging.warning('Datos no recibidos en Wunder.')
                return False
        except:
            logging.exception('Excepción: Error en envío a Wunder.')
            return False
        return True

    def run(self):
        threading.Thread(target= self.run_minutero).start()
        try:
            server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            server.bind(('', 3069))
            server.listen(1)
        except OSError:
            logging.exception('Excepción al arrancar la estación')
        else:
            logging.info('Preparado para recibir datos...')
            while True:
                mensaje = ''
                error_datos = True
                try:
                    cliente,address = server.accept()
                    mensaje = cliente.recv(1024).decode()
                except OSError:
                    logging.exception('Excepción al recibir de la estación.')
                else:
                    # Quita todo lo que no sean numeros (decimal o exponencial), comas y caracteres I y F
                    sval = ''.join(c for c in mensaje if c in 'IF0123456789.,+-e')
                    if len(sval) and sval[0]=='I' and sval[-1] == 'F':
                        sval = sval[1:-1]
                        lval = sval.split(',')
                        if len(lval) == len(Estacion.KEYS):
                            cliente.sendall(self.es_cambio_de_dia())
                            self.sdatos = sval
                            nuevos_datos = dict(zip(Estacion.KEYS, lval))
                            dif_uptime = int(nuevos_datos['uptime']) - int(self.ddatos['uptime'])
                            if self.datos_disponibles and dif_uptime > 1:
                                logging.warning('Se perdieron %s mensaje(s) anteriore(s).', str(dif_uptime - 1))
                            self.ddatos = nuevos_datos
                            self.salvar_datos()
                            error_datos = False
                            self.datos_disponibles = True
                    if error_datos:
                        logging.warning('Recibido mensaje incorrecto desde estación: %s', mensaje)
                cliente.close()
            server.close()
            logging.info('Estación cerrada.')

    def run_minutero(self):
        logging.info('Temporizador minutero arrancado.')
        minuto_ant = datetime.now().minute
        while True:
            minuto = datetime.now().minute
            es_minuto_clave = minuto != minuto_ant and minuto % self.periodo == 0
            if self.datos_disponibles and es_minuto_clave:
                if oled:
                    SSPMeteoOled.update(self.ddatos)
                self.enviar_datos_a_wunder()
                # Control watchdog de la estación
                if self.ddatos['uptime'] == self.uptime_ant:
                    self.watchdog += 1
                else:
                    self.watchdog = 0
                if self.watchdog > 5:
                    logging.warning('No se reciben datos de la estación.')
                self.uptime_ant = self.ddatos['uptime']
            minuto_ant = minuto
            time.sleep(0.5)

if __name__ == "__main__":
    import locale
    locale.setlocale(locale.LC_ALL, '')
    import logging
    logging.basicConfig(filename='sspmeteo2.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%c')
    # Comunicacion con el Wemos
    Estacion().run()
