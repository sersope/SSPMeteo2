 /*
  SSPMeteo2 para WEMOS D1 R2
  
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
*/

#include "DHT.h"

// TODO Los pines se deben redefinir o usar los correpondientes en WEMOS
#define LLUVIA_PIN  2
#define LLUVIA_INT  0
#define ANEMOM_PIN  3
#define ANEMOM_INT  1
#define ANEMOM_FACTOR 2.4     // km/h para un giro de un segundo. DETERMINAR EXPERIMENTALMENTE PARA NUEVO ANEMOMETRO
#define DHT22_PIN   4
#define VELETA_PIN  A0

#define INTERVALO_BASE 10000  // (en milisegundos) 
#define NUM_INTERVALOS 5      // Número de intervalos base que pasan en cada lectura/trasmision de valores (Ej. 5 * 10s. = 50seg.)


// DHT22: TEMPERATURA Y HUMEDAD
DHT dht(DHT22_PIN, DHT22);  // Initialize DHT sensor for normal 16mhz Arduino
float humi;  // Huemdad relativa en %
float temp;  // Temperatura en ºC

// LLUVIA
volatile word lluvia_ticks = 0L;             // variables modified in callback must be volatile
volatile unsigned long lluvia_last = 0UL;    // the last time the output pin was toggled

// ANEMOMETRO
float vel_vent;         // Velocidad del viento en km/h
float vel_racha = 0.0;  // Velocidad de rachas en km/h
volatile unsigned long anemom_ticks = 0L;    // variables modified in callback must be volatile
volatile unsigned long anemom_last = 0UL;    // the last time the output pin was toggled

// VELETA
const int veletaVal[] = {75, 132, 191, 233, 314, 389, 418, 555, 610, 733, 777, 835, 895, 928, 937, 957};  // DETERMINAR EXPERIMENTALMENTE
const word veletaDir[] = {270, 315, 292, 0, 337, 225, 247, 45, 22, 180, 202, 135, 157, 90, 67, 112};
word dir_vent;  // Direccion del viento en grados sexagesimales. (0 - 359)

unsigned long timer_lectura;
int intervalo;

// Callback para el contaje de lluvia
void cuenta_lluvia()
{
  if ((millis() - lluvia_last) > 100)  // Fecuencia volteo balancin maxima = 1 / (debounce / 1000) (Con debounce = 200 son 5 volteos/seg. Imposible fisicamente, bien) 
  {
    lluvia_ticks++;
  }
  lluvia_last = millis();
}

// Callback para contar ticks del anemometro
void cuenta_anemom()
{
  if((millis() - anemom_last) > 15)  // Max.vel.anemom. = ANEMOM_FACTOR / (debounce / 1000) (con debounce = 15 milis son 160 km/h. Máx. velocidad anemometro WH1080
  {
    anemom_ticks++;
  }
  anemom_last = millis();
}

// Obten valores de Temperatura y Humedad
void leeDHT()
{
    humi = dht.readHumidity();
    temp = dht.readTemperature();
  
    // Algun fallo en la lectura
    if (isnan(humi) || isnan(temp))
    {
      humi = 1000.0;
      temp = 1000.0;
    }
}

// Obten la velocidad del viento como promedio en el intervalo NUM_INTERVALOS * INTERVALO_BASE
// La velocidad de racha es la maxima de las medidas en cada INTERVALO_BASE
// La funcion ha de ser llamada exactamente cada INTERVALO_BASE para exactitud en el calculo de la velocidad del viento
void leeAnemom()
{
  float vel = (ANEMOM_FACTOR * anemom_ticks) / (INTERVALO_BASE / 1000.0);
  anemom_ticks = 0;
  
  if( vel > vel_racha)
    vel_racha = vel;
  
  vel_vent += vel; 
  
  if (intervalo == NUM_INTERVALOS)
    vel_vent /= NUM_INTERVALOS;
}

void leeVeleta()
{
  int lectura = analogRead(VELETA_PIN);
  
  unsigned int minDif = 2048;
  int i, min_i,dif;
 
  for (i = 0; i < 16; i++)
  {
     dif = abs(lectura - veletaVal[i]);
     if(dif < minDif)
     {
       minDif = dif;
       min_i = i;
     }
  }
  dir_vent = veletaDir[min_i];
}


void sendData()
{
  
  Serial.print("Temp= "); Serial.print(temp);
  Serial.print(" Hume= "); Serial.print(humi);
  Serial.print(" Lluv= "); Serial.print(lluvia_ticks);
  Serial.print(" Vven= "); Serial.print(vel_vent);
  Serial.print(" Vrac= "); Serial.print(vel_racha);
  Serial.print(" Dven= "); Serial.println(dir_vent);
}


 
void setup()
{
  Serial.begin(9600);
  Serial.println("SSPMeteo2.");
    
  // Para el conteo de lluvia
  pinMode(LLUVIA_PIN,INPUT_PULLUP);
  attachInterrupt(LLUVIA_INT,cuenta_lluvia,FALLING);
  
  // Para el conteo del anemometro
  pinMode(ANEMOM_PIN,INPUT_PULLUP);
  attachInterrupt(ANEMOM_INT,cuenta_anemom,FALLING);
  
  // Prepara el sensor DHT22
  dht.begin();
    
  // Primera vez
  timer_lectura = millis();
  intervalo = 0;
}

void loop()
{
  if ((millis() - timer_lectura) >= INTERVALO_BASE)
  {
    intervalo ++;
    leeAnemom();
    //Serial.print("Vrac= "); Serial.println(vel_racha); // PRUEBAS
    if (intervalo == NUM_INTERVALOS)
    {
      leeVeleta();
      leeDHT();
      sendData();
      
      intervalo = 0;
      vel_vent = 0.0;
      vel_racha = 0.0;
    }
    timer_lectura += INTERVALO_BASE;
  }
}


