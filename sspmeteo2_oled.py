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

from oled.device import sh1106
from oled.render import canvas
from PIL import ImageDraw, ImageFont
from datetime import datetime

FONT_FILE0 = 'Roboto-BoldCondensed.ttf'
FONT_FILE1 = 'wwDigital.ttf'

class SSPMeteoOled:

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
    def update(cls, ddatos):
        for k, v in ddatos.items():
            ddatos[k] = float(v)
        with canvas(cls.oled) as draw:
            # Line 1 - Temp. and humidity
            line = '{:.1f}º {:.0f}%'.format(ddatos['temp'], ddatos['humi'])
            font = cls.font0
            if draw.textsize(line, font)[0] > cls.oled.width:
                font = cls.font1
            of = int((cls.oled.width - draw.textsize(line, font)[0]) / 2)
            draw.text((0 + of, 0), line, 1, font)

            # Line 2 - Rain
            line = ''
            if ddatos['llud'] > 0 or ddatos['lluh'] > 0:
                if ddatos['lluh'] > 0:
                    line = '{:.1f}mm/h {:.0f}mm'.format(ddatos['lluh'], ddatos['llud'])
                    #~ status = '¡ LLUEVE !   '
                else:
                    line = 'Lluvia diaria {:.0f}mm'.format(ddatos['llud'])
            draw.text((0, 28), line, 1, cls.font2)

            # Line 3 - Pressure and wind
            line = '{:.0f}mb {:.0f}kph {:.0f}º'.format(ddatos['pres'], ddatos['vven'], ddatos['dven'])
            font = cls.font2
            draw.text((0, 40), line, 1, font)

            # Line 4 - Status
            d, resto = divmod(ddatos['wdog'] * 5, 24 * 60)
            h, m = divmod(resto, 60)
            line = '{} {}d{}:{}'.format(datetime.now().strftime('%H:%M:%S'), int(d), int(h), int(m))
            draw.text((0, 52), line, 1, cls.font2)

if __name__ == "__main__":
    SSPMeteoOled.begin()
