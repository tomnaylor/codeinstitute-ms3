import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
# from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    import env


app = Flask(__name__)

# GET ENV VARS FROM OS
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")


@app.route("/cues")
def get_cues():
    """ HOME PAGE WILL BE LIST OF CUES INC A FILTER OPTION """
    cues = mongo.db.cues.find().sort("number", 1)
    return render_template("cues.html", cues=cues)


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    """ NEW USER SIGNUP """
    if request.method == "POST":

        # DOES USER ALREADY EXIST?
        exists = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if exists:
            flash("User already exists")
            return redirect(url_for("sign_up"))

        # ELSE BUILD NEW USER RECORD
        new_user = {
            "email": request.form.get("email").lower(),
            "name": request.form.get("name"),
            "password": generate_password_hash(request.form.get("password"))
        }

        mongo.db.users.insert_one(new_user)

        # ADD USER EMAIL TO SESSION
        session["user"] = request.form.get("email").lower()
        flash("Sign up successful!")
        return redirect(url_for("get_user"))

    return render_template("sign-up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ LOGIN EXISTING USER """
    if request.method == "POST":
        exists = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})
        if not exists:
            flash("Invalid user details")
            return redirect(url_for("login"))

        if check_password_hash(
                exists["password"], request.form.get("password")):
            session["user"] = exists["email"]
            session["admin"] = exists["admin"]
            flash(f"Welcome, { exists['name'] }")
            return redirect(url_for("get_user"))
        else:
            flash("Invalid email or password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """ LOGOUT """
    session.pop("user")
    session.pop("admin")
    flash("Logged out")
    return redirect(url_for("login"))


@app.route("/user")
def get_user():
    """ GET USER DETAILS """
    if not session["user"]:
        flash("No user signed in")
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"email": session["user"]})
    return render_template("user.html", user=user)


@app.route("/departments")
def get_departments():
    """ LIST OF ALL DEPARTMENTS (ADMIN ONLY) """
    # CHECK FOR ADMIN RIGHTS FIRST
    if session["admin"] != "yes":
        flash("Sorry you need to be an admin to edit departments")
        return redirect(url_for("get_cues"))

    # GET LIST OF ALL DEPARTMENTS
    departments = list(mongo.db.departments.find())
    return render_template("departments.html", departments=departments)


# NEW CUE
@app.route("/new-cue", methods=["GET", "POST"])
def new_cue():
    """ ADD A NEW CUE """
    # CHECK USER RIGHTS
    if not session['user']:
        flash("You must be logged in to add a cue")
        return redirect(url_for("login"))

    if request.method == "POST":

        # BUILD NEW CUE RECORD
        new_cue_record = {
            "number": request.form.get("number"),
            "dept": request.form.get("dept"),
            "desc": request.form.get("desc")
        }

        mongo.db.cues.insert_one(new_cue_record)

        flash("Cue added successful!")
        return redirect(url_for("get_cues"))

    departments = mongo.db.departments.find().sort("name", 1)
    return render_template("new-cue.html", departments=departments)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
