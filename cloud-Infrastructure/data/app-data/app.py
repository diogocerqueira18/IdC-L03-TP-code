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


if __name__ == '__main__':
    app.run(debug=True)
