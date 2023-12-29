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
    observations = list(db.observations.find())
    return render_template("obseravtions.html", observations=observations)


@app.route("/my_nest/", methods=["GET", "POST"])
def my_nest():
    observations = list(db.observations.find())
    return render_template("my_nest.html", observations=observations)


@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "email": request.form.get("email"),
            "experience": request.form.get("experience")
        }
        db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful! Welcome, {}!".format(request.form.get("username")))
        return redirect(url_for("my_nest"))
    
    return render_template("register.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}!".format(request.form.get("username")))
                    return redirect(url_for("profile"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/", methods=["GET", "POST"])
def profile():
    username = db.users.find_one(
        {"username": session["user"]})["username"]
    
    if session["user"]:
            return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout/")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_observation/", methods=["GET", "POST"])
def add_observation():
    if request.method == "POST":
        entry = {
            "bird_species": request.form.get("bird"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "seen_by": session["user"],
            "certainty": request.form.get("certainty"),
            "notes": request.form.get("notes"),
            "quantity": request.form.get("quantity")
        }
        db.observations.insert_one(entry)
        flash("Observation added to your nest")
        return redirect(url_for("my_nest"))
            
    return render_template("add_observation.html")


@app.route("/edit_observations", strict_slashes=False)
@app.route("/edit_observation/<observation_id>", methods=["GET", "POST"])
def edit_observation(observation_id):
    if request.method == "POST":
        entry = {
            "bird_species": request.form.get("bird"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "seen_by": session["user"],
            "certainty": request.form.get("certainty"),
            "notes": request.form.get("notes"),
            "quantity": request.form.get("quantity")
        }
        db.observations.replace_one({"_id": ObjectId(observation_id)}, entry)
        flash("Observation updated")
        return redirect(url_for("my_nest"))

    observation = db.observations.find_one({"_id": ObjectId(observation_id)})
    return render_template("edit_observation.html", observation=observation)


@app.route("/delete_observations", strict_slashes=False)
@app.route("/delete_observation/<observation_id>")
def delete_observation(observation_id):
    
    db.observations.delete_one({"_id": ObjectId(observation_id)})
    flash("Observation deleted")
    return redirect(url_for("get_observations"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)


