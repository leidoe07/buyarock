from flask import Flask, render_template, request,redirect,flash,abort
import pymysql
from dynaconf import Dynaconf
import flask_login


app = Flask(__name__)

conf = Dynaconf(
    settings_file = ['settings.toml']
)


app.secret_key = conf.secret_key


login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view =('/signin')

class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True
    
    def __init__(self, user_id, username,email,first_name,last_name):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self) :
        return str(self.user_id)   
    


@login_manager.user_loader    
def load_user(user_id):
    conn = connect_db()
    cursor =conn.cursor()
    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id};")
    result = cursor.fetchone()
    cursor.close
    conn.close

    if result is not None:
        return User(result['id'], result['username'], result['email'],result['first_name'],result['last_name'])

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
    if result is  None:
        abort(404)
    return render_template("product.html.jinja")




    
@app.route("/signup", methods=["POST", "GET"])
def sign_up():
    if flask_login.current_user.is_authenticated:
        return redirect('/')
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

        spec_char=['$', '@', '#', '%']
        if not any(char in spec_char for char in password):
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






@app.route("/signin", methods=["POST", "GET"])
def sign_in():
    if request.method =="POST" :
        username = request.form['username']
        password = request.form['password']

        conn =connect_db()

        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")

        result = cursor.fetchone()
        
        if result is None:
            flash('Username/Password is Wrong')
        elif password != result['password']:
            flash('Username/Password is Wrong')
        else:
            user = User(result['id'], result['username'], result['email'],result['first_name'],result['last_name'])

            flask_login.login_user(user)
            flask_login.current_user.is_authenticated
            return redirect('/')

    if flask_login.current_user.is_authenticated:
        return redirect('/')
    return  render_template("signin.html.jinja")

@app.route('/logout')
def logout():
        flask_login.logout_user()
        return redirect('/')


@app.route('/cart')
@flask_login.login_required
def cart():
   return "hi"
    