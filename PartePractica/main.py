# Importamos las bibliotecas necesarias para la conexión a la red y MQTT
import network
from umqtt.simple import MQTTClient  # Protocolo MQTT para comunicación con el broker

# Importamos módulos para controlar hardware
from machine import Pin  # Manejo de pines GPIO
from time import sleep  # Pausas en la ejecución
from hcsr04 import HCSR04  # Control del sensor de ultrasonido

# Configuración del servidor MQTT
MQTT_BROKER = "broker.emqx.io"  # Dirección del broker
MQTT_USER = ""  # Usuario (vacío si no se requiere autenticación)
MQTT_PASSWORD = ""  # Contraseña (vacío si no se requiere autenticación)
MQTT_CLIENT_ID = ""  # Identificador único del cliente
MQTT_TOPIC = "utng/sensor"  # Tema donde se enviarán los datos
MQTT_PORT = 1883  # Puerto estándar de MQTT

# Inicializamos el sensor de distancia con los pines correspondientes
sensor = HCSR04(trigger_pin=16, echo_pin=4, echo_timeout_us=24000)

# Configuración de pines para los LEDs (simulando un semáforo)
led_rojo = Pin(2, Pin.OUT)  # LED rojo
led_amarillo = Pin(5, Pin.OUT)  # LED amarillo
led_verde = Pin(18, Pin.OUT)  # LED verde

# Aseguramos que todos los LEDs inicien apagados
led_rojo.value(0)
led_amarillo.value(0)
led_verde.value(0)

# Función para conectar a una red WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)  # Creamos un objeto para manejar la conexión WiFi
    sta_if.active(True)  # Activamos la interfaz WiFi
    sta_if.connect('Red-Peter', '12345678')  # Nos conectamos con la red WiFi
    while not sta_if.isconnected():  # Esperamos a que la conexión sea exitosa
        print(".", end="")
        sleep(0.3)
    print("¡WiFi conectado!")

# Función para suscribirse a un broker MQTT y recibir mensajes

def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID,
                        MQTT_BROKER, port=MQTT_PORT,
                        user=MQTT_USER,
                        password=MQTT_PASSWORD,
                        keepalive=0)
    client.set_callback(llegada_mensaje)  # Definimos qué hacer cuando llega un mensaje
    client.connect()  # Nos conectamos al broker
    client.subscribe(MQTT_TOPIC)  # Nos suscribimos al tema MQTT
    print("Conectado a %s, en el tópico %s" % (MQTT_BROKER, MQTT_TOPIC))
    return client

# Función que se ejecuta cuando llega un mensaje al tópico MQTT

def llegada_mensaje(topic, msg):
    print("Mensaje recibido:", msg)

# Función que enciende los LEDs dependiendo de la distancia detectada

def controlar_leds(distancia):
    # Apagamos todos los LEDs antes de encender el necesario
    led_rojo.value(0)
    led_amarillo.value(0)
    led_verde.value(0)

    # Encendemos el LED correspondiente según la distancia
    if distancia < 10:
        led_rojo.value(1)  # Distancia peligrosa (Rojo encendido)
    elif 10 <= distancia < 20:
        led_amarillo.value(1)  # Distancia moderada (Amarillo encendido)
    else:
        led_verde.value(1)  # Distancia segura (Verde encendido)

# Conectamos a WiFi antes de iniciar la comunicación MQTT
conectar_wifi()

# Nos suscribimos al broker MQTT para enviar y recibir datos
client = subscribir()

# Variable para evitar enviar datos repetidos si la distancia no cambia
distancia_anterior = 0

# Bucle principal del programa
while True:
    client.check_msg()  # Revisamos si hay mensajes nuevos en el tema MQTT
    distancia = int(sensor.distance_cm())  # Leemos la distancia en centímetros
    if distancia != distancia_anterior:  # Solo enviamos datos si la distancia cambia
        print(f"La distancia es {distancia} cm.")
        client.publish(MQTT_TOPIC, str(distancia))  # Enviamos la distancia al broker MQTT
        controlar_leds(distancia)  # Actualizamos los LEDs según la distancia detectada
    distancia_anterior = distancia  # Guardamos la última distancia medida
    sleep(2)  # Esperamos 2 segundos antes de la siguiente lectura