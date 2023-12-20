import os
from flask import (
    Flask, Blueprint, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__, template_folder='templates')

import pymongo


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
db = client["birdcount"]


@app.route("/")
@app.route("/welcome/")
def welcome():
    return render_template("welcome.html")


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/get_observations/")
def get_observations():
    observations = db.observations.find()
    return render_template("obseravtions.html", observations=observations)


@app.route("/my_nest/")
def my_nest():
    return render_template("my_nest.html")


@app.route("/register/", methods=["GET", "POST"])
def register():
    return render_template("register.html")


@app.route("/log_in/", methods=["GET", "POST"])
def log_in():
    return render_template("log_in.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
