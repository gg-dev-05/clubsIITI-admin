from flask import Flask, render_template, redirect, request, session, url_for
import yaml
from flask_mysqldb import MySQL
from authlib.integrations.flask_client import OAuth
from functions.dbConfig import database_config



app = Flask(__name__)


env = "dev"
DATABASE_URL = ""
if env == "dev":
    dev = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
    DATABASE_URL  = dev['CLEARDB_DATABASE_URL']

else:
    DATABASE_URL  = os.environ.get("CLEARDB_DATABASE_URL")


user, password, host, db = database_config(DATABASE_URL)

app.config['MYSQL_HOST'] = host
app.config['MYSQL_USER'] = user
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = db

mysql = MySQL(app)

# OAuth Config
if env == 'dev':
    app.secret_key = dev['secret_key']
else:
    app.secret_key = os.environ.get("secret_key")
oauth = OAuth(app)
# value_when_true if condition else value_when_false
clientSecret = os.environ.get("client_secret") if (env != 'dev') else dev['client_secret']
clientId = os.environ.get("client_id") if (env != 'dev') else dev['client_id']

google = oauth.register(
    name="google",
    client_id=clientId,
    client_secret= clientSecret,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint=
    "https://openidconnect.googleapis.com/v1/userinfo",  # This is only needed if using openId to fetch user info
    client_kwargs={"scope": "openid email profile"},
)

@app.route("/")
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students;")
    data = cur.fetchall()
    print(data)

    return str(data)


    
@app.route("/login")
def login():
    google = oauth.create_client("google")
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    google = oauth.create_client("google")
    token = google.authorize_access_token()
    resp = google.get("userinfo", token=token)
    user_info = resp.json()
    # print(user_info)
    session["email"] = user_info["email"]
    email = session["email"]   
    session["name"] = user_info["name"]
    session["signedIn"] = True

    
    # Find admin mail in database (assuming garvitgalgat@gmail.com is admin)
    if(email == "garvitgalgat@gmail.com"):
        session["name"] = "ADMIN"
        return redirect("/admin")

    
    if email[:3] in ("cse") and email[-11:] == "@iiti.ac.in":
        session["roll_no"] = email[3:12]
        session["branch"] = email[:3].upper()
        return redirect("/")
    elif email[:2] in ("ee", "me", "ce") and email[-11:] == "@iiti.ac.in":
        session["roll_no"] = email[2:11]
        session["branch"] = email[:2].upper()
        return redirect("/")
    elif email[:4] in ("mems") and email[-11:] == "@iiti.ac.in":
        session["roll_no"] = email[4:13]
        session["branch"] = email[:4].upper()

        return redirect("/")
    else:
        logout()
        session["signedIn"] = False 
        return redirect("/")

    


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)