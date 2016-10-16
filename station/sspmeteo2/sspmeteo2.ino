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
#include <Adafruit_BME280.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>



// Los pines usados
#define LLUVIA_PIN  D7
#define ANEMOM_PIN  D6
#define VELETA_PIN  A0
#define DHT22_PIN   D4

#define ANEMOM_FACTOR 2.4       // km/h para un giro de un segundo. Para anemometro WH1080.
#define LLUVIA_FACTOR 0.138     // Por cada tick de mi pluviómetro. En mm.
#define ALTITUD 20.0            // En mi casa. en metros.

#define INTERVALO_BASE 30000    // (en milisegundos)
#define NUM_INTERVALOS 10       // Número de intervalos base que pasan en cada lectura/trasmision de valores (Ej. 5 * 10s. = 50seg.)
unsigned long timer_lectura;
int intervalo;

// Direcciones para la conexión Wifi
IPAddress staticIP(192,168,1,11);
IPAddress gateway(192,168,1,33);
IPAddress subnet(255,255,255,0);
IPAddress dns1(8,8,8,8);
IPAddress dns2(8,8,4,4);

const uint16_t puerto = 1234;
const char * servidor = "192.168.1.10"; // ip or dns
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "europe.pool.ntp.org", 7200, 3600000); // Dos horas de offset y actualiza cada hora
int hora_anterior;

// watchdog y contadores de errores
unsigned long watchdog;
unsigned long conterr_wifi;
unsigned long conterr_ntp;
unsigned long conterr_server;
unsigned long conterr_wunder;

// BME280: PRESION, TEMPERATURA Y HUMEDAD
Adafruit_BME280 bme;  // I2C
float temp2;           // Temperatura del BMP en ºC
float pres;           // Presion en mbar
float humi2;           // Huemdad relativa en %

// DHT22: TEMPERATURA Y HUMEDAD
DHT dht(DHT22_PIN, DHT22);
float humi;  			// Huemdad relativa en %
float temp;  			// Temperatura en ºC
float troc;           	// Punto de rocio en ºC
float sum_temp = 0.0;
float min_temp = 1000.0;
float max_temp = -1000.0;
float sum_humi = 0.0;
float min_humi = 1000.0;
float max_humi = -1000.0;

// LLUVIA
float lluvia_dia;                            // Lluvia diaria
float lluvia_por_hora;                 // Acumulado de lluvia en ultimo intervalo
volatile word lluvia_ticks = 0L;             // variables modified in callback must be volatile
volatile unsigned long lluvia_last = 0UL;    // the last time the output pin was toggled
word lluvia_ticks_ant = 0L;                  // Para la gestión de la lluvia ultimo intervalo

// ANEMOMETRO
float vel_vent;                               // Velocidad del viento en km/h
float vel_racha = 0.0;                        // Velocidad de rachas en km/h
volatile unsigned long anemom_ticks = 0L;     // variables modified in callback must be volatile
volatile unsigned long anemom_last = 0UL;     // the last time the output pin was toggled

// VELETA
const word veletaDir[] = {  0, 23, 45, 68, 90, 113, 135, 158, 180, 203, 225, 248, 270, 293, 315, 338};
const int veletaVal[] =  {752, 401, 454, 92, 101, 74, 190, 134, 286, 246, 606, 578, 895, 789, 843, 676}; // DETERMINADO EXPERIMENTALMENTE
int veletaCount[16];    // Lleva la cuenta de las veces que se lee cada dirección
word dir_vent;  // Direccion del viento en grados sexagesimales. (0 - 359)

// Valores convertidos a unidades imperiales para Wunder
float tempW;
float presW;
float trocW;
float lluvia_diaW;
float lluvia_por_horaW;
float vel_ventW;
float vel_rachaW;

