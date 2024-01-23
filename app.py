# Imports
import os
import io
from flask import (
    Flask, Blueprint, flash, render_template,
    redirect, request, session, url_for, send_file)
from flask_pymongo import PyMongo
from gridfs import GridFS
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


# Set up app.
app = Flask(__name__, template_folder='templates')


# Set up MongoDB.
import pymongo
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")
client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
db = client["birdcount"]
fs = GridFS(db)


# Add user data to all templates.
@app.context_processor
def inject_user():
    """ Add session user infromation to all templates before they are rendered"""
    user = None
    if 'user' in session:
        username = session['user']
        user = db.users.find_one({'username': username})
    return dict(user=user)

# Render template for welcome page.
@app.route("/")
def welcome():
    """ Renders template for the 'Welcome' page."""
    return render_template("welcome.html")


# Render template for about page.
@app.route("/about/")
def about():
    """ Renders the 'About' page template"""
    return render_template("about.html")


# Render template for community observations page.
@app.route("/get_observations/")
def get_observations():
    """ 
    Renders the 'Observations' page template. 
    
    Returns:
        users(list): all data from users in the birdcount database.
        observations(list): all data from observations in the birdcount database.
    """
    # Get users data from the database.
    users = list(db.users.find())

    # Get observations data from database and sort with most recent first.
    observations = list(db.observations.find().sort("date", -1))

    return render_template("observations.html", observations=observations, users=users)


# Render template for Admin's nest page.
@app.route("/get_users/")
def get_users():
    """ 
    Renders the 'Admin' page template only for users who are the admin. Other users are redirected.
    
    Redirect: 
        non-users: login()
        non-admin users: my_nest()

    Returns:
        users(list): all data from users in the birdcount database.
        messages(list): all data from messages in the birdcount database.
    """
    # Get user data from the database.
    users = list(db.users.find())
    # Get message data from the database.
    messages = list(db.messages.find())

    # Redirect non-users to 'login'.
    if 'user' not in session:
        flash("Log in or register to get started")
        return redirect(url_for('login'))
    #  Redirect non-admin users to 'my nest'.
    elif session["user"] != 'admin':
        flash("You are not authorised to view the admin page")
        return redirect(url_for('my_nest'))

    return render_template("admin.html", users=users, messages=messages)


# Render template for my nest page.
@app.route("/my_nest/", methods=["GET", "POST"])
def my_nest():
    """
    Renders 'My Nest' template only for users who are logged in not as 'Admin'; other users are redirected. 
    Bird stats are calculated from the session user's observations. Message data from the birdcount database
    are listed.

    Redirect:
        non-users: login()
        admin: get_users()

    Returns:
        observations(list): all observation data from the birdcount database, sorted with most recent first.
        user(list): all user data for only the session user.
        total_observations(list): the total number of birds of any species observed by the current user.
        species_count: the number of different species in user's observations.
        average_certainty(int): average of the 'certainty' field of all observations from current user.
        tally(list): 'bird_species' and corresponding 'quantity' observed by the logged in user, grouped by 'bird_species'.
        messages(list): all message data from the birdcount databse.

    """
    # Redirect non users to the login page.
    if 'user' not in session:
        flash("Log in or register to get started")
        return redirect(url_for('login'))
    # Redirect user if 'admin' to the admin page.
    elif session["user"] == 'admin':
        flash("Admin can't access personal nests")
        return redirect(url_for('get_users'))
    
    # Get user data for the current logged in user.
    username = session["user"]
    if username :
        user = db.users.find_one({'username': username})

    # Get all observation data and sort so most recent is first.
    observations = list(db.observations.find().sort("date", -1))   

    # Get all observations created by the logged in user to calculate bird stats from.
    users_observations = list(db.observations.find({"seen_by": username}))
    # Create empty list variables for new list data.
    quantities = []
    species_seen = []
    certainty_list = []
    # Create lists of observation data from which bird stats can be calculated.
    for users_observation in users_observations:
        quantities.append(users_observation["quantity"])
        species_seen.append(users_observation["bird_species"])
        certainty_list.append(int(users_observation["certainty"]))

    # Calculate the total number of birds of any species.
    total_observations = 0
    for count in quantities:
        total_observations += int(count)

    # Create a list of the species observed without repeats.
    unique_species = []
    for species in species_seen :
        if species not in unique_species:
            unique_species.append(species)

    # Calculate the number of different species observed.
    species_count = 0
    species_count = len(unique_species)

    # Calculate the average certainty of the user's observations.
    total_certainty = sum(certainty_list)
    try:
        average_certainty = int(total_certainty / len(certainty_list))
    # Can't divide 0 error.
    except ZeroDivisionError:
        average_certainty = 0
        print("cannot divide zero")

    # Creates a list, 'tally', of bird species and their quantities, grouped by species.
    bird_count = [
    {'$match': {'seen_by': session['user']}},
    {'$group': {'_id': '$bird_species', 'totalQuantity': {'$sum': '$quantity'}}}
    ]
    tally = list(db.observations.aggregate(bird_count))

    # Creates a list of all messages from the database.
    messages = list(db.messages.find())

    return render_template(
        "my_nest.html", 
        observations=observations, 
        user=user, 
        total_observations=total_observations, 
        species_count=species_count, 
        average_certainty=average_certainty,
        tally=tally,
        messages=messages
    )


