# -*- coding: utf-8 -*-

from scripts import tabledef
from scripts import forms
from scripts import helpers
import keras
import tensorflow as tf
from keras.models import load_model
from flask import Flask, redirect, url_for, render_template, request, session
import json
import sys
import stripe
import os
from keras.preprocessing import image
import fastai
from werkzeug.utils import secure_filename
from fastai.vision import *

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only

stripe_keys = {
  'secret_key': 'sk_test_9cBvYnidXQdQAhxd5zDgUVt4',#os.environ['STRIPE_SECRET_KEY'],
  'publishable_key':'pk_test_1jKluzjGp6msb5WwL2PoLgCM'# os.environ['STRIPE_PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']

# Heroku
#from flask_heroku import Heroku
#heroku = Heroku(app)

## https://testdriven.io/blog/adding-a-custom-stripe-checkout-to-a-flask-app/
# ======== Routing =========================================================== #

@app.route('/stripe', methods=['GET'])
def index():
    return render_template('stripe.html', key=stripe_keys['publishable_key'])


# -------- Login ------------------------------------------------------------- #
@app.route('/', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form)
    user = helpers.get_user()
    user.active = user.payment == helpers.payment_token()
    user.key = stripe_keys['publishable_key']
    return render_template('home.html', user=user)

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))

# -------- Charge ---------------------------------------------------------- #
@app.route('/charge', methods=['POST'])
def charge():
    if session.get('logged_in'):
        user = helpers.get_user()
        try:
            amount = 1000   # amount in cents
            customer = stripe.Customer.create(
                email= user.email,
                source=request.form['stripeToken']
            )
            stripe.Charge.create(
                customer=customer.id,
                amount=amount,
                currency='eur',
                description='Discount Optimizer Charge'
            )
            helpers.change_user(payment=helpers.payment_token())
            user.active = True
            return render_template('home.html', user=user)
        except stripe.error.StripeError:
            return render_template('error.html')

# -------- Model ---------------------------------------------------------- #

@app.route('/predict', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        img = open_image(file_path)
        
        learn = load_learner('models')

        pred,idx,outputs = learn.predict(img)
        print('Predicted class: ', pred)
        img
        if int(pred.__str__()) == 1:
            return "Palm oil plantation: YES"
        elif int(pred.__str__()) == 0:
            return "Palm oil plantation: NO"



# MODEL_PATH = 'models/image_classifier.h5'

# model = load_model(MODEL_PATH)
# model._make_predict_function()

# def init():
#     global model
#     model = load_model('image_classifier.h5')
# global graph
# graph = tf.get_default_graph()
#     #return graph


# def model_predict(img_path, model):
#     img = image.load_img(img_path, target_size=(224, 224))

#     x = image.img_to_array(img)
#     x = np.expand_dims(x, axis=0)

#     x = preprocess_input(x)

#     preds = model.predict(x)
#     return preds

# @app.route('/predict', methods = ['GET', 'POST'])
# def upload_file():
#     print(df)
#     if request.method == 'POST':
#         f = request.files['file']
#         basepath = os.path.dirname(__file__)
#         file_path = os.path.join(
#             basepath, 'uploads', secure_filename(f.filename))
#         f.save(file_path)

#         with graph.as_default():
#             preds = model_predict(file_path, model)

#             pred_class = preds.argmax(axis=-1)
#             result = str(pred_class[0])
#             return result

#     return None

# ======== Main ============================================================== #
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
