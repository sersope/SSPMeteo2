

// TODO:
//        Resetear lluvia diaria por cambio de dia. HECHO
//        Contemplar lluvia última hora.
//        Calcular punto de rocio. HECHO
//        Meter las conversiones de unidades en una sola subrutina. HECHO
//        Completar el envio a Wunder.

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
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>

// Los pines usados
#define LLUVIA_PIN  D3
#define ANEMOM_PIN  D6
#define DHT22_PIN   D5
#define VELETA_PIN  A0

#define ANEMOM_FACTOR 2.4     // km/h para un giro de un segundo. Para anemometro WH1080.
#define LLUVIA_FACTOR 0.138   // Por cada tick de mi pluviómetro. En mm.
#define ALTITUD 20            // En mi casa. en metros.

#define INTERVALO_BASE 60000   // (en milisegundos) 
#define NUM_INTERVALOS 10      // Número de intervalos base que pasan en cada lectura/trasmision de valores (Ej. 5 * 10s. = 50seg.)

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "europe.pool.ntp.org");
int hora_actual;

// BMP: PRESION Y TEMPERATURA
Adafruit_BMP085 bmp;
float temp2; // Temperatura del BMP en ºC
float pres;  // Presion en mbar

// DHT22: TEMPERATURA Y HUMEDAD
DHT dht(DHT22_PIN, DHT22);
float humi;  // Huemdad relativa en %
float temp;  // Temperatura en ºC
float troc;  // Punto de rocio en ºC
// LLUVIA
float lluvia_dia;                            // Lluvia diaria en inches
volatile word lluvia_ticks = 0L;             // variables modified in callback must be volatile
volatile unsigned long lluvia_last = 0UL;    // the last time the output pin was toggled

// ANEMOMETRO
float vel_vent;         // Velocidad del viento en km/h
float vel_racha = 0.0;  // Velocidad de rachas en km/h
volatile unsigned long anemom_ticks = 0L;    // variables modified in callback must be volatile
volatile unsigned long anemom_last = 0UL;    // the last time the output pin was toggled

// VELETA
const word veletaDir[] = {  0, 23, 45, 68, 90, 113, 135, 158, 180, 203, 225, 248, 270, 293, 315, 338};
const int veletaVal[] =  {752, 401, 454, 92, 101, 74, 190, 134, 286, 246, 606, 578, 895, 789, 843, 676}; // DETERMINADO EXPERIMENTALMENTE

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
  if ((millis() - anemom_last) > 15) // Max.vel.anemom. = ANEMOM_FACTOR / (debounce / 1000) (con debounce = 15 milis son 160 km/h. Máx. velocidad anemometro WH1080
  {
    anemom_ticks++;
  }
  anemom_last = millis();
}

// Obten valores de Temperatura y Humedad
void leeDHT()
{
  float auxhumi = dht.readHumidity();
  float auxtemp = dht.readTemperature(); // En ºC
  // Si algun fallo en la lectura manten el valor actual
  if (!isnan(auxhumi) && !isnan(auxtemp))
  {
    humi = auxhumi;
    temp = auxtemp;
  }
  troc = pow(humi / 100.0, 1.0 / 8.0) * (112.0 + 0.9 * temp) + 0.1 * temp - 112.0;
}

// Obten alores de presion y temperatura del BMP
void leeBMP()
{
  temp2 = bmp.readTemperature();              // En ºC
  pres = bmp.readSealevelPressure(ALTITUD) / 100; // En mbar
}

// Obten la velocidad del viento como promedio en el intervalo NUM_INTERVALOS * INTERVALO_BASE
// La velocidad de racha es la maxima de las medidas en cada INTERVALO_BASE
// La funcion ha de ser llamada exactamente cada INTERVALO_BASE para exactitud en el calculo de la velocidad del viento
void leeAnemom()
{
  float vel = (ANEMOM_FACTOR * anemom_ticks) / (INTERVALO_BASE / 1000.0);
  anemom_ticks = 0;
  if ( vel > vel_racha)
    vel_racha = vel;

  vel_vent += vel;

  if (intervalo == NUM_INTERVALOS)
    vel_vent /= NUM_INTERVALOS;
}

void leeVeleta()
{
  int lectura = analogRead(VELETA_PIN);
  unsigned int minDif = 2048;
  int i, min_i, dif;

  for (i = 0; i < 16; i++)
  {
    dif = abs(lectura - veletaVal[i]);
    if (dif < minDif)
    {
      minDif = dif;
      min_i = i;
    }
  }
  dir_vent = veletaDir[min_i];
}

void printSerial()
{
  lluvia_dia = lluvia_ticks * LLUVIA_FACTOR;
  Serial.print(timeClient.getFormattedTime());
  Serial.print(" Temp= ");   Serial.print(temp, 1);
  Serial.print(" Hume= ");   Serial.print(humi, 0);
  Serial.print(" Troc= ");   Serial.print(troc, 1);
  Serial.print(" Tem2= ");   Serial.print(temp2, 1);
  Serial.print(" Pres= ");   Serial.print(pres);
  Serial.print(" Lluv= ");   Serial.print(lluvia_dia, 3);
  Serial.print(" (");        Serial.print(lluvia_ticks);
  Serial.print(") Vven= ");  Serial.print(vel_vent, 1);
  Serial.print(" Vrac= ");   Serial.print(vel_racha, 1);
  Serial.print(" Dven= ");   Serial.println(dir_vent);
}