# Render template for registration page.
@app.route("/register/", methods=["GET", "POST"])
def register():
    """
    Renders template for 'register'. 
    
    Value of 'username' in submitted form is checked against 'username' field in each document in the 
    users collection in the birdcount database. Dulicated usernames are prevented. 

    Field validation is added for 'experience', so '0' is not a valid value.

    Variable 'register' value is added to the 'users' collection in the birdcount database.

    The registered user is logged in and added to the 'session' cookie.

    Redirect:
        Existing users: login()
        Invalid experience value: register()
        Successful registration: my_nest()
    """

    if request.method == "POST":
        # check if username already exists in db.
        existing_user = db.users.find_one(
            {"username": request.form.get("username").lower()})
        
        # If the username already exists redirect user to login.
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("login"))
        
        # Validate 'experience' field so '0' isn't an accepted value.
        experience = request.form.get("experience")
        # Match experience levels to different avatars
        if experience == '1':
            avatar_url = '../static/assets/images/eggs.png' 
        elif experience == '2':
            avatar_url = 'https://images.pexels.com/photos/1275680/pexels-photo-1275680.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '3':
            avatar_url = 'https://images.pexels.com/photos/11064121/pexels-photo-11064121.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '4':
            avatar_url = 'https://images.pexels.com/photos/10922696/pexels-photo-10922696.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '5':
            avatar_url = 'https://images.pexels.com/photos/12290958/pexels-photo-12290958.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '6':
            avatar_url = 'https://images.pexels.com/photos/2474014/pexels-photo-2474014.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 

        # Redirect if value is invalid.
        if experience == '0':
            flash("You need to choose a value for 'experience'. This can be changed in your nest at any time.")
            return redirect(url_for("register"))
        # Register user if experience is valid.
        else:
            register = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(request.form.get("password")),
                "email": request.form.get("email"),
                "experience": request.form.get("experience"),
                "visible": bool("True"),
                "anonymous": bool(""),
                "avatar": avatar_url
            }
            db.users.insert_one(register)

        # Put the new user into 'session' cookie and redirect to 'My nest'.
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful! Welcome, {}!".format(request.form.get("username")))
        return redirect(url_for("my_nest"))
    
    return render_template("register.html")


