from flask import Flask, render_template, request,redirect,flash
import pymysql
from dynaconf import Dynaconf



app = Flask(__name__)

conf = Dynaconf(
    settings_file = ['settings.toml']
)


app.secret_key = conf.secret_key
def connect_db ():
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
    conn = connect_db()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product` ")

    else:
        cursor.execute(f"SELECT * FROM `Product`  WHERE `product_name` LIKE '%{query}% ' OR `id` LIKE '%{query}%' OR `description` LIKE '%{query}%'  ; ")

    results = cursor.fetchall()

    cursor.close()
    conn.close
    
    return render_template("browse.html.jinja", product = results)

@app.route("/product/<product_id>")
def product_page(product_id):
    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")

    result =cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja" , product = result)

    
@app.route("/signup", methods=["POST", "GET"])
def sign_up():

    if request.method == "POST":
        
        first_name=request.form["first_name"]
        last_name=request.form["last_name"]
        email=request.form["email"]
        phone=request.form["phone"]
        address=request.form["address"]
        username=request.form["username"]
        password=request.form["password"]
        confirm_password=request.form["confirm_password"]


    
        conn = connect_db()
        cursor = conn.cursor()

        if password!= confirm_password:
            flash(" passwords do not match")

        SpecialSym =['$', '@', '#', '%']
        if not any(char in SpecialSym for char in password):
            print('Password should have at least one of the symbols $@#') 

        if len(password) < 8:
            flash("password must be longer than 8 character")

        if len(password) > 20:
            flash("password must be longer than 8 character")




        try:
            cursor.execute(f"""
                INSERT INTO `Customer`
                    (`username`,`first_name`, `last_name`,`address`,`phone_number`,`email`,`password`)
                VALUES
                    ('{username}','{first_name}','{last_name}','{address}','{phone}','{email}','{password}')
            
            """)
        except  pymysql.err.IntegrityError:
            # oh noo!! Username or Email already exists
            flash(" uh oh!! Username or Email is already in use")
            
        else:
            return redirect('/signin')
        finally:
            cursor.close
            conn.close()

       


    return  render_template("signup.html.jinja")            






@app.route("/signin")
def sign_in():
     return  render_template("signin.html.jinja")