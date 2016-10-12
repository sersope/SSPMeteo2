import socketserver
import logging
from oled.device import sh1106
from oled.render import canvas
from PIL import ImageDraw, ImageFont

FONT_FILE0 = 'Roboto-BoldCondensed.ttf'
FONT_FILE1 = 'wwDigital.ttf'

class MiOled:

    oled = sh1106()
    font0 = ImageFont.truetype(FONT_FILE0, 30)
    font1 = ImageFont.truetype(FONT_FILE0, 24)
    font2 = ImageFont.truetype(FONT_FILE1, 12)

    @classmethod
    def begin(cls):
        with canvas(cls.oled) as draw:
            draw.text((8, 14), 'SSPMeteo2', 1, cls.font1)
            draw.text((0, 50), 'Esperando datos...', 1, cls.font2)

    @classmethod
    def update(cls, datos):
        try:
            lval = datos.split(', ')
            val = [float(x) for x in lval[1:]]     # Remove wemos date (lval[0])
        except:
            return
        with canvas(cls.oled) as draw:
            # Line 1 - Temp. and humidity
            line = '{:.1f}º {:.0f}%'.format(val[0],val[1])
            font = cls.font0
            if draw.textsize(line, font)[0] > cls.oled.width:
                font = cls.font1
            of = int((cls.oled.width - draw.textsize(line, font)[0]) / 2)
            draw.text((0 + of, 0), line, 1, font)

            # Line 2 - Rain
            line = ''
            if val[4] > 0 or val[5] > 0:
                if val[5] > 0:
                    line = '{:.1f}mm/h {:.0f}mm'.format(val[5],val[4])
                    #~ status = '¡ LLUEVE !   '
                else:
                    line = 'Lluvia diaria {:.0f}mm'.format(val[4])
            draw.text((0, 28), line, 1, cls.font2)

            # Line 3 - Pressure and wind
            line = '{:.0f}mb {:.0f}kph {:.0f}º'.format(val[3],val[6],val[8])
            font = cls.font2
            draw.text((0, 40), line, 1, font)

            # Line 4 - Status
            d, resto = divmod(val[9] * 5, 24 * 60)
            h, m = divmod(resto, 60)
            line = '{} {}d{}:{}'.format(lval[0], int(d), int(h), int(m))
            draw.text((0, 52), line, 1, cls.font2)


class Datos:
    datos = 'NADA'


class MiTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        datos = self.request.recv(256).decode()
        if 'Q' in datos:
            datos = datos.replace('Q','')
            Datos.datos = datos
            logging.info(datos)
            MiOled.update(datos)
        elif 'GET_DATOS' in datos:
            self.request.sendall(Datos.datos.encode())


if __name__ == "__main__":
    logconf = { 'filename'  : 'datos.log',
                'level'     : logging.INFO,
                'format'    : '%(asctime)s, %(message)s',
                'datefmt'   : '%c'}

    logging.basicConfig(**logconf)
    logging.info('A la escucha ...')
    MiOled.begin()
    HOST, PORT = "", 1234
    server = socketserver.TCPServer((HOST, PORT), MiTCPHandler)
    server.serve_forever()
