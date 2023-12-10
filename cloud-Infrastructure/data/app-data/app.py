from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import joblib
import mysql.connector 
from modules.functions import get_model_response

app = Flask(__name__)

db_config = {
    'host': 'db',  
    'user': 'root',
    'password': 'root',
    'database': 'dbIOT'
}

@app.route('/velocity', methods=['POST'])
def get_velocity():
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Body is empty.'}, 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT Velocity FROM Velocities WHERE Range_start <= %s AND Range_finished >= %s AND Genre = %s"
        cursor.execute(query, (data['Age'], data['Age'], data['Gender']))
        velocity = cursor.fetchone()

        cursor.close()
        connection.close()

        if velocity:
            return jsonify({'velocity': float(velocity[0])}), 200
        else:
            return jsonify({'error': 'Velocity not found for the given parameters'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    
@app.route('/predict', methods=['POST'])
def predict():
    feature_dict = request.get_json()
    if not feature_dict:
        return {
            'error': 'Body is empty.'
        }, 500

    try:
        data = []
        feature_dict[1].pop('time', None)
        feature_dict[1].pop('date', None)
        model_name = feature_dict[0]['model']
#        print(model_name)
        data.append(feature_dict[1])
        print(data)
        model = joblib.load('model/' + model_name + '.dat.gz')

        response = get_model_response(data, model)
    except ValueError as e:
        return {'error': str(e).split('\n')[-1].strip()}, 500

    return response, 200

@app.route('/insert', methods=['POST'])
def insert_data_into_db():
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Body is empty.'}, 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "INSERT INTO Activities (Date, ActivityType, Distance, Duration, CaloriesBurned) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data['Date'], data['ActivityType'], data['Distance'], data['Duration'], data['CaloriesBurned']))

        connection.commit()
        cursor.close()
        connection.close()

        return {'message': 'Data inserted successfully'}, 201

    except mysql.connector.Error as err:
        return {'error': str(err)}, 500
    
@app.route('/activities', methods=['GET'])
def get_activities():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT * FROM Activities"
        cursor.execute(query)
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        activities_list = []
        for row in data:
            activity = {
                'ActivityID': row[0],
                'Date': row[1].strftime("%Y-%m-%d"),
                'ActivityType': row[2],
                'Distance': float(row[3]),
                'Duration': str(row[4]),
                'CaloriesBurned': float(row[5])
            }
            activities_list.append(activity)

        return jsonify(activities_list), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/login', methods=['POST'])
def get_user():
    feature_dict = request.get_json()
    if not feature_dict:
        return {
            'error': 'Body is empty.'
        }, 500
    try:
        username = feature_dict['username']
        password = feature_dict['password']
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT * FROM Users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        print(user)
        if user is not None and user[1] == password:
            return username, 200
        else:
            return {'error': 'User not found'}, 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/register', methods=['POST'])
def register():
    user_data = request.get_json()
    if not user_data:
        return {'error': 'Body is empty.'}, 400
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query_exists = "SELECT * FROM Users WHERE username = %s"
        cursor.execute(query_exists, (user_data['username'],))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'error': 'User already exists'}), 409

        query_insert = "INSERT INTO Users (username, password, Name, Age, Gender, Weight, Height) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query_insert, (user_data['username'], user_data['password'], user_data['name'], user_data['age'], user_data['gender'],
                               user_data['weight'], user_data['height'],))
        
        connection.commit()

        return {'message': 'User created successfully'}, 201
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/user/<string:username>', methods=['GET'])
def user(username):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = "SELECT * FROM Users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if user is not None:
            response = {
                "name": user[2],
                "age": user[3],
                "gender": user[4],
                "weight": user[5],
                "height": user[6]
            }
            return response, 200
        else:
            return {'error': 'User not found'}, 404
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()  


@app.route('/all_today', methods=['GET'])
def get_today_activities():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        current_date = datetime.now().strftime("%Y-%m-%d")
        #current_date = "2023-07-10"
        query = "SELECT * FROM Activities WHERE Date = %s"
        cursor.execute(query, (current_date,))
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        

        results = [0, 0, 0, 0, 0, 0]
        for row in data:
            print(type(row[5]))
            if row[2] == 0:
                results[0] += row[3]  # distance_walk
                results[2] += row[5]  # calories_walk
                results[4] += row[4].seconds  # time_walk
            elif row[2] == 1:
                results[1] += row[3]  # distance_run
                results[3] += row[5]  # calories_run
                results[5] += row[4].seconds  # time_run

        temp = {
            "distance_walk": results[0],
            "distance_run": results[1],
            "calories_walk": results[2],
            "calories_run": results[3],
            "time_walk": results[4],
            "time_run": results[5]
        }

        return temp, 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()  


