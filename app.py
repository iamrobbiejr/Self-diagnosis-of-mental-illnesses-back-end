from flask import Flask, render_template, request, json, jsonify
from flask.wrappers import Response
from flask_mysqldb import MySQL
from flask_cors import CORS, cross_origin
from questions import ptsd_questions, adhd_questions, schizophrenia_questions, depression_questions, \
    eatingdisorders_questions, general_questions
import numpy as np
import pandas as pd
import pickle

ptsd_model = pickle.load(open('PTSD_model.pkl', 'rb'))
adhd_model = pickle.load(open('ADHD_model.pkl', 'rb'))
schizophrenia_model = pickle.load(open('Schizophrenia_model.pkl', 'rb'))
depression_model = pickle.load(open('Depression_model.pkl', 'rb'))
eatingdisorders_model = pickle.load(open('Eatingdisorders_model.pkl', 'rb'))
general_model = pickle.load(open('General_model.pkl', 'rb'))

ml_models = [general_model, ptsd_model, adhd_model, schizophrenia_model, depression_model, eatingdisorders_model]
question_sets = [general_questions, ptsd_questions, adhd_questions, schizophrenia_questions, depression_questions,
                 eatingdisorders_questions, ]

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "mental_health"

mysql = MySQL(app)


@app.route('/')
def index():
    print(set1)
    return render_template('index.html')


@app.route('/users')
def users():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * from student')

    userDetails = cur.fetchall()
    print(userDetails)
    return render_template('users.html', users=userDetails)


@app.route('/register', methods=['GET', 'POST'])
@cross_origin()
def register():
    if request.method == 'POST':
        data = json.loads(request.data)
        email = data['email']
        password = data['password']
        cur = mysql.connection.cursor()
        cur.execute('select * from user_login where email = %s', [email])
        result = cur.fetchall()
        print(result)
        if len(result) > 0:
            response = jsonify(message="Already email exists")
        else:
            cur.execute('INSERT into user_login (email,password) values(%s,%s)', (email, password))
            mysql.connection.commit()
            cur.execute('select user_id from user_login where email=%s', [email])
            result = cur.fetchone()
            print(result)
            res = {
                "msg": "success",
                "id": result[0
                ]
            }
            response = jsonify(res)
        return response


@app.route('/loginuser', methods=['GET', 'POST'])
@cross_origin()
def loginuser():
    if request.method == 'POST':
        data = json.loads(request.data)
        email = data['email']
        password = data['password']
        cur = mysql.connection.cursor()
        cur.execute('select * from user_login where email = %s', [email])
        result = cur.fetchall()
        print(result)
        if len(result) > 0:
            cur.execute('select user_id from user_login where email=%s and password=%s', [email, password])
            result = cur.fetchone()
            print(result)
            if result == None:
                response = jsonify(message="incorrect password")
            else:
                r = result
                res = {
                    "msg": "success",
                    "id": r[0]
                }
                response = jsonify(res)
        else:
            response = jsonify(message="please register to continue")
        return response


@app.route('/login', methods=['GET', 'POST'])
@cross_origin()
def login():
    if request.method == 'POST':
        data = json.loads(request.data)
        print(data['email'])
        email = data['email']
        name = data['name']
        googleid = data['googleid']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * from login_with_google where email=%s', [email])
        result = cur.fetchall()
        print("result-----", result)
        if len(result) > 0:
            # response = jsonify(message="Already email exists")
            cur.execute('select user_id from login_with_google where email=%s', [email])
            result = cur.fetchone()
            print(result)
            res = {
                "msg": "success",
                "id": result[0
                ],
                "email": email,
            }
            response = jsonify(res)
        else:
            cur.execute('INSERT into login_with_google (email,name,google_id) values(%s,%s,%s)',
                        (email, name, googleid))
            mysql.connection.commit()
            cur.execute('select user_id from login_with_google where email=%s', [email])
            result = cur.fetchone()
            print(result)
            res = {
                "msg": "success",
                "id": result[0
                ],
                "email": email,
            }
            response = jsonify(res)
        return response
    return "success"


@app.route("/questions", methods=['GET', 'POST'])
def questions():
    if request.method == 'GET':
        args = request.args
        id = args['id']
        cur = mysql.connection.cursor()
        cur.execute('select questionset_id from user_activity where user_id=%s order by date desc', [id])
        result = cur.fetchone()
        if (result):
            set_id = int(result[0])
            new_set_id = (set_id + 1) % 6
        else:
            new_set_id = 0
        print("------", result)
        response = jsonify(question_sets[new_set_id])
    if request.method == 'POST':
        data = json.loads(request.data)
        print(data)
        print(data['answer'])
        id = int(data['id'])
        print("id-----", id)
        cur = mysql.connection.cursor()
        cur.execute('select questionset_id from user_activity where user_id=%s order by date desc', [id])
        result_of_set = cur.fetchone()
        if (result_of_set):
            set_id = int(result_of_set[0])
            new_set_id = (set_id + 1) % 6
        else:
            new_set_id = 0
        ans = []
        for x in data['answer']:
            if x['answer'] == "Yes":
                ans.append('1')
            elif x['answer'] == "No":
                ans.append('0')
            elif x['answer'] == "Somewhat":
                ans.append('0.5')
            else:
                ans.append(x['answer'])
        print("-------", ans)
        init_features = [float(x) for x in ans]
        print("--------", init_features)
        final_features = [np.array(init_features)]
        print("final---------", final_features)
        final = pd.DataFrame(final_features)
        predict = ml_models[new_set_id].predict(final)
        output = round(predict[0], 2)
        result = int(output)

        cur.execute('INSERT into user_activity (user_id,result,questionset_id) values(%s,%s,%s)',
                    (id, result, new_set_id))
        mysql.connection.commit()
        print("Prediction----", output)
        res = {
            "prediction": int(output),
            "message": "Success"
        }
        response = jsonify(res)
        # response=jsonify(message="success")
    return response


@app.route("/changepassword", methods=['POST'])
def changePassword():
    if request.method == 'POST':
        data = json.loads(request.data)
        print(data)
        id = data['id']
        oldpassword = data['oldpassword']
        newpassword = data['newpassword']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * from user_login where user_id=%s', [id])
        result = cur.fetchall()
        print("result-----", result[0][2])
        password = result[0][2]
        if password == oldpassword:
            cur.execute("UPDATE user_login set password=%s where user_id=%s", [newpassword, id])
            mysql.connection.commit()
            response = jsonify(message="successfully updated")
        else:
            response = jsonify(message="Wrong password")
    return response


if __name__ == '__main__':
    app.run(debug=True)
