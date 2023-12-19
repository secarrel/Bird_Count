import os
from flask import (
    Flask, Blueprint, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env


app = Flask(__name__, template_folder='templates')

import pymongo


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
db = client["birdcount"]
# observations = db["observations"]
# cursor = db.observations.find() 
# Print out the results 
# print("Observations:")
# for observation in cursor:     
#     print(observation)


@app.route("/")
@app.route("/get_observations/")
def get_observations():
    observations = db.observations.find()
    return render_template("obseravtions.html", observations=observations)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