@app.route('/all_month', methods=['GET'])
def get_month_activities():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        current_month = datetime.now().month
        current_year = datetime.now().year

        #current_month = datetime.strptime("2023-07-10", "%Y-%m-%d").month
        #current_year = datetime.strptime("2023-07-10", "%Y-%m-%d").year

        query = "SELECT * FROM Activities WHERE YEAR(Date) = %s AND MONTH(Date) = %s"
        cursor.execute(query, (current_year, current_month))
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        results = [0, 0, 0, 0, 0, 0]
        for row in data:
            if row[2] == 0:
                results[0] += row[3]  # distance_walk
                results[2] += row[5]  # calories_walk
                results[4] += row[4].seconds  # time_walk
            if row[2] == 1:
                results[1] += row[3]  # distance_run
                results[3] += row[5]  # calories_run
                results[5] += row[4].seconds  # time_run    

        temp = {
            "distance_walk": results[0],
            "distance_run": results[1],
            "calories_walk": results[2],
            "calories_run": results[3],
            "time_walk": results[4],
            "time_run": results[5]
        }
        return temp, 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close() 

@app.route('/all_week', methods=['GET'])
def get_week_activities():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        #current_month = datetime.now().month
        #current_year = datetime.now().year

        data_atual = datetime.now()
        primeiro_dia_semana = data_atual - timedelta(days=data_atual.weekday())
        ultimo_dia_semana = primeiro_dia_semana + timedelta(days=6)

        query = "SELECT * FROM Activities WHERE Date BETWEEN %s AND %s"
        cursor.execute(query, (primeiro_dia_semana, ultimo_dia_semana))
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        dias_da_semana = [0, 1, 2, 3, 4, 5, 6]

        valores_semana = {}
        for dia in dias_da_semana:
            results = [0, 0, 0, 0, 0, 0]
            for row in data:
                if row[1].weekday() == dia:
                    if row[2] == 0:
                        results[0] += row[3]  # distance_walk
                        results[2] += row[5]  # calories_walk
                        results[4] += row[4].seconds  # time_walk
                    if row[2] == 1:
                        results[1] += row[3]  # distance_run
                        results[3] += row[5]  # calories_run
                        results[5] += row[4].seconds  # time_run     

            temp = {
                "distance_walk": results[0],
                "distance_run": results[1],
                "calories_walk": results[2],
                "calories_run": results[3],
                "time_walk": results[4],
                "time_run": results[5]
            }
            valores_semana[dia] = temp

        temp = {
            "Segunda": valores_semana[0],
            "Terça": valores_semana[1],
            "Quarta": valores_semana[2],
            "Quinta": valores_semana[3],
            "Sexta": valores_semana[4],
            "Sabado": valores_semana[5],
            "Domingo": valores_semana[6]
        }
        return temp, 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close() 

@app.route('/months', methods=['GET'])
def get_months():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        primeiro_dia = datetime(2023,1,1)
        ultimo_dia = datetime(2023,12,31)

        query = "SELECT * FROM Activities WHERE Date BETWEEN %s AND %s"
        cursor.execute(query, (primeiro_dia, ultimo_dia))
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        meses = [0, 1, 2, 3, 4, 5, 6,7,8,9,10,11]
        valores_meses ={}
        for mes in meses:
            result = 0
            for row in data:
                if row[1].month == mes+1:
                    result += row[4].seconds

            temp = {
                "time": result
            }
            valores_meses[mes] = temp

        temp = {
            "Janeiro": valores_meses[0],
            "Fevereiro": valores_meses[1],
            "Março": valores_meses[2],
            "Abril": valores_meses[3],
            "Maio": valores_meses[4],
            "Junho": valores_meses[5],
            "Julho": valores_meses[6],
            "Agosto": valores_meses[7],
            "Setembro": valores_meses[8],
            "Outubro": valores_meses[9],
            "Novembro": valores_meses[10],
            "Dezembro": valores_meses[11]
        }
        return temp, 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/changeAge', methods=['POST'])
def changeAge():
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Body is empty.'}, 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "UPDATE Users SET Age = %s WHERE username = %s"
        cursor.execute(query, (data['Age'], data['username']))
        user = cursor.fetchone()

        if cursor.rowcount > 0:
            connection.commit()
            return {'message': 'Age updated successfully'}, 201
        else:
            return {'error': 'User not found'}, 404
        

    except mysql.connector.Error as err:
        return {'error': str(err)}, 500
    finally:
        cursor.close()
        connection.close()

@app.route('/changeWeight', methods=['POST'])
def changeWeight():
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Body is empty.'}, 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "UPDATE Users SET Weight = %s WHERE username = %s"
        cursor.execute(query, (data['weight'], data['username']))
        user = cursor.fetchone()

        if cursor.rowcount > 0:
            connection.commit()
            return {'message': 'Weight updated successfully'}, 201
        else:
            return {'error': 'User not found'}, 404
        

    except mysql.connector.Error as err:
        return {'error': str(err)}, 500
    finally:
        cursor.close()
        connection.close()       

@app.route('/changeHeight', methods=['POST'])
def changeHeight():
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Body is empty.'}, 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "UPDATE Users SET Height = %s WHERE username = %s"
        cursor.execute(query, (data['height'], data['username']))
        user = cursor.fetchone()

        if cursor.rowcount > 0:
            connection.commit()
            return {'message': 'Height updated successfully'}, 201
        else:
            return {'error': 'User not found'}, 404
        

    except mysql.connector.Error as err:
        return {'error': str(err)}, 500
    finally:
        cursor.close()
        connection.close()         

if __name__ == '__main__':
    app.run(debug=True)
