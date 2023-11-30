import paho.mqtt.client as mqtt
import mysql.connector

# Configurações de conexão com o banco de dados
db_config = {
    'host': 'db',  # Nome do serviço MySQL conforme definido no docker-compose.yml
    'user': 'root',
    'password': 'root',
    'database': 'dbIOT'
}

def connect_to_db():
    return mysql.connector.connect(**db_config)

def insert_data_into_db(data):
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Exemplo de inserção de dados na tabela 'nome_da_tabela'
        query = "INSERT INTO nome_da_tabela (campo1, campo2, campo3) VALUES (%s, %s, %s)"
        cursor.execute(query, (data['campo1'], data['campo2'], data['campo3']))

        connection.commit()
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        print("Erro ao inserir dados no banco de dados:", err)

def on_connect(client, userdata, flags, return_code):
    if return_code == 0:
        print("Conectado ao MQTT Broker")
        client.subscribe("idc/fitness")
    else:
        print("Não foi possível conectar, código de retorno:", return_code)

def on_message(client, userdata, message):
    received_data = str(message.payload.decode("utf-8"))
    print("Dados recebidos:", received_data)

    # Supondo que você tem os dados em formato JSON, você pode converter para dicionário
    data_dict = json.loads(received_data)

    # Função para inserir dados no banco de dados
    insert_data_into_db(data_dict)

broker_hostname = "localhost"
port = 1883

client = mqtt.Client("Client2")
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_hostname, port)
client.loop_forever()