# Render template for login page.
@app.route("/login/", methods=["GET", "POST"])
def login():
    """
    Renders the template for 'Login' page. 

    Takes submitted form data and checks validity of username and password against 'users' collection in database.
    Logs in users if username and password fields match that of a single document in the databse.

    Redirects:
        Logged in admin: get_users().
        Logged in existing users that are not admin: my_nest().
        Invalid input fields: login().
    """
    if request.method == "POST":
        # check if username exists in db.
        existing_user = db.users.find_one(
            {"username": request.form.get("username").lower()})

        # Log in user.
        if existing_user:
            # Check password matches hashed password, then log user in.
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}! You have successfully logged in.".format(request.form.get("username")))
                    # If admin logs in redirect them to the 'Admin' page.
                    if session["user"] == 'admin':
                        return redirect(url_for("get_users"))
                    # If an other existing user logs in redirect them to 'My Nest'.
                    else:
                        return redirect(url_for("my_nest"))                    
            else:
                # Invalid password match.
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # Username doesn't exist.
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# Render template for add observations page 
@app.route("/add_observation/", methods=["GET", "POST"])
def add_observation():
    """
    Renders the template for 'add_observation.html', only for users that are logged in and not the admin. Other users are redirected.

    Gets data from observation form at adds it to the birdcount database as a new observation document.

    Redirect:
        admin: get_users().
        users that are not logged in: login().
        Successful observation addition: my_nest().
    """
    if request.method == "POST":
        # Redirect users that are not logged in to 'login' page.
        if 'user' not in session:
            flash("Log in or register to get started")
            return redirect(url_for('login'))
        # Redirect admin in 'Admin' page.
        elif session["user"] == 'admin':
            flash("Admin can't add observations")
            return redirect(url_for('get_users'))

        # Set up user ID data in variables.
        user = session["user"]
        user_info = db.users.find_one({"username": user})
        user_id = user_info["_id"]

        # Set up privacy data in variables.
        visible = user_info["visible"]
        anonymous = user_info["anonymous"]

        # Check if the file is present in the request
        if 'image-file' in request.files:
            image_file = request.files['image-file']
            if image_file.filename != '':
                # A file has been uploaded; proceed to handle it
                image_id = fs.put(image_file)
                # Further logic to handle the image ID, possibly storing it in the database
            else:
                # No file uploaded; handle accordingly
                image_id = ObjectId('65a522a638bb15858a80cc53')
                print("No file uploaded")
        else:
            # No file field in the request; handle accordingly
            print("No file field in the request")
                
        # Create new observation document in 'observations' collection.
        entry = {
            "bird_species": request.form.get("bird"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "seen_by": session["user"],
            "seen_by_id": user_id,
            "certainty": request.form.get("certainty"),
            "notes": request.form.get("notes"),
            "quantity": int(request.form.get('quantity')),
            "edited": False,
            "anonymous": anonymous,
            "visible": visible            
        }
        if image_id is not None:
            entry["image"] = image_id
        db.observations.insert_one(entry)
        flash("Observation added to your nest")
        return redirect(url_for("my_nest")) 
    return render_template("add_observation.html")


# Render template for edit observations page
@app.route("/edit_observations", strict_slashes=False)
@app.route("/edit_observation/<observation_id>", methods=["GET", "POST"])
def edit_observation(observation_id):
    """
    Renders template for 'edit_observation.html), only for user who are 'admin' or match the 
    observation 'seen_by' field. Other users are redirected.

    Gets data from the 'edit_observation' form to replace the data in the observation document in teh birdcount database with the 
    matching observation_id as is passed into the function.

    Parameters:
        observation_id (str): a unique string.

    Redirects:
        User that is not logged in: login().
        Logged in user that is neither admin or creator of the observation: get_observations().
        Successful update: get_observations().

    Returns:
        observation (dict): a dictionary containing data of the observation matching the id passed into function.
        original_user (str): a string containing the username of the original creator of the observation.
    """
    # Find the observation with '_id' matching the 'observation_id'
    observation = db.observations.find_one({"_id": ObjectId(observation_id)})

    # Get data for the user who originally created the selected observation.
    original_user = observation.get("seen_by")
    user_info = db.users.find_one({"username": original_user})
    user_id = user_info["_id"]
    visible = user_info["visible"]
    anonymous = user_info["anonymous"]
    original_image_id = observation.get("image")
    
    # Redirect user to login if they are not already.
    if 'user' not in session:
        flash("You are not authorised to edit other user's observation. Log in or register to get started.")
        return redirect(url_for('login'))
    # Redirect user to community observations page if they are logged in but neither the admin or creator of the observation.
    elif session["user"] != original_user and session["user"] != 'admin':
        flash("You are not authorised to edit other user's observation.")
        return redirect(url_for('get_observations'))
    
    # Check if the file is present in the request
    if 'image-file' in request.files:
        image_file = request.files['image-file']
        if image_file.filename != '':
            # A file has been uploaded; proceed to handle it
            image_id = fs.put(image_file)
            # Further logic to handle the image ID, possibly storing it in the database
        else:
            # No file uploaded; handle accordingly
            image_id = ObjectId(original_image_id)
            print("No file uploaded")
    else:
        # No file field in the request; handle accordingly
        print("No file field in the request")

    if request.method == "POST":
        # Get information from form fields to create new data for observation.
        entry = {
            "bird_species": request.form.get("bird"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "seen_by": original_user,
            "seen_by_id": user_id,
            "certainty": request.form.get("certainty"),
            "notes": request.form.get("notes"),
            "quantity": int(request.form.get("quantity")),
            "edited": True,
            "edited_by": session["user"],
            "anonymous": anonymous,
            "visible": visible            
        }
        if image_id is not None:
            entry["image"] = image_id

        # Replace document with matching id with 'entry'.
        db.observations.replace_one({"_id": ObjectId(observation_id)}, entry)
        flash("Observation updated")
        return redirect(url_for("get_observations"))

    return render_template("edit_observation.html", observation=observation, original_user=original_user)


# ------------------ function routes -----------------
@app.route("/get_image", strict_slashes=False)
@app.route('/get_image/<observation_id>')
def get_image(observation_id):
    document = db.observations.find_one({"_id": ObjectId(observation_id)})
    image_id = document.get("image")
    image_file = fs.get(image_id)
    return send_file(image_file, mimetype='image/jpeg')

# Logout the session user
@app.route("/logout/")
def logout():
    """ The current user is removed from the 'session' cookie."""
    session.pop("user")
    flash("You have been logged out")
    return redirect(url_for("login"))


# Delete the selected observation
@app.route("/delete_observations", strict_slashes=False)
@app.route("/delete_observation/<observation_id>")
def delete_observation(observation_id):
    """
    Observations from the birdcount database are deleted if their '_id' matches the
    observation_id passed into the function.
    
    Parameters:
        observation_id (str): a unique string.
    """
    observation = db.observations.find_one({"_id": ObjectId(observation_id)})
    image_id = observation["image"]
    if ObjectId(image_id) != ObjectId("65a522a638bb15858a80cc53"):
        fs.delete(ObjectId(image_id))
        flash("Image file deleted")
    db.observations.delete_one({"_id": ObjectId(observation_id)})
    flash("Observation deleted")
    return redirect(request.referrer)


# Write and send a new message 
@app.route("/new_message/", methods=["GET", "POST"])
def new_message():
    """Gets form values to add to the messages collection in the birdcount database as a new document."""
    if request.method == "POST":
        # Add new message data to the messages collection in DB.
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
        return redirect(request.referrer)


# delete the selected message 
@app.route("/delete_message", strict_slashes=False)
@app.route("/delete_message/<message_id>")
def delete_message(message_id):
    """
    Messages from the birdcount database are deleted if their '_id' matches the
    message_id passed into the function.
    
    Parameters:
        message_id (str): a unique string.
    """
    db.messages.delete_one({"_id": ObjectId(message_id)})
    flash("Message deleted")
    return redirect(request.referrer)


# --------- Routes for editing and deleting user settings. ------------ 
# Route for deleting user.
@app.route("/delete_user", strict_slashes=False)
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    """
    Users from the birdcount database are deleted if their '_id' matches the
    user_id passed into the function.

    Updates observations made by user with passed in user_id change 'seen_by' field to 'admin'.

    Removes user from 'session' cookie.
    
    Parameters:
        user_id (str): a unique string.
    """
    # Deleted user with Id that matches the id passed into function.
    user = db.users.find_one({"_id": ObjectId(user_id)})
    username = user['username']
    db.users.delete_one({"_id": ObjectId(user_id)})

    # Update observations with matching username to remove ownership to user.
    db.observations.update_many(
        {'seen_by': username},
        {
            '$set': {
                'anonymous': bool(True),
                'seen_by': 'admin' 
            }
        }
    )
    flash("User successfully deleted")
    # Redirect admin to Admin page.
    if session["user"] == 'admin':
        return redirect(url_for("get_users"))
    # Logout if deletion is successful and user is not the admin.
    else:
        return redirect(url_for("logout"))


# Route for editing session user's email.
@app.route("/edit_user_email", strict_slashes=False)
@app.route("/edit_user_email/<user_id>", methods=["GET", "POST"])
def edit_user_email(user_id):
    """
    User 'email' field is updated in the document that has an '_id' that matches the
    user_id passed into the function.
    
    Parameters:
        user_id (str): a unique string.
    """
    if request.method == "POST":
        # Set user variable to match format in database.
        user = ObjectId(user_id)
        # Get the email value from the form.
        new_email = request.form.get("email-edit")
        # Update the relevant document with the new email.
        db.users.update_one(
            {'_id': user},
            {'$set': {'email': new_email}}
        )
        flash("Email updated")
        return redirect(url_for("my_nest"))


# Route for editing session user's experience level
@app.route("/edit_user_experience", strict_slashes=False)
@app.route("/edit_user_experience/<user_id>", methods=["GET", "POST"])
def edit_user_experience(user_id):
    """
    User 'experience' field is updated in the document that has an '_id' that matches the
    user_id passed into the function.

    Validates the 'experience' field in the form to ensure the value is not '0'. User will have to resubmit the form.
    
    Parameters:
        user_id (str): a unique string.
    """
    if request.method == "POST":
        # Get the 'experience' field value from the form.
        user = ObjectId(user_id)
        experience = request.form.get("experience-edit")
        
        # Match experience levels to different avatars
        if experience == '1':
            avatar_url = 'https://images.pexels.com/photos/5501020/pexels-photo-5501020.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '2':
            avatar_url = 'https://images.pexels.com/photos/1275680/pexels-photo-1275680.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '3':
            avatar_url = 'https://images.pexels.com/photos/11064121/pexels-photo-11064121.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '4':
            avatar_url = 'https://images.pexels.com/photos/10922696/pexels-photo-10922696.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '5':
            avatar_url = 'https://images.pexels.com/photos/12290958/pexels-photo-12290958.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        elif experience == '6':
            avatar_url = 'https://images.pexels.com/photos/2474014/pexels-photo-2474014.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' 
        # Validate 'experience' field so that value cannot = 0.
        if experience == '0':
            flash("No changes made, fill in the experience field to make changes")
        # Update the 'experience' field in the database.
        else:
            db.users.update_one(
                {'_id': user},
                {'$set': {
                    'experience': experience,
                    'avatar': avatar_url
                    }
                }
            )
            flash("Experience updated")
        return redirect(url_for("my_nest"))


# Route for editing session user's visibility
@app.route("/edit_user_visibility", strict_slashes=False)
@app.route("/edit_user_visibility/<user_id>", methods=["GET", "POST"])
def edit_user_visibility(user_id):
    """
    User 'visible' field is updated in the document that has an '_id' that matches the
    user_id passed into the function.

    All observations whose 'seen_by' field matches the username of the user_id will be 
    updated with the new visibility data.

    Parameters:
        user_id (str): a unique string.
    """
    if request.method == "POST":
        # Set user data.
        user = user_id
        username = session["user"]

        # Get visibility settings from form.
        visible = request.form.get("visibility-switch")
        # Edit values of 'visible' depending on form data.
        if visible == "on":
            visible = True
        else:
            visible = False
        # Update the user with the new visbility setting.
        db.users.update_one(
            {'_id': ObjectId(user)},
            {'$set': {'visible': visible}}
        )
        # Update all observations by this user with new visibility setting.
        db.observations.update_many(
            {'seen_by': username},
            {'$set': {'visible': visible}}
        )
        flash("Visibility updated")
        return redirect(url_for("my_nest"))


# Route for editing session user's anominity
@app.route("/edit_user_anonymous", strict_slashes=False)
@app.route("/edit_user_anonymous/<user_id>", methods=["GET", "POST"])
def edit_user_anonymous(user_id):
    """
    User 'anonymous' field is updated in the document that has an '_id' that matches the
    user_id passed into the function.

    All observations whose 'seen_by' field matches the username of the user_id will be 
    updated with the new anonymity data.

    Parameters:
        user_id (str): a unique string.
    """
    if request.method == "POST":
        # Set user data.
        user = user_id
        username = session["user"]

        # Get anonymity settings from form.
        anonymous = request.form.get("anonymous-switch")
        # Edit values of 'anonymous' depending on form data.
        if anonymous == "on":
            anonymous = True
        else:
            anonymous = False
        # Update the user with the new anonymity setting.
        db.users.update_one(
            {'_id': ObjectId(user)},
            {'$set': {'anonymous': anonymous}}
        )
        # Update all observations by this user with new anonymity setting.
        db.observations.update_many(
            {'seen_by': str(username)},
            {'$set': {'anonymous': anonymous}}
        )
        flash("Anonymity updated")
        return redirect(url_for("my_nest"))


# --------- Routes for Admin to sort fields in users table. ------------ 
@app.route("/sort_ascending_admin", strict_slashes=False)
@app.route("/sort_ascending_admin/<observation_field>", methods=["GET", "POST"])
def sort_ascending_admin(observation_field):
    """
    Renders template for 'admin.html' only if the user is the admin. Other users are redirected.

    Finds all user data from users collection in birdcount database and sorts it in ascending 
    order by the observation_field passed into the function.

    Parameters:
        observation_field (str): a string containing a field name.
    """
    # Redirect non-users to 'login'.
    if 'user' not in session:
        flash("Log in or register to get started")
        return redirect(url_for('login'))
    #  Redirect non-admin users to 'my nest'.
    elif session["user"] != 'admin':
        flash("You are not authorised to view the admin page")
        return redirect(url_for('my_nest'))

    # Finds all user data and sorts it in ascening order by field.
    users = list(db.users.find().sort(observation_field, pymongo.ASCENDING))
    return render_template("admin.html", users=users)


@app.route("/sort_descending_admin", strict_slashes=False)
@app.route("/sort_descending_admin/<observation_field>", methods=["GET", "POST"])
def sort_descending_admin(observation_field):
    """
    Renders template for 'admin.html' only if the user is the admin. Other users are redirected.

    Finds all user data from users collection in birdcount database and sorts it in descending 
    order by the observation_field passed into the function.

    Parameters:
        observation_field (str): a string containing a field name.
    """
    # Redirect non-users to 'login'.
    if 'user' not in session:
        flash("Log in or register to get started")
        return redirect(url_for('login'))
    #  Redirect non-admin users to 'my nest'.
    elif session["user"] != 'admin':
        flash("You are not authorised to view the admin page")
        return redirect(url_for('my_nest'))

    # Finds all user data and sorts it in descening order by field.
    users = list(db.users.find().sort(observation_field, pymongo.DESCENDING))
    return render_template("admin.html", users=users)


# ----------- Search and sort functionality in observation table -----------
# Search bird species and location fields.
@app.route("/search/", methods=["GET", "POST"])
def search():
    """ Get search query from form and find documents with text matching the query"""
    # Get query value from form.
    query = request.form.get("query")
    # Find observations with text that matches the query.
    observations = list(db.observations.find({"$text": {"$search": query}}))
    return render_template("observations.html", observations=observations)


@app.route("/sort_ascending", strict_slashes=False)
@app.route("/sort_ascending/<observation_field>", methods=["GET", "POST"])
def sort_ascending(observation_field):
    """
    Renders template for 'observations.html'.

    Finds all user data from observations collection in birdcount database and sorts it in ascending 
    order by the observation_field passed into the function.

    Parameters:
        observation_field (str): a string containing a field name.
    """
    observations = list(db.observations.find().sort(observation_field, pymongo.ASCENDING))
    return render_template("observations.html", observations=observations)


@app.route("/sort_descending", strict_slashes=False)
@app.route("/sort_descending/<observation_field>", methods=["GET", "POST"])
def sort_descending(observation_field):
    """
    Renders template for 'observations.html'.

    Finds all user data from observations collection in birdcount database and sorts it in descending 
    order by the observation_field passed into the function.

    Parameters:
        observation_field (str): a string containing a field name.
    """
    observations = list(db.observations.find().sort(observation_field, pymongo.DESCENDING))
    return render_template("observations.html", observations=observations)



# error 404 handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"),404

# error 500 handler
@app.errorhandler(500)
def internal_server_error(error):
    return render_template('404.html'), 500

# Run the app
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)


