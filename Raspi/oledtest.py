from sspmeteo2_server import MiPantallita

datos = '15:39:11, 26.60, 72.23, 21.18, 1023.59, 0.0, 0.00, 228.35, 12.80, 345'

pantallita = MiPantallita()
pantallita.update(datos)