// Callback para el contaje de lluvia
void cuenta_lluvia()
{
  // Fecuencia volteo balancin maxima = 1 / (debounce / 1000) (Con debounce = 200 son 5 volteos/seg. Imposible fisicamente, bien)
  // Si hace mas de 20 min. (20 x 60 x 1000 = 1200000) que no llueve no consideres el pulso que entra. Filtro de pulsos espontáneos.
  if ((millis() - lluvia_last) > 200 && (millis() - lluvia_last) < 1200000)
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

// Obten valores de presion, temperatura y humedad del BMP
void leeBME()
{
  temp2 = bme.readTemperature();                      // En ºC
  humi2 = bme.readHumidity();
  pres = bme.readPressure() / 100;                    // En mbar
  pres = (pres / pow(1.0 - ALTITUD / 44330, 5.255));  // At sea level	
}

// Obten valores de temperatura y humedad del DHT
void leeDHT()
{
  float t,h;
  h = dht.readHumidity();
  t = dht.readTemperature(); // En ºC
  // Si algun fallo en la lectura manten el valor actual
  if (isnan(h) || isnan(t))
  {
    h = humi;
    t = temp;
  }

  sum_temp += t;
  if (t < min_temp)
      min_temp = t;
  if (t > max_temp)
      max_temp = t;
      
  sum_humi += h;
  if (h < min_humi)
      min_humi = h;
  if (h > max_humi)
      max_humi = h;
}

void calcDHT()
{
    // Elimina valores máximo y minimo y calcula la media
    sum_temp -= min_temp + max_temp;
    temp = sum_temp / (NUM_INTERVALOS - 2);
    
    sum_humi -= min_humi + max_humi;
    humi = sum_humi / (NUM_INTERVALOS - 2);
   
    // Punto de rocío
    troc = pow(humi / 100.0, 1.0 / 8.0) * (112.0 + 0.9 * temp) + 0.1 * temp - 112.0;
    
    // Resetea valores de intervalo
    sum_temp = 0.0;
    min_temp = 1000.0;
    max_temp = -1000.0;
    sum_humi = 0.0;
    min_humi = 1000.0;
    max_humi = -1000.0;
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

  // Obten la dirección más próxima al valor de lectura
  for (i = 0; i < 16; i++)
  {
    dif = abs(lectura - veletaVal[i]);
    if (dif < minDif)
    {
      minDif = dif;
      min_i = i;
    }
  }
  veletaCount[min_i] += 1;
}

void calcVeleta()
{
  // La dirección del viento es la que mas veces ha ocurrido (la moda) en el intervalo
  unsigned int maxCount = 0, max_i = 0;
  int i;
  for (i = 0; i < 16; i++)
  {
    if (veletaCount[i] > maxCount)
    {
      maxCount = veletaCount[i];
      max_i = i;
    }
  }
  dir_vent = veletaDir[max_i];
  // Resetea contadores
  for (i = 0; i < 16; i++)
    veletaCount[i] = 0;

}

void calcLluvia()
{
  lluvia_dia = lluvia_ticks * LLUVIA_FACTOR;
  // Calculo lluvia/hora
  lluvia_por_hora = (lluvia_ticks - lluvia_ticks_ant) * LLUVIA_FACTOR * 60.0 * 60.0 * 1000.0 / (INTERVALO_BASE * NUM_INTERVALOS);
  lluvia_ticks_ant = lluvia_ticks;
}

void comunicaPorWifi(bool send_to_wunder = false, bool send_to_servidor= true)
{
  const char* ssid     = "Wsergio";
  const char* password = "cochin29";
  float ini;

  //Serial.print(timeClient.getFormattedTime());
  //Serial.print(" Conectando Wifi...");
  //Serial.print(" Estado:");
  //Serial.println(WiFi.status());
  ini = millis();
  WiFi.begin(ssid, password);
  WiFi.config(staticIP, gateway, subnet, dns1, dns2);
  while (WiFi.status() != WL_CONNECTED)
  {
    //Serial.print(".");
    delay(100);
  }
  //Serial.println(' ');
  if (WiFi.status() == WL_CONNECTED)
  {
    //Serial.print(timeClient.getFormattedTime());
    //Serial.print(" WiFi conectada en ");
    //Serial.print((millis() - ini) / 1000.0, 3);
    //Serial.print(" Estado:");
    //Serial.print(WiFi.status());
    //Serial.print(" IP:");
    //Serial.println(WiFi.localIP());
    
    // Actualiza hora del día (via NTP)
    bool horaOK;
    timeClient.begin();
    horaOK = timeClient.update();
    //Serial.print(timeClient.getFormattedTime());
    //Serial.print(" NTP: ");
    if (horaOK)
    {
      horaOK = true;
      //Serial.println("OK");
    }
    else
    {
      conterr_ntp++;
      //Serial.println("error");
    }
    timeClient.end();
    
    // Acceso a Wunder
    if (send_to_wunder)
    {
      convertirUnidades(); // A Wunder unidades imperiales
      HTTPClient http;
      String uri = String("http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=ICOMUNID54&PASSWORD=laura11&action=updateraw&dateutc=now");
      uri += "&tempf=";        uri += tempW;
      uri += "&humidity=";     uri += humi;
      uri += "&dewptf=";       uri += trocW;
      uri += "&dailyrainin=";  uri += lluvia_diaW;
      uri += "&rainin=";       uri += lluvia_por_horaW;
      uri += "&windspeedmph="; uri += vel_ventW;
      uri += "&windgustmph=";  uri += vel_rachaW;
      uri += "&winddir=";      uri += dir_vent;
      uri += "&baromin=";      uri += presW;
      http.begin(uri);
      int httpCode = http.GET();
      //Serial.print(timeClient.getFormattedTime());
      //Serial.print(" Wunder: ");
      if (httpCode == HTTP_CODE_OK)
      {
        String payload = http.getString();
        //Serial.print(payload);
      }
      else
      {
        conterr_wunder++;
        //Serial.print("error: "); //Serial.println(http.errorToString(httpCode).c_str());
      }
      http.end();
    }
    // Envio al servidor
    if (send_to_servidor)
    {
      WiFiClient cliente;
      //Serial.print(timeClient.getFormattedTime());
      //Serial.print(" Servidor "); //Serial.print(servidor);
      if (!cliente.connect(servidor, puerto))
      {
        conterr_server++;
        //Serial.println(": Conexión fallida.");
      }
      else
      {
        String msg = String(timeClient.getFormattedTime());
        msg += ", "; msg += temp;
        msg += ", "; msg += temp2;
        msg += ", "; msg += humi;
        msg += ", "; msg += humi2;
        msg += ", "; msg += troc;
        msg += ", "; msg += pres;
        msg += ", "; msg += lluvia_dia;
        msg += ", "; msg += lluvia_por_hora;
        msg += ", "; msg += vel_vent;
        msg += ", "; msg += vel_racha;
        msg += ", "; msg += dir_vent;
        msg += ", "; msg += watchdog;
        msg += ", "; msg += conterr_wifi;
        msg += ", "; msg += conterr_ntp;
        msg += ", "; msg += conterr_wunder;
        msg += ", "; msg += conterr_server;
        msg += ", "; msg += (millis() - ini) / 1000.0;   // Duracion en segundos del acceso Wifi
        msg += "Q";
        cliente.print(msg);
        //Serial.println(": Datos enviados");
      }
      cliente.stop();
    }       
  }
  else
  {
    conterr_wifi++;
  }
  // Fin de la WiFi
  WiFi.disconnect();
  //Serial.print(timeClient.getFormattedTime());
  //Serial.print(" WiFi desconectada en ");
  //Serial.print((millis() - ini) / 1000.0, 3);
  //Serial.print(" Estado:");
  //Serial.println(WiFi.status());
  //Serial.println("");
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
  tempW = temp * 1.8 + 32;                      // to ºF
  trocW = troc * 1.8 + 32;                      // to ºF
  presW = pres * 0.0295299830714;               // A pulgadas de columna de mercurio
  lluvia_diaW = lluvia_dia / 25.4;              // En pulgadas
  lluvia_por_horaW = lluvia_por_hora / 25.4;    // En pulgadas
  vel_ventW =  vel_vent * 0.621371192;          // En mph
  vel_rachaW = vel_racha *0.621371192;          // En mph
}

void setup()
{
  WiFi.disconnect();
  //Serial.begin(115200);
  //delay(100);
  //Serial.println();
  //Serial.println("SSPMeteo2.");
  //Serial.println();
  comunicaPorWifi(false, false); //Solo para obtener la hora
  // Para el conteo de lluvia
  pinMode(LLUVIA_PIN, INPUT_PULLUP);
  // Para el conteo del anemometro
  pinMode(ANEMOM_PIN, INPUT_PULLUP);
  conectaInterrupts();
  // Prepara el sensor DHT22
  pinMode(DHT22_PIN, INPUT_PULLUP);
  dht.begin();
  // Prepara el sensor BME280
  if (!bme.begin(0x76))
  {
    //Serial.println("No se encuentra el sensor BME280.");
  }
  // Primera vez
  hora_anterior = timeClient.getHours();
  intervalo = 0;
  timer_lectura = millis();
}

void loop()
{
  int hora;

  if ((millis() - timer_lectura) >= INTERVALO_BASE)
  {
    intervalo ++;
    leeVeleta();
    leeDHT();
    leeAnemom();
    if (intervalo == NUM_INTERVALOS)
    {
      // Calculo de valores
      calcLluvia();
      leeBME();
      calcVeleta();
      calcDHT();
      // Comunicate
      desconectaInterrupts();
      watchdog++;
      comunicaPorWifi(true, true);
      conectaInterrupts();
      // Comprueba cambio de dia
      hora = timeClient.getHours();
      if ( hora < hora_anterior && hora_anterior == 23)
      {
        lluvia_ticks = 0;
        lluvia_ticks_ant = 0;
      }
      hora_anterior = hora;
      // Reset de timer y valores de viento
      intervalo = 0;
      vel_vent = 0.0;
      vel_racha = 0.0;
    }
    timer_lectura += INTERVALO_BASE;
  }
}


