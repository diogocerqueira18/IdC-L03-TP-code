from flask import Flask, request, jsonify
import joblib
import mysql.connector 
from modules.functions import get_model_response

app = Flask(__name__)

db_config = {
    'host': 'db',  
    'user': 'admin',
    'password': 'root',
    'database': 'dbIOT'
}

@app.route('/predict', methods=['POST'])
def predict():
    feature_dict = request.get_json()
    if not feature_dict:
        return {
            'error': 'Body is empty.'
        }, 500

    try:
        data = []
        model_name = feature_dict[0]['model']
#        print(model_name)
        data.append(feature_dict[1])
#        print(data)
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

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT * FROM Users WHERE UserID = %s"
        cursor.execute(query, (user_id,))
        data = cursor.fetchone()

        cursor.close()
        connection.close()

        if data:
            user = {
                'Age': data[2],
                'Gender': data[3],
                'Weight': float(data[4]),
                'Height': float(data[5]),
                'Goal': int(data[6])
            }
            return jsonify(user), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = request.get_json()
        if not user_data:
            return {'error': 'Body is empty.'}, 400

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "INSERT INTO Users (UserName, Age, Gender, Weight, Height, Goal) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (user_data['UserName'], user_data['Age'], user_data['Gender'],
                               user_data['Weight'], user_data['Height'], user_data['Goal']))
        
        connection.commit()
        cursor.close()
        connection.close()

        return {'message': 'User created successfully'}, 201
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/velocity', methods=['GET'])
def get_velocity():
    try:
        age = int(request.args.get('age'))
        gender = request.args.get('gender')
        gender_value = 1 if gender.lower() == 'female' else 0

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT Velocity FROM Velocities WHERE Range_start <= %s AND Range_finished >= %s AND Genre = %s"
        cursor.execute(query, (age, age, gender_value))
        velocity = cursor.fetchone()

        cursor.close()
        connection.close()

        if velocity:
            return jsonify({'velocity': float(velocity[0])}), 200
        else:
            return jsonify({'error': 'Velocity not found for the given parameters'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
