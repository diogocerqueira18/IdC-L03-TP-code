from datetime import datetime
import paho.mqtt.client as mqtt 
import time
import pandas as pd
import json

def readCSV():
    fitness_data = pd.read_csv('data/Fitness_online.csv', sep=';')

    model = "fitness-LDA"

    data_list = []

    for index, row in fitness_data.iterrows():
        data_dict = {
            "acceleration_x": row['acceleration_x'],
            "acceleration_y": row['acceleration_y'],
            "acceleration_z": row['acceleration_z'],
            "gyro_x": row['gyro_x'],
            "gyro_y": row['gyro_y'],
            "gyro_z": row['gyro_z'],
            "time": "",
            "date": ""
        }
        data_list.append([{"model": model}, data_dict])
    return data_list 


broker_hostname = "localhost"
port = 1883 

def on_connect(client, userdata, flags, return_code):
    if return_code == 0:
        print("connected")
    else:
        print("could not connect, return code:", return_code)

client = mqtt.Client("Client1")
# client.username_pw_set(username="user_name", password="password") # uncomment if you use password auth
client.on_connect=on_connect

client.connect(broker_hostname, port)
client.loop_start()

topic = "idc/fc15"
msg_count = 0

msg = readCSV()

try:
    while msg_count < len(msg):
        time.sleep(1)
        
        now = datetime.now()

        date = now.strftime("%d/%m/%y")
        time_str = now.strftime("%H:%M:%S:%f")
        msg[msg_count][1]["date"] = date
        msg[msg_count][1]["time"] = time_str


        result = client.publish(topic, json.dumps(msg[msg_count]))
        status = result[0]
        if status == 0:
            print("Message "+ str(msg[msg_count]) + " is published to topic " + topic)
        else:
            print("Failed to send message to topic " + topic)
        msg_count += 1
finally:
    client.loop_stop()
