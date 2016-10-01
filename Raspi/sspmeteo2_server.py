import select
import socket
import sys
import logging
from datetime import datetime
from oled.device import sh1106
from oled.render import canvas
from PIL import ImageDraw, ImageFont

FONT_FILE0 = 'Roboto-BoldCondensed.ttf'
FONT_FILE1 = 'wwDigital.ttf'

class MiPantallita:
    def __init__(self):
        self.oled = sh1106()
        self.font0 = ImageFont.truetype(FONT_FILE0, 30)
        self.font1 = ImageFont.truetype(FONT_FILE0, 24)
        self.font2 = ImageFont.truetype(FONT_FILE1, 12)
        with canvas(self.oled) as draw:
            draw.text((8, 14), 'SSPMeteo2', 1, self.font1)
            draw.text((0, 50), 'Esperando datos...', 1, self.font2)

    def update(self, datos):
        lval = datos.split(', ')
        val = [float(x) for x in lval[1:]]     # Remove wemos date (lval[0])
        status = datetime.now().strftime('%X') + '   '
        with canvas(self.oled) as draw:
            # Line 1 - Temp. and humidity
            line = '{:.1f}º {:.0f}%'.format(val[0],val[1])
            font = self.font0
            if draw.textsize(line, font)[0] > self.oled.width:
                font = self.font1
            of = int((self.oled.width - draw.textsize(line, font)[0]) / 2)
            draw.text((0 + of, 0), line, 1, font)
            
            # Line 2 - Rain
            line = ''
            if val[4] > 0 or val[5] > 0:
                if val[5] > 0:
                    line = '{:.1f}mm/h {:.0f}mm'.format(val[5],val[4])
                    status = '¡ LLUEVE !   '
                else:
                    line = 'Lluvia diaria {:.0f}mm'.format(val[4])
            draw.text((0, 28), line, 1, self.font2)
            
            # Line 3 - Pressure and wind
            line = '{:.0f}mb {:.0f}kph {:.0f}º'.format(val[3],val[6],val[8])
            font = self.font2
            draw.text((0, 40), line, 1, font)
            
            # Line 4 - Status
            draw.text((0, 52), status + lval[0], 1, self.font2)
    
class Server:
    def __init__(self, port):
        self.host = ''
        self.port = port
        self.server = None

    def open_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host,self.port))
            self.server.listen(5)
            logging.info('A la escucha...')
        except socket.error as error:
            if self.server:
                self.server.close()
            logging.info("No se puede abrir el socket: " + error.strerror)
            sys.exit(1)

    def run(self, pantallita):
        self.open_server()
        input = [self.server]
        running = True
        while running:
            inputready,outputready,exceptready = select.select(input,[],[])
            for s in inputready:
                # handle the server socket
                if s == self.server:
                    cliente, foo = self.server.accept()
                    datos = cliente.recv(1024).decode()
                    if 'Q' in datos:
                        datos = datos.replace('Q','')
                        logging.info(datos)
                        pantallita.update(datos)
                    cliente.close()
        self.server.close()

if __name__ == "__main__":
    logconf = { 'filename'  : 'datos.log',
                'level'     : logging.INFO,
                'format'    : '%(asctime)s, %(message)s',
                'datefmt'   : '%c'}
                
    logging.basicConfig(**logconf)
    Server(port=1234).run(MiPantallita())


