import os
from flask import (
    Flask, Blueprint, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
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
    observations = list(db.observations.find().sort("date", -1))
    anonymous_users = list(db.users.find({"anonymous": True}, {"_id": 1}))
    anonymous_user_ids = list(user["_id"] for user in anonymous_users)
    print(anonymous_users)
    print(anonymous_user_ids)
    for user_id in anonymous_user_ids:
        db.observations.update_many(
            {"_id": ObjectId(user_id)},
            {"$set": {"anonymous": False}}
        )
    
    return render_template("observations.html", observations=observations)


@app.route("/get_users/")
def get_users():
    users = list(db.users.find())
    return render_template("admin.html", users=users)


@app.route("/view_messages/")
def view_messages():
    messages = list(db.messages.find())
    return render_template("messages.html", messages=messages)


@app.route("/delete_user", strict_slashes=False)
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    db.users.delete_one({"_id": ObjectId(user_id)})
    flash("User successfully deleted")
    if session["user"] == 'admin':
        return redirect(url_for("get_users"))
    else:
        return redirect(url_for("logout"))


@app.route("/edit_user_email", strict_slashes=False)
@app.route("/edit_user_email/<user_id>", methods=["GET", "POST"])
def edit_user_email(user_id):
    if request.method == "POST":
        user = ObjectId(user_id)
        new_email = request.form.get("email-edit")
        db.users.update_one(
            {'_id': user},
            {'$set': {'email': new_email}}
        )
        flash("Email updated")
        return redirect(url_for("my_nest"))


@app.route("/edit_user_experience", strict_slashes=False)
@app.route("/edit_user_experience/<user_id>", methods=["GET", "POST"])
def edit_user_experience(user_id):
    if request.method == "POST":
        user = ObjectId(user_id)
        new_experience = request.form.get("experience-edit")
        db.users.update_one(
            {'_id': user},
            {'$set': {'experience': new_experience}}
        )
        flash("Experience updated")
        return redirect(url_for("my_nest"))


@app.route("/edit_user_visibility", strict_slashes=False)
@app.route("/edit_user_visibility/<user_id>", methods=["GET", "POST"])
def edit_user_visibility(user_id):
    if request.method == "POST":
        user = ObjectId(user_id)
        username = session["user"]
        visible = request.form.get("visibility-switch")
        
        if visible == "on":
            visible = True
        elif visible == "None":
            visible = False
        print(user)
        print(visible)

        db.users.update_one(
            {'_id': user},
            {'$set': {'visible': request.form.get("visibility-switch")}}
        )

        db.observations.update_one(
            {'seen_by': username},
            {'$set': {'visible': visible}}
        )

        flash("Visibility updated")
        return redirect(url_for("my_nest"))


@app.route("/edit_user_anonymous", strict_slashes=False)
@app.route("/edit_user_anonymous/<user_id>", methods=["GET", "POST"])
def edit_user_anonymous(user_id):
    if request.method == "POST":
        user = ObjectId(user_id)
        username = session["user"]
        anonymous = request.form.get("anonymous-switch")
        print(user)
        print(anonymous)

        if anonymous == "on":
            anonymous = True
        elif anonymous == "None":
            anonymous = False

        db.users.update_one(
            {'_id': user},
            {'$set': {'anonymous': anonymous}}
        )

        db.observations.update_one(
            {'seen_by': username},
            {'$set': {'anonymous': anonymous}}
        )

        flash("Anonymity updated")
        return redirect(url_for("my_nest"))


@app.route("/sort_username/", methods=["GET", "POST"])
def sort_username():
    users = list(db.users.find().sort('username', pymongo.ASCENDING))
    return render_template("admin.html", users=users)


@app.route("/sort_experience/", methods=["GET", "POST"])
def sort_experience():
    users = list(db.users.find().sort('experience', pymongo.ASCENDING))
    return render_template("admin.html", users=users)


@app.route("/search/", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    observations = list(db.observations.find({"$text": {"$search": query}}))
    return render_template("observations.html", observations=observations)


@app.route("/sort_user/", methods=["GET", "POST"])
def sort_user():
    observations = list(db.observations.find().sort('seen_by', pymongo.ASCENDING))
    return render_template("observations.html", observations=observations)


@app.route("/sort_birds/", methods=["GET", "POST"])
def sort_birds():
    observations = list(db.observations.find().sort('bird_species', pymongo.ASCENDING))
    return render_template("observations.html", observations=observations)


@app.route("/sort_quantity/", methods=["GET", "POST"])
def sort_quantity():
    observations = list(db.observations.find().sort('quantity', pymongo.DESCENDING))
    return render_template("observations.html", observations=observations)


@app.route("/sort_location/", methods=["GET", "POST"])
def sort_location():
    observations = list(db.observations.find().sort('location', pymongo.ASCENDING))
    return render_template("observations.html", observations=observations)


@app.route("/sort_date/", methods=["GET", "POST"])
def sort_date():
    observations = list(db.observations.find().sort('date', pymongo.ASCENDING))
    return render_template("observations.html", observations=observations)


@app.route("/my_nest/", methods=["GET", "POST"])
def my_nest():
    observations = list(db.observations.find())
    username = session["user"]
    if username :
        user = db.users.find_one({'username': username})
    return render_template("my_nest.html", observations=observations, user=user)


@app.route("/life_list/")
def show_life_list():
    bird_count = [
        {'$match': {'seen_by': session['user']}},
        {'$group': {'_id': '$bird_species', 'totalQuantity': {'$sum': '$quantity'}}}
    ]
    tally = list(db.observations.aggregate(bird_count))

    return render_template("life_list.html", tally=tally)


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
            "experience": request.form.get("experience"),
            "visible": request.form.get("visibility-switch"),
            "anonymous": request.form.get("anonymous-switch")
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
                    flash("Welcome, {}! You have successfully logged in.".format(request.form.get("username")))
                    return redirect(url_for("my_nest"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout/")
def logout():
    session.pop("user")
    flash("You have been logged out")
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
            "quantity": int(request.form.get('quantity')),
            "edited": False,
            "anonymous": False,
            "visibile": True            
        }
        db.observations.insert_one(entry)
        flash("Observation added to your nest")
        return redirect(url_for("my_nest"))
            
    return render_template("add_observation.html")


@app.route("/edit_observations", strict_slashes=False)
@app.route("/edit_observation/<observation_id>", methods=["GET", "POST"])
def edit_observation(observation_id):
    original_entry = db.observations.find_one({"_id": ObjectId(observation_id)})
    original_user = original_entry.get("seen_by")
    if request.method == "POST":
        entry = {
            "bird_species": request.form.get("bird"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "seen_by": original_user,
            "certainty": request.form.get("certainty"),
            "notes": request.form.get("notes"),
            "quantity": request.form.get("quantity"),
            "edited": True,
            "edited_by": session["user"]
        }
        db.observations.replace_one({"_id": ObjectId(observation_id)}, entry)
        flash("Observation updated")
        return redirect(url_for("get_observations"))

    observation = db.observations.find_one({"_id": ObjectId(observation_id)})
    return render_template("edit_observation.html", observation=observation)


@app.route("/delete_observations", strict_slashes=False)
@app.route("/delete_observation/<observation_id>")
def delete_observation(observation_id):
    db.observations.delete_one({"_id": ObjectId(observation_id)})
    flash("Observation deleted")
    return redirect(url_for("get_observations"))


@app.route("/new_message/", methods=["GET", "POST"])
def new_message():
    if request.method == "POST":
        body = request.form.get("body")
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = {
            "sender": session["user"],
            "recipient": request.form.get("recipient"),
            "subject": request.form.get("subject"),
            "body": body,
            "time": current_timestamp
        }
        db.messages.insert_one(message)
        flash("Message sent successfully")
        return redirect(url_for("view_messages"))


@app.route("/delete_message", strict_slashes=False)
@app.route("/delete_message/<message_id>")
def delete_message(message_id):
    db.messages.delete_one({"_id": ObjectId(message_id)})
    flash("Message deleted")
    return redirect(url_for("get_users"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)


