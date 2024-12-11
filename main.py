from flask import Flask, render_template, request
import pymysql
from dynaconf import Dynaconf


app = Flask(__name__)

conf = Dynaconf(
    settings_file = ['settings.toml']
)

def  connect_dv():
    conn =pymysql.connect(
        host="10.100.34.80",
        database="ldore_buy_a_rock",
        user = "ldore",
        password = conf.password,
        autocommit= True,
        cursorclass= pymysql.cursors.DictCursor,

    )
    return conn

@app.route("/")
def index():
    return render_template("homepage.html.jinja")


@app.route("/browse")
def  product_browse ():
    query = request.args.get('query')
    conn = connect_dv()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product` ")

    else:
        cursor.execute(f"SELECT * FROM `Product`  WHERE `product_name` LIKE '%{query}% ' OR `id` LIKE '%{query}%' OR `description` LIKE '%{query}%'  ; ")

    results = cursor.fetchall()

    cursor.close()
    conn.close
    
    return render_template("browse.html.jinja", product = results)