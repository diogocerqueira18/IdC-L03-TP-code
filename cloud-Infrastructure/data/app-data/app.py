import paho.mqtt.client as mqtt
import mysql.connector

# Configurações de conexão com o banco de dados
db_config = {
    'host': 'db',  # Nome do serviço MySQL conforme definido no docker-compose.yml
    'user': 'admin',
    'password': 'root',
    'database': 'dbIOT'
}

import paho.mqtt.client as mqtt
import mysql.connector
import json

db_config = {
    'host': 'db',  
    'user': 'admin',
    'password': 'root',
    'database': 'dbIOT'
}

def insert_data_into_db(data):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "INSERT INTO Activities (Date, ActivityType, Distance, Duration, CaloriesBurned) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data['Date'], data['ActivityType'], data['Distance'], data['Duration'], data['CaloriesBurned']))

        connection.commit()
        cursor.close()
        connection.close()
        print("Dados inseridos na base de dados com sucesso!")
    except mysql.connector.Error as err:
        print("Erro ao inserir dados na base de dados:", err)

def on_connect(client, userdata, flags, return_code):
    if return_code == 0:
        print("Conectado ao MQTT Broker")
        client.subscribe("idc/fitness")
    else:
        print("Não foi possível conectar, código de retorno:", return_code)

def on_message(client, userdata, message):
    received_data = str(message.payload.decode("utf-8"))
    print("Dados recebidos:", received_data)
    data_dict = json.loads(received_data)
    insert_data_into_db(data_dict)

broker_hostname = "localhost"
port = 1883

client = mqtt.Client("Client1")
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_hostname, port)
client.loop_forever()