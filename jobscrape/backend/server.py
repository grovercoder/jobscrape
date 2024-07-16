from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/app/site/add")
def app_sites():
    return render_template("sites_form.html")