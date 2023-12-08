import pandas as pd
from datetime import datetime
import mysql.connector 

db_config = {
    'host': '127.0.0.1',  
    'user': 'root',
    'password': 'root',
    'database': 'dbIOT'
}

df = pd.read_csv('Fitness_training.csv', sep=';')


# Conectar ao banco de dados MySQL
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Inserir dados na tabela
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO training 
        (date, time, activity, acceleration_x, acceleration_y, acceleration_z, gyro_x, gyro_y, gyro_z)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, tuple(row))

# Commit e fechar conexão
conn.commit()
conn.close()
