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


@app.route("/")
def get_cues():
    """ HOME PAGE WILL BE LIST OF CUES INC A FILTER OPTION """
    cues = mongo.db.cues.find().sort("number", 1)
    return render_template("cues.html", cues=cues)


# ----- USERS -----


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


# ----- DEPARTMENTS -----


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

def is_user_logged_in():
    """ CHECK USER RIGHTS """
    if not session.get('user'):
        flash("You must be logged in to do that!")
        return False
    else:
        return True


@app.route("/new-department", methods=["GET", "POST"])
def new_department():
    """ ADD A NEW DEPARTMENT """
    
    if not is_user_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":

        # BUILD NEW DEPARTMENT RECORD
        new_record = {
            "name": request.form.get("name")
        }

        mongo.db.departments.insert_one(new_record)

        flash("New department added successful!")
        return redirect(url_for("get_departments"))

    return render_template("new-department.html")


@app.route("/edit_department/<dept_id>", methods=["GET", "POST"])
def edit_department(dept_id):
    """ EDIT A DEPARTMENT """

    if not is_user_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":

        new_value = { "$set": { "name": request.form.get("name") } }
        mongo.db.departments.update_one({"_id": ObjectId(dept_id)}, new_value)
        flash("Department updated")
        return redirect(url_for("get_departments"))

    department = mongo.db.departments.find_one({"_id": ObjectId(dept_id)})
    return render_template("edit-department.html", department=department)


@app.route("/delete_department/<dept_id>/<dept_name>")
def delete_department(dept_id, dept_name):
    """ DELETE A DEPARTMENT """
    
    if not is_user_logged_in():
        return redirect(url_for("login"))
    
    inuse = mongo.db.cues.find_one({"dept": dept_name})
    if inuse:
        flash("Department is used in cues")
        return redirect(url_for("get_departments"))

    mongo.db.departments.delete_one({"_id": ObjectId(dept_id)})
    flash("Department deleted")
    return redirect(url_for("get_departments"))


# ----- ROLES -----


@app.route("/roles")
def get_roles():
    """ LIST OF ALL ROLES (ADMIN ONLY) """
    # CHECK FOR ADMIN RIGHTS FIRST
    if session["admin"] != "yes":
        flash("Sorry you need to do that")
        return redirect(url_for("get_cues"))

    # GET LIST OF ALL ROLES
    roles = list(mongo.db.roles.find())
    return render_template("roles.html", roles=roles)


@app.route("/new-role", methods=["GET", "POST"])
def new_role():
    """ ADD A NEW ROLE """
    if not is_user_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":

        # BUILD NEW ROLE RECORD
        new_record = {
            "name": request.form.get("name"),
            "dept": request.form.get("dept")
        }

        mongo.db.roles.insert_one(new_record)

        flash("New role added successful!")
        return redirect(url_for("get_roles"))

    departments = list(mongo.db.departments.find())
    return render_template("new-role.html", departments=departments)


@app.route("/edit-role/<role_id>", methods=["GET", "POST"])
def edit_role(role_id):
    """ EDIT A ROLE """

    if not is_user_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":
        new_value = {"$set": {
            "name": request.form.get("name"),
            "dept": request.form.get("dept")}}
        mongo.db.roles.update_one({"_id": ObjectId(role_id)}, new_value)
        flash("Role updated")
        return redirect(url_for("get_roles"))

    role = mongo.db.roles.find_one({"_id": ObjectId(role_id)})
    departments = list(mongo.db.departments.find())
    return render_template("edit-role.html", role=role, departments=departments)


@app.route("/delete-role/<role_id>/<role_name>")
def delete_role(role_id, role_name):
    """ DELETE A ROLE """

    if not is_user_logged_in():
        return redirect(url_for("login"))
    
    inuse = mongo.db.roles.find_one({"role": role_name})
    if inuse:
        flash("Role is used in cues")
        return redirect(url_for("get_role"))

    mongo.db.roles.delete_one({"_id": ObjectId(role_id)})
    flash("Role deleted")
    return redirect(url_for("get_roles"))


# ----- CUES ------

@app.route("/new-cue", methods=["GET", "POST"])
def new_cue():
    """ ADD A NEW CUE """
    # CHECK USER RIGHTS
    if not session['user']:
        flash("You must be logged in to add a cue")
        return redirect(url_for("login"))

    if request.method == "POST":

        # FIND DEPT FROM ROLE
        role = mongo.db.roles.find_one({"name": request.form.get("role")})

        # BUILD NEW CUE RECORD
        new_cue_record = {
            "number": round(float(request.form.get("number")), 1),
            "dept": role["dept"],
            "role": request.form.get("role"),
            "scene": request.form.get("scene"),
            "desc": request.form.get("desc")
        }

        mongo.db.cues.insert_one(new_cue_record)

        flash("Cue added successful!")
        return redirect(url_for("get_cues"))

    departments = mongo.db.departments.find().sort("name", 1)
    roles = mongo.db.roles.find().sort("name", 1)
    return render_template("new-cue.html", departments=departments, roles=roles)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
