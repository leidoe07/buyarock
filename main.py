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
    conn.close()
    
    return render_template("browse.html.jinja", product = results)



@app.route("/product/<product_id>")
def product_page(product_id):
    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"""SELECT * FROM `Product` WHERE `id` = {product_id};""")

    result =cursor.fetchone()

    cursor.execute(f""" SELECT `customer_id`,`product_id`,`rating`,`Review`.`timestamp`, `comment` ,`Review`.`id`	
                FROM `Review`  
                JOIN  `Customer` ON `customer_id` = `Customer`.`id`
                WHERE  `product_id` = {product_id} ;""")
    results = cursor.fetchall()
    total = 0
    for review in results:
        rate = review['rating']
        total= total + rate
    count = len(results)
    average = total/count

    cursor.close()
    conn.close()
    if result is  None:
        abort(404)
    return render_template("product.html.jinja", product = result , reviews = results , average = average)


@app.route("/product/<product_id>/cart" ,methods =['POST'])
@flask_login.login_required
def add_to_cart(product_id):
    if request.method == "POST":
        quantity =request.form["quantity"]

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(f"""
                        INSERT INTO `Cart`
                        (`quantity`, `customer_id`, `product_id`)
                        VALUES
                        ('{quantity}','{flask_login.current_user.user_id}','{product_id}')
                        ON DUPLICATE KEY UPDATE
                            `quantity`= `quantity` + {quantity}
                   
                  ;""" )
        
        
        cursor.close()
        conn.close()
        return redirect('/cart')

    
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
            cursor.close()
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

@app.route('/cart', methods=["POST", "GET"] )
@flask_login.login_required
def cart():
    conn=connect_db()
    cursor= conn.cursor()

    customer_id = flask_login.current_user.user_id
    cursor.execute(f"""
                SELECT 
                    `product_name`,
                    `price`,
                    `Cart`.`quantity`,
                    `image`,
                    `product_id`,
                    `Cart`.`id`
                FROM `Cart` 
                JOIN `Product` ON `product_id` = `Product`.`id` 
                WHERE `customer_id` =  {customer_id};""")
    

    results = cursor.fetchall()

    cart_total = 0 

    for item in results:
        total = item['price'] * item['quantity']
        cart_total += total


    cursor.close()

    conn.close()    

    return render_template("cart.html.jinja", products=results, cart_total=cart_total)



@app.route("/cart/<cart_id>/delete" ,methods =['POST','GET'])
@flask_login.login_required
def delete_from_cart(cart_id):
   
    
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"""DELETE FROM `Cart` WHERE  `id` = {cart_id} ;""" )
    conn.close()
    cursor.close()
    return redirect('/cart')
       
@app.route("/cart/<cart_id>/update",methods =['POST'])
@flask_login.login_required
def update_cart(cart_id):
    cart_itm_qty = request.form["quantity"]
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f""" UPDATE `Cart` SET `quantity`= {cart_itm_qty} WHERE  `id` = {cart_id} ;""" )
    conn.close()
    cursor.close()
    return redirect('/cart')

@app.route("/checkout",methods =['POST'])
@flask_login.login_required
def checkout_page():
    conn = connect_db()
    cursor = conn.cursor()

    customer_id = flask_login.current_user.user_id
    cursor.execute(f"""
                SELECT 
                    `product_name`,
                    `price`,
                    `Cart`.`quantity`,
                    `image`,
                    `product_id`,
                    `Cart`.`id`
                FROM `Cart` 
                JOIN `Product` ON `product_id` = `Product`.`id` 
                WHERE `customer_id` =  {customer_id};""")
    results = cursor.fetchall()
    cart_total = 0
    for item in results:
        total = item['price'] * item['quantity']
        cart_total += total

    conn.close()
    cursor.close()
    return render_template("checkout.html.jinja"  , products=results, cart_total=cart_total )



@app.route ("/continue_sale", methods=["POST"]) 
def finish_sale():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.user_id


    cursor.execute(f"""INSERT INTO `Sale` (`customer_id`)
                    VALUES ({customer_id});""")



    sale_id = cursor.lastrowid



    cursor.execute(f""" SELECT * FROM `Cart`  WHERE  `customer_id` = {customer_id}   ;""")
    results = cursor.fetchall()
    

    for item in results:
        
        cursor.execute (f"""
                   
                    INSERT INTO `Sale_Product`
                   (`product_id`, `sale_id`,`quantity`)
                   VALUES
                        ({item['product_id']}, {sale_id },{item['quantity']} )
;""")
        


    cursor.execute(f"""

    "DELETE FROM `Cart` WHERE  `id` = {customer_id}

    """)
    return ("/thankyou")

@app.route("/add_review/<product_id>/", methods=["POST"])
def add_review(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    comment = request.form["comment"]
    rating = request.form["rating"]
    customer_id = flask_login.current_user.user_id
    cursor.execute(f"SELECT * FROM `Review` WHERE `product_id` = {product_id} AND `customer_id` = {customer_id};")
    result = cursor.fetchone()
    cursor.execute(f"""
                    INSERT INTO `Review`
                    (`product_id`, `comment`, `rating`, `customer_id`)
                    VALUES
                    ('{product_id}', '{comment}', '{rating}','{customer_id}')
                    ;""")
    
    conn.close()
    cursor.close()
    flash("Review Added")
    return redirect(url_for("product_page", product_id=product_id))
