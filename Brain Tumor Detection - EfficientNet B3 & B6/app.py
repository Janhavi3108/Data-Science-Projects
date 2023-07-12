from __future__ import division, print_function
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import logging
from logging.handlers import RotatingFileHandler
from waitress import serve

# coding=utf-8
import sys
import os
import cv2
import glob
import numpy as np

# Keras

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Flask utils
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

os.environ["CUDA_VISIBLE_DEVICES"]="-1"
 
 
app = Flask(__name__)

@app.after_request
def after_request(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# # Set up logging
# handler = RotatingFileHandler('app.log', maxBytes=10000000000000, backupCount=1)
# handler.setLevel(logging.INFO)
# app.logger.addHandler(handler)
# app.logger.disabled = False
# app.logger.setLevel(logging.INFO)
 
app.secret_key = 'Gintoki@1010'
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'janhavi@3108'
app.config['MYSQL_DB'] = 'pythonlogin'
 
mysql = MySQL(app)
 
@app.route('/')

@app.route("/")
def start():
    return render_template("startpage.html")

@app.route('/startlogin')
def startlogin():
    return redirect(url_for('login'))

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
 
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)   

# Model saved with Keras model.save()
MODEL_PATH = 'models\EfficientNetB6_Final.h5'

#Load your trained model
model = load_model(MODEL_PATH)
#model._make_predict_function()          # Necessary to make everything ready to run on the GPU ahead of time
print('Model loaded. Start serving...')



def model_predict(img_path, model):
    img = cv2.imread(img_path) #target_size must agree with what the trained model expects!!

    # Preprocessing the image
    img = cv2.resize(img,(224,224))     # resize image to match model's expected sizing
    img = img.reshape(1,224,224,3)
    #img = image.img_to_array(img)
    #img = np.expand_dims(img, axis=0)
    #img = img.astype('float32')/255

    preds = model.predict(img)

   
   
    classes = np.argmax(preds,axis = 1)
    return classes


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']
        
        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)

        # Make prediction
        classes = model_predict(file_path, model)
       # os.remove(file_path)#removes file from the server after prediction has been returned

        # Arrange the correct return according to the model. 
		# In this model 1 is Pneumonia and 0 is Normal.
        str0 = 'Glioma'
        str1 = 'Meningioma'
        str3 = 'Pituitary'
        str2 = 'No Tumour'
        if classes == 0:
            return str0
        elif classes == 1:
            return str1
        elif classes == 3:
            return str3
        else:
            return str2      
    return None

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080, threads=10)