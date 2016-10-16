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

from bottle import route, run, template, static_file
import socket
import sys, getopt

data_server = 'localhost'
data_server_port = 1234
web_server_port = 8080

# Rutas del servidor
@route('/static/<filename>')
def send_static(filename):
    return static_file(filename, root='./static')

@route('/sspmeteo2')
def hello():
    datos = ['0' for i in range(16)]
    datos[4] = '950'
    try:
        s = socket.socket()
        s.connect((data_server, data_server_port))
        s.send('GET_DATOS'.encode())
        datos = s.recv(256).decode().split(',')
        s.close()
        # Línea de estado
        d, resto = divmod(int(datos[12]) * 5, 24 * 60)
        h, m = divmod(resto, 60)
        uptime = ' Actividad: {}d {}h {}m'.format(int(d), int(h), int(m))
        datos[0] = 'Datos actualizados a las ' + datos[0] + uptime
    except:
        datos[0]= "ERROR en el acceso al servidor de datos."
    return template('sspmeteo2', datos=datos)


# Parse argumentos de linea de comandos
usage = 'Usage: -p <web server port> -S <data server> -P <data server port>'
try:
    opts, args = getopt.getopt(sys.argv[1:],"hp:S:P:")
except getopt.GetoptError:
    print(usage)
    sys.exit(2)
if  len(opts) == 0 and len(args) > 0:
    print(usage)
    sys.exit()
for opt, arg in opts:
    if opt == '-h':
        print(usage)
        sys.exit()
    elif opt == '-p':
        web_server_port = arg
    elif opt == '-S':
        data_server = arg
    elif opt == '-P':
        data_server_port = arg
    else:
        print(usage)
        sys.exit()

print('Data server: ', data_server + ':' + str(data_server_port))
# Lanza el servidor
run(host='', port=web_server_port)
