 /*
    Codificación de datos:
    -   nº del mensaje [1..255] 8 bits
    // TODO (sergio#1#): Determinar códigos de error para los valores erróneos
    -   temperatura [-30,0ºC, 70,0ºC] float    -> codigo temperatura= word(temperatura * 10) + 300 [0,1000]  Error de lectura:
    -   humedad     [0.0%, 100.0%]    float    -> codigo humedad= word(humedad * 10)               [0,1000]. Error de lectura:
    -   tics lluvia [0, 65535] 16 bits. word
    -   velocidad viento [0.0, 160.0 km/h]     float    -> codigo vel. vent. = word(vel_vent * 10)
    -   velocidad racha  [0.0, 160.0 km/h]     float    -> codigo vel. racha = word(vel_racha *10)
    -   direccion viento [0, 359]     word   
    mensaje1: unsigned long. 32 bits
        0000000000000001tttttttttttttttt -> temperatura.
    mensaje2: unsigned long. 32 bits
        0000000000000010hhhhhhhhhhhhhhhh -> humedad.
    mensaje3: unsigned long. 32 bits
        0000000000000011rrrrrrrrrrrrrrrr -> lluvia.
    mensaje4: unsigned long. 32 bits
        0000000000000100rrrrrrrrrrrrrrrr -> velocidad del viento.
    mensaje5: unsigned long. 32 bits
        0000000000000101rrrrrrrrrrrrrrrr -> velocidad de racha
    mensaje6: unsigned long. 32 bits
        0000000000000110rrrrrrrrrrrrrrrr -> direccion del viento
*/

#include <RCSwitch.h>
#include "DHT.h"

#define LLUVIA_PIN  2
#define LLUVIA_INT  0
#define ANEMOM_PIN  3
#define ANEMOM_INT  1
#define ANEMOM_FACTOR 2.4     // km/h para un giro de un segundo. DETERMINAR EXPERIMENTALMENTE PARA NUEVO ANEMOMETRO
#define DHT22_PIN   4
#define RF433_PIN   7
#define VELETA_PIN  A0

#define INTERVALO_BASE 10000  // (en milisegundos) 
#define NUM_INTERVALOS 5      // Número de intervalos base que pasan en cada lectura/trasmision de valores (Ej. 5 * 10s. = 50seg.)
#define N_MENSAJES  6         // Número total de mensajes a transmitir

// TRANSMISOR RF433
RCSwitch rcswitch = RCSwitch();
long mensaje[N_MENSAJES];  // Contiene los mensajes a transmitir

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


// Codifica los mensajes segun los valores a transmitir
void codifica()
{
  word ct,ch,cvv,cvr;
  ct = (word)round(temp * 10.0) + 300;
  ch = (word)round(humi * 10.0);
  cvv = (word)round(vel_vent * 10.0);
  cvr = (word)round(vel_racha * 10.0);
  mensaje[0] = 0x10000 | ct;
  mensaje[1] = 0x20000 | ch;
  mensaje[2] = 0x30000 | lluvia_ticks;
  mensaje[3] = 0x40000 | cvv;
  mensaje[4] = 0x50000 | cvr;
  mensaje[5] = 0x60000 | dir_vent;
}
 
// Transmitir los mensajes en secuencia por RF4333
void transmite()
{
  digitalWrite(13,HIGH);
  codifica();
  int i = 0;
  for (i = 0; i < N_MENSAJES; i++)
  {
    rcswitch.send(mensaje[i], 24);
    delay(50);
  }
  digitalWrite(13,LOW);
}


 
void setup()
{
  //Serial.begin(9600);
  //Serial.println("SSPMeteo.");
    
  // Para el conteo de lluvia
  pinMode(LLUVIA_PIN,INPUT_PULLUP);
  attachInterrupt(LLUVIA_INT,cuenta_lluvia,FALLING);
  
  // Para el conteo del anemometro
  pinMode(ANEMOM_PIN,INPUT_PULLUP);
  attachInterrupt(ANEMOM_INT,cuenta_anemom,FALLING);
  
  // Prepara el sensor DHT22
  dht.begin();
  
  // Prepara la transmision RF433
  pinMode(13,OUTPUT);  // Este LED durante la transmision
  rcswitch.enableTransmit(RF433_PIN);
  rcswitch.setRepeatTransmit(20);
  
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
      //sendData();
      transmite();
      
      intervalo = 0;
      vel_vent = 0.0;
      vel_racha = 0.0;
    }
    timer_lectura += INTERVALO_BASE;
  }
}


