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


def is_user_logged_in():
    """ CHECK USER RIGHTS """
    if not session.get('user'):
        flash("You must be logged in to do that")
        return False
    else:
        return True


def is_user_admin():
    """ CHECK FOR ADMIN RIGHTS """
    if not session.get('admin'):
        flash("Sorry you need to be an admin to do that")
        return False
    else:
        return True


@app.route("/", methods=["GET"])
def get_cues():
    """ HOME PAGE WILL BE LIST OF CUES INC A FILTER OPTION """

    if request.method == 'GET' and request.args.get("dept"):
        query = request.args.get("dept")
        cues = mongo.db.cues.find({"dept": query}).sort("time", 1)
    elif request.method == 'GET' and request.args.get("search"):
        query = request.args.get("search")
        cues = mongo.db.cues.find({'desc': {'$regex': query, '$options': 'i'}})
    else:
        cues = mongo.db.cues.find().sort("time", 1)

    departments = list(mongo.db.departments.find())

    return render_template("cues.html", cues=cues, departments=departments)


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
            flash("Invalid email or password")
            return redirect(url_for("login"))

        if check_password_hash(
                exists["password"], request.form.get("password")):
            session["user"] = exists["email"]

            if exists.get('admin'):
                session["admin"] = exists["admin"]

            flash(f"Hello { exists['name'] }")
            return redirect(url_for("get_cues"))
        else:
            flash("Invalid email or password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """ LOGOUT """
    session.pop("user")

    if session.get('admin'):
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

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    # GET LIST OF ALL DEPARTMENTS
    departments = list(mongo.db.departments.find())
    return render_template("departments.html", departments=departments)


@app.route("/new-department", methods=["GET", "POST"])
def new_department():
    """ ADD A NEW DEPARTMENT """

    if not is_user_admin():
        return redirect(url_for("get_cues"))

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

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    if request.method == "POST":

        new_value = {"$set": {"name": request.form.get("name")}}
        mongo.db.departments.update_one({"_id": ObjectId(dept_id)}, new_value)
        flash("Department updated")
        return redirect(url_for("get_departments"))

    department = mongo.db.departments.find_one({"_id": ObjectId(dept_id)})
    return render_template("edit-department.html", department=department)


@app.route("/delete_department/<dept_id>/<dept_name>")
def delete_department(dept_id, dept_name):
    """ DELETE A DEPARTMENT """

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    inuse = mongo.db.cues.find_one({"dept": dept_name})
    if inuse:
        flash("Department is used in cues")
        return redirect(url_for("get_departments"))

    mongo.db.departments.delete_one({"_id": ObjectId(dept_id)})
    flash("Department deleted")
    return redirect(url_for("get_departments"))


# ----- SCENES -----


@app.route("/scenes")
def get_scenes():
    """ LIST OF ALL SCENES (ADMIN ONLY) """

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    # GET LIST OF ALL SCENES
    scenes = list(mongo.db.scenes.find())
    return render_template("scenes.html", scenes=scenes)


@app.route("/new-scene", methods=["GET", "POST"])
def new_scene():
    """ ADD A NEW SCENE """

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    if request.method == "POST":

        # BUILD NEW RECORD
        new_record = {
            "name": request.form.get("name"),
            "desc": request.form.get("desc")
        }

        mongo.db.scenes.insert_one(new_record)

        flash("New scene added successful!")
        return redirect(url_for("get_scenes"))

    return render_template("new-scene.html")


@app.route("/edit-scene/<scene_id>", methods=["GET", "POST"])
def edit_scene(scene_id):
    """ EDIT A SCENE """

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    if request.method == "POST":
        new_value = {"$set": {
            "name": request.form.get("name"),
            "desc": request.form.get("desc")}}
        mongo.db.scenes.update_one({"_id": ObjectId(scene_id)}, new_value)
        flash("Scene updated")
        return redirect(url_for("get_scenes"))

    scene = mongo.db.scenes.find_one({"_id": ObjectId(scene_id)})
    return render_template("edit-scene.html", scene=scene)


@app.route("/delete-scene/<scene_id>")
def delete_scene(scene_id):
    """ DELETE A SCENE """

    if not is_user_admin():
        return redirect(url_for("get_cues"))

    mongo.db.scenes.delete_one({"_id": ObjectId(scene_id)})
    flash("Scene deleted")
    return redirect(url_for("get_scenes"))


# ----- CUES ------

@app.route("/new-cue", methods=["GET", "POST"])
def new_cue():
    """ ADD A NEW CUE """

    if not is_user_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":

        # BUILD NEW CUE RECORD
        new_cue_record = {
            "number": round(float(request.form.get("number")), 1),
            "time": int(request.form.get("time")),
            "dept": request.form.get("dept"),
            "scene": request.form.get("scene"),
            "desc": request.form.get("desc")
        }

        mongo.db.cues.insert_one(new_cue_record)

        flash("Cue added successful!")
        return redirect(url_for("get_cues"))

    departments = mongo.db.departments.find().sort("name", 1)
    scenes = mongo.db.scenes.find().sort("name", 1)
    return render_template(
        "new-cue.html", departments=departments, scenes=scenes)


@app.route("/edit-cue/<cue_id>", methods=["GET", "POST"])
def edit_cue(cue_id):
    """ EDIT A CUE """

    if not is_user_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":
        new_value = {"$set": {
            "number": round(float(request.form.get("number")), 1),
            "time": int(request.form.get("time")),
            "dept": request.form.get("dept"),
            "scene": request.form.get("scene"),
            "desc": request.form.get("desc")
            }}

        mongo.db.cues.update_one({"_id": ObjectId(cue_id)}, new_value)
        flash("Cue updated")
        return redirect(url_for("get_cues"))

    departments = mongo.db.departments.find().sort("name", 1)
    scenes = mongo.db.scenes.find().sort("name", 1)
    cue = mongo.db.cues.find_one({"_id": ObjectId(cue_id)})
    return render_template(
        "edit-cue.html", cue=cue, departments=departments, scenes=scenes)


@app.route("/delete-cue/<cue_id>")
def delete_cue(cue_id):
    """ DELETE A CUE """

    if not is_user_logged_in():
        return redirect(url_for("login"))

    mongo.db.cues.delete_one({"_id": ObjectId(cue_id)})
    flash("Cue deleted")
    return redirect(url_for("get_cues"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
