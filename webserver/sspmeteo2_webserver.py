from bottle import route, run, template, static_file
import socket

@route('/static/<filename>')
def send_static(filename):
    return static_file(filename, root='./static')

@route('/sspmeteo2')
def hello():
    s = socket.socket()
    s.connect(('192.168.1.10', 1234))
    s.send('GET_DATOS'.encode())
    datos = s.recv(256).decode().split(',')
    s.close()
    return template('sspmeteo2', datos=datos)
run(host='192.168.1.5', port=8080, debug=True, reloader=True)
