gitpod from github template
added app.py file
touch env.py then added to .gitignore then added env values 
added flash to requirements installed from pip3
added new project in monogo db called "cue_manager"
built a shared (free) cluster called "cue-manager"
created user "cuemanager" with password "cuemanager" - added access from anywhere
created a DB "cue_manager" and collections "departments", "cues", "users"
added default route to app.py to test 
added procfile ready for heroku
created new heroku app "cue-manager-tn-ci-ms3"
added env variabled to match local file
auto deployed app on heroku via github commit updates
added flask-pymongo + dnspython + updated requirements
Debugged connection to mongoDB - URI was wrong and needed to restart python
added base.html and flash container
added mataralize template


Problems
problems connection to mongoDB - https://flask-pymongo.readthedocs.io/en/latest/#flask_pymongo.PyMongo.db as reference
Heroku didn't work - env var wasn't updated in line with env.py
User profile wouldn't load - had an error in base.html that called url for user not get_user
cues loop would not work on template - fixed with {% if cues[0]|length > 0 %} (cues[0] no cues)
admin session not working - forgot need to logout and back in after each time record was modified.
Cues did not sort in order. 1 and 11 would be before 2. Think it's bacause it's in DB as a string and not number
password regex https://stackoverflow.com/questions/27976446/html-password-regular-expression-validation
objectid didn't work - needed to inport library

"TypeError: 'Collection' object is not callable. If you meant to call the 'update' method on a 'Collection' object it is failing because no such method exists." when trying to edit a department