void comunicaPorWifi(bool wunder = false)
{
  const char* ssid     = "Wsergio";
  const char* password = "cochin29";
  float ini;

  Serial.print(timeClient.getFormattedTime());
  Serial.print(" Conectando Wifi...");
  Serial.print(" Estado:");
  Serial.println(WiFi.status());
  ini = millis();
  WiFi.begin(ssid, password);
  while (WiFi.status() == WL_DISCONNECTED)
  {
    delay(10);
  }
  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print(timeClient.getFormattedTime());
    Serial.print(" WiFi conectada en ");
    Serial.print((millis() - ini) / 1000.0, 3);
    Serial.print(" Estado:");
    Serial.print(WiFi.status());
    Serial.print(" IP:");
    Serial.println(WiFi.localIP());
    if (wunder)
    {
      // Acceso a Wunder
      HTTPClient http;
      String uri = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=ICOMUNID54&PASSWORD=laura11&action=updateraw&dateutc=now";
      uri += "&tempf=";        uri += temp;
      uri += "&humidity=";     uri += humi;
      uri += "&dewptf=";       uri += troc;
      uri += "&dailyrainin=";  uri += lluvia_dia;
      uri += "&windspeedmph="; uri += vel_vent;
      uri += "&windgustmph=";  uri += vel_racha;
      uri += "&winddir=";      uri += dir_vent;
      uri += "&baromin=";      uri += pres;
      http.begin(uri);
      int httpCode = http.GET();
      Serial.print(timeClient.getFormattedTime());
      Serial.print(" Wunder: ");
      if (httpCode > 0)
      {
        if (httpCode == HTTP_CODE_OK)
        {
          String payload = http.getString();
          Serial.print(payload);
        }
      }
      else
      {
        Serial.printf("error: %s\n", http.errorToString(httpCode).c_str());
      }
      http.end();
    }
    // Actualiza hora del día (via NTP)
    bool horaOK;
    timeClient.begin();
    horaOK = timeClient.update();
    Serial.print(timeClient.getFormattedTime());
    Serial.print(" NTP: ");
    if (horaOK)
    {
      Serial.println("OK");
    }
    else
    {
      Serial.println("error");
    }
    timeClient.end();
    // Fin de la WiFi
    WiFi.disconnect();
    Serial.print(timeClient.getFormattedTime());
    Serial.print(" WiFi desconectada en ");
    Serial.print((millis() - ini) / 1000.0, 3);
    Serial.print(" Estado:");
    Serial.println(WiFi.status());
  }
  Serial.println("");
}

void conectaInterrupts()
{
  attachInterrupt(digitalPinToInterrupt(ANEMOM_PIN), cuenta_anemom, FALLING);
  attachInterrupt(digitalPinToInterrupt(LLUVIA_PIN), cuenta_lluvia, FALLING);
}

void desconectaInterrupts()
{
  detachInterrupt(digitalPinToInterrupt(ANEMOM_PIN));
  detachInterrupt(digitalPinToInterrupt(LLUVIA_PIN));
}

void convertirUnidades()
{
  temp = dht.convertCtoF(temp);
  temp2 = dht.convertCtoF(temp2);
  troc = dht.convertCtoF(troc);
  pres *= 0.0295299830714; // A pulgadas de columna de mercurio
  lluvia_dia = lluvia_ticks * LLUVIA_FACTOR / 25.4; // En pulgadas
  vel_vent *=  0.621371192; // En mph
  vel_racha *= 0.621371192; // En mph
}

void setup()
{
  WiFi.disconnect();
  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println("SSPMeteo2.");
  Serial.println();
  comunicaPorWifi(false); //Solo para obtener la hora
  // Para el conteo de lluvia
  pinMode(LLUVIA_PIN, INPUT_PULLUP);
  // Para el conteo del anemometro
  pinMode(ANEMOM_PIN, INPUT_PULLUP);
  conectaInterrupts();
  // Prepara el sensor DHT22
  pinMode(DHT22_PIN, INPUT_PULLUP);
  dht.begin();
  // Prepara el sensor BMP
  bmp.begin();
  // Primera vez
  timer_lectura = millis();
  intervalo = 0;
  hora_actual = timeClient.getHours();
}

void loop()
{
  int hora;

  if ((millis() - timer_lectura) >= INTERVALO_BASE)
  {
    intervalo ++;
    leeAnemom();
    if (intervalo == NUM_INTERVALOS)
    {
      // Lectura de sensores
      leeVeleta();
      leeDHT();
      leeBMP();
      // Comunicate
      printSerial();
      convertirUnidades();
      desconectaInterrupts();
      comunicaPorWifi(true);// FALSE:evita acceso a wunder (PARA PRUEBAS)
      conectaInterrupts();
      // Comprueba cambio de dia
      hora = timeClient.getHours();
      if ( hora < hora_actual)
      {
        hora_actual = hora;
        lluvia_ticks = 0;
      }
      // Reset de timer y valores de viento
      intervalo = 0;
      vel_vent = 0.0;
      vel_racha = 0.0;
    }
    timer_lectura += INTERVALO_BASE;
  }
}


