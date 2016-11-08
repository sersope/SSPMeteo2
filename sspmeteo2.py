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

import locale
import logging
from bottle import route, run, template, static_file
import threading
from datetime import datetime
from sspmeteo2_estacion import Estacion

# Rutas del servidor
@route('/static/<filename>')
def send_static(filename):
    return static_file(filename, root='./static')

@route('/sspmeteo2')
def principal():
    # Línea de estado
    d, resto = divmod(int(float(estacion.ddatos['wdog'])) * estacion.periodo, 24 * 60)
    h, m = divmod(resto, 60)
    uptime = ' Actividad: {}d {}h {}m'.format(int(d), int(h), int(m))
    status = 'Datos actualizados a las ' + datetime.now().strftime('%H:%M:%S') + uptime
    return template('sspmeteo2', datos=estacion.ddatos, status=status)

@route('/sspmeteo2/<year>/<mes>/<dia>')
def datos_diarios(year, mes, dia):
    filename = year + '-' + mes + '-' + dia + '.dat'
    root = './datos/{0}/{0}-{1}'.format(year,mes)
    return static_file(filename, root=root)

@route('/sspmeteo2/log')
def log():
    return static_file('sspmeteo2.log', root='.')

@route('/sspmeteo2/datos')
def datos():
    return estacion.ddatos

locale.setlocale(locale.LC_ALL, '')
logging.basicConfig(filename='sspmeteo2.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%c')
logging.info('Iniciando sspmeteo2...')
# Arranca la estacion
estacion = Estacion()
threading.Thread(target= estacion.run).start()
# Lanza el servidor web
run(host='', port=8080)
