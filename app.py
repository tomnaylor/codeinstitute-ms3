import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

# GET ENV VARS FROM OS
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# HOME PAGE WILL BE LIST OF CUES INC A FILTER OPTION
@app.route("/")
def get_cues():
    return "hello world"


# NEW USER SIGN UP
@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":

        # DOES USER ALREADY EXIST?
        exists = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if exists:
            flash("User already exists")
            return redirect(url_for("sign_up"))

        # BUILD NEW USER RECORD
        new_user = {
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }

        mongo.db.users.insert_one(new_user)

        # ADD USER EMAIL TO SESSION 
        session["user"] = request.form.get("email").lower()
        flash("Sign up successful!")
        return redirect(url_for("user", user=session["user"]))

    return render_template("sign-up.html")


# LIST OF ALL DEPARTMENTS (ADMIN ONLY)
@app.route("/departments")
def get_departments():
    
    # CHECK FOR ADMIN RIGHTS FIRST
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    # GET LIST OF ALL DEPARTMENTS
    departments = list(mongo.db.departments.find())
    return render_template("departments.html", departments=departments)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
