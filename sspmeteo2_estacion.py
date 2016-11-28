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
import requests
import time
import serial
from datetime import datetime, timedelta
import logging

oled = True
try:
    from sspmeteo2_oled import SSPMeteoOled
except:
    oled = False

class Estacion:

    KEYS = ['hora', 'temp', 'temp2', 'humi', 'humi2', 'troc', 'pres', 'llud', 'lluh', 'vven', 'vrac', 'dven', 'ciclos']

    def __init__(self, port= '/dev/ttyUSB0', periodo= 5):
        self.port = port
        self.periodo = periodo          # Periodo de comunicacion en minutos de la estacion
        self.hoy = datetime.now().day
        self.ciclos = 0.0               # Uptime estacion = ciclos * periodo (en minutos)
        self.serial = None
        # Inicializacion de datos
        self.ddatos = dict(zip(Estacion.KEYS, ['0' for k in Estacion.KEYS]))
        # Pantalla Oled
        if oled:
            SSPMeteoOled.begin()
        else:
            logging.info('Sin pantalla OLED.')
        # Inicia serial
        try:
            self.serial = serial.Serial(self.port, 115200, timeout= 2)
        except:
            print(datetime.now().strftime('%c'), 'Excepción: No se pudo abrir el puerto con la estación.')
            self.serial = None

    def es_cambio_de_dia(self):
        dema = (datetime.now() + timedelta(minutes= self.periodo)).day
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
           f.write(','.join([self.ddatos[k] for k in Estacion.KEYS]))
        #Salva la lluvia diaria
        with open('datos/lluvia.last','w') as f:
            f.write(self.ddatos['llud'])

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

    def comunica_con_estacion(self):
        datos_ok = False
        if self.serial != None:
            mensaje = ''
            envio = self.es_cambio_de_dia()
            self.serial.write(envio)
            time.sleep(0.6)     # Si es necesario, aumentar el timeout
            mensaje = self.serial.read(self.serial.in_waiting).decode()
            # Quita todo lo que no sean numeros (decimal o exponencial), comas y caracteres I y F
            sval = ''.join(c for c in mensaje if c in 'IF0123456789.,+-e')
            if len(sval) and sval[0]=='I' and sval[-1] == 'F':
                lval = sval[1:-1].split(',')
                if len(lval) == len(Estacion.KEYS) - 1:
                    self.ddatos = dict(zip(Estacion.KEYS[1:], lval))
                    self.ddatos['hora'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.ciclos = float(self.ddatos['ciclos'])
                    datos_ok = True
            if not datos_ok:
                logging.warning('Recibido mensaje incorrecto desde estación: %s', mensaje)
        return datos_ok

    def run(self):
        logging.info('Estación arrancada.')
        minuto_ant = datetime.now().minute
        while True:
            minuto = datetime.now().minute
            es_minuto_clave = minuto != minuto_ant and minuto % self.periodo == 0
            if es_minuto_clave:
                if self.comunica_con_estacion() and self.ciclos > 0:
                    self.salvar_datos()
                    if oled:
                        SSPMeteoOled.update(self.ddatos)
                    self.enviar_datos_a_wunder()
            minuto_ant = minuto
            time.sleep(0.2)

if __name__ == "__main__":
    import locale
    locale.setlocale(locale.LC_ALL, '')
    import logging
    logging.basicConfig(filename='sspmeteo2.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%c')
    # Comunicacion con el Wemos
    Estacion().run()
