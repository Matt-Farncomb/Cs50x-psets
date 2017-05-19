from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
import collections
from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():

    temp_list = []
    try:
        retrieve_current_stock = db.execute("SELECT DISTINCT product FROM Transactions WHERE user_id = :user", user = session["user_id"])
    except:
            return "test"
    db.execute("DELETE FROM current_stock_price")
    for e in retrieve_current_stock:
            
        temp = lookup(e['product'])
        temp = temp['price']
        temp_product = e['product']
        temp_counting_stuff = db.execute("SELECT product FROM transactions WHERE product = :current_product", current_product = e['product'])
        
        temp_current_price = db.execute("INSERT INTO current_stock_price (stock, stock_price) VALUES (:stock, :current_stock_price)", stock = str(temp_product), current_stock_price = temp )
        temp_dict = {str(temp_product):temp}
        
        temp_list.append(temp_dict)

    rows = db.execute('''SELECT SUM(transactions.quantity) as 'new_quantity', transactions.stock_price as purchase_price, 
                                product AS stocks_owned, current_stock_price.stock_price AS 'Current_Stock_Price', 
                                current_stock_price.stock_price * SUM(transactions.quantity) AS 'Current_Total_Value'
                                FROM transactions JOIN users ON transactions.user_id = users.id  
                               JOIN current_stock_price ON transactions.product = current_stock_price.stock  GROUP BY product ''')
    
    rows3 = db.execute('''SELECT users.cash + SUM(current_stock_price.stock_price * transactions.quantity) AS 'net_worth' 
                               FROM transactions JOIN users ON transactions.user_id = users.id 
                               JOIN current_stock_price ON transactions.product = current_stock_price.stock WHERE users.id = :user GROUP BY users.id''', user = session["user_id"])
    try:
        rows2 = db.execute("SELECT users.cash, :rows3 AS 'net_worth' FROM users WHERE id = :user", user = session["user_id"], rows3 = rows3)
                                   
        row_ord_dict = collections.OrderedDict()
        rows_list = []
    
        return render_template("index.html", rows = rows, rows2 = rows2, rows3 = rows3,temp_counting_stuff=temp_counting_stuff)
    except:
        rows2 = db.execute("SELECT users.cash, users.cash AS 'net_worth' FROM users WHERE id = :user", user = session["user_id"])
        return render_template("index.html", rows2 = rows2, rows3 = rows2 )

def hash_password(password):
            return pwd_context.encrypt(password)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
            
        # ensure password was submitted
        elif not request.form.get("confirm password"):
            return apology("must confirm password")
            
        elif request.form.get("confirm password") != request.form.get("password"):
            return apology("Please re-enter password")
       
        # query database for username
        rows = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=hash_password(request.form.get("password")))

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    currency = request.form.get("currency")
    quantity = request.form.get("quantity")
    try:
            
        if request.method == "POST":
    
            if currency == "" or quantity == "" or currency == None or quantity == None:
                return render_template("buy.html")
            else:
                currency_value = lookup(currency)
                if currency_value == None:
                    return apology("NOT A REAL STOCK")
                else:
                    currency = str(currency).upper()
                    ## access the price key of the stock
                    stock_price = currency_value['price']
                    ## convert quantity to float to enable multiplication
                    quantity = int(quantity)
                    if quantity < 0:
                        return apology("please enetr positive numbers only")
                    total_cost = stock_price * quantity
                
                    # retrieves current chash amount from the db
                    user_cash = db.execute("SELECT cash FROM users WHERE ID = :user", user = session["user_id"])
                    user_cash = user_cash[0]
                    new_cash = float(user_cash ['cash'])
                    if new_cash < total_cost:
                        return apology("Too Poor")
                    new_cash-=total_cost
                    # updates db with the new cash amount
                    rows = db.execute("UPDATE users SET cash = :new_amount WHERE id = :user", new_amount = new_cash, user = session["user_id"] )
                    rows_II = db.execute('''INSERT INTO Transactions (user_id, product, quantity, total_cost, stock_price) 
                                        VALUES (:user, :currency, :quantity, :total_cost, :stock_price)''',
                                        user = session["user_id"], currency = currency, quantity = quantity, total_cost = total_cost, stock_price = stock_price)
                
                    return index()
                
        else:
            return render_template("buy.html")
            
    except:
        "AttributeError: 'NoneType' object has no attribute 'startswith'"
        
@app.route("/history")
@login_required
def history():
    
    
    rows = db.execute("SELECT * FROM transactions WHERE user_id = :user", user = session["user_id"])
    """Show history of transactions."""
    return render_template("history.html", rows = rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    new_symbol = request.form.get("currency")
    
    if request.method == "POST":

        if new_symbol == "" or new_symbol == None:
            return render_template("quote.html")
        else:
            new_result = lookup(new_symbol)
            if new_result == None:
                return apology("NOT A REAL STOCK")
            return quote_result(new_result)
            
    else:
        return render_template("quote.html")

@app.route("/quote_result")
def quote_result(result):
    """return quote result"""
    return render_template("quote_result.html", result = result)
    

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    
    render_template("sell.html")
    
    currency = request.form.get("currency")
    quantity = request.form.get("quantity")
    
    if request.method == "POST":

        if currency == "" or quantity == "" or currency == None or quantity == None:
            return render_template("sell.html")
        else:
            currency = str(currency).upper()
            currency_value = lookup(currency)
            test = db.execute("SELECT SUM(quantity) FROM transactions WHERE product = :currency GROUP BY product", currency = currency)
  
            for e in test:
                for key, value in e.items():
                    value = int(value)
                    if value < int(quantity):
                        return apology("not ennough stock")
            
            if currency_value == None:
                return apology("NOT A REAL STOCK")
            
            else:
                ## access the price key of the stock
                stock_price = currency_value['price']
                ## convert quantity to float to enable multiplication
                quantity = int(quantity)
                if quantity < 0:
                    return apology("please enter positive numbers only")
                total_cost = stock_price * quantity
                sale = db.execute("UPDATE users SET cash = cash + (:quantity * :stock_price) WHERE id = :user", quantity = quantity, stock_price = stock_price, user = session["user_id"] )
                
                ## sell stock adds negative sales to the table so that the total quantities will be adding a -1
                sell_stock = db.execute('''INSERT INTO Transactions (user_id, product, quantity, total_cost, stock_price) 
                                    VALUES (:user, :currency, :quantity, :total_cost, :stock_price)''', user = session["user_id"], 
                                    currency = currency, quantity = -quantity, total_cost = -total_cost , stock_price = stock_price)
                return index()
    else:
        return render_template("sell.html")
        
   
@app.route("/extra", methods=["GET", "POST"])
@login_required
def extra():
    
    beg = request.form.get("beg")

    if request.method == "POST":
                if beg == "" or beg == None:
                    return render_template("extra.html")
                else:
                    rows2 = db.execute("UPDATE users SET cash = users.cash + :begged WHERE id = :user", begged = beg, user = session["user_id"])
                    return index()
    else:
        return render_template("extra.html")    
   
     
@app.route("/sell_one", methods=["GET", "POST"])
@login_required
def sell_one():
    '''sell one stock at a time per click'''
   
    currency = request.form.get("currency")
   
    if request.method == "POST":

        currency_value = lookup(currency)
        quantity = 1
        test = db.execute("SELECT SUM(quantity) FROM transactions WHERE product = :currency GROUP BY product", currency = currency)
        
        for e in test:
            for key, value in e.items():
                value = int(value)
                if value <= 0:
                    return apology("not ennough stock")
        
        
        
        
        if currency_value == None:
            return apology("NOT A REAL STOCK")
        
        else:
            ## access the price key of the stock
            stock_price = currency_value['price']
            ## convert quantity to float to enable multiplication
            quantity = int(quantity)
            
            total_cost = stock_price
            sale = db.execute("UPDATE users SET cash = cash + (:quantity * :stock_price) WHERE id = :user", quantity = quantity, stock_price = stock_price, user = session["user_id"] )
            
            ## sell stock adds negative sales to the table so that the total quantities will be adding a -1
            sell_stock = db.execute('''INSERT INTO Transactions (user_id, product, quantity, total_cost, stock_price) 
                                VALUES (:user, :currency, :quantity, :total_cost, :stock_price)''', user = session["user_id"], 
                                currency = currency, quantity = -quantity, total_cost = -total_cost , stock_price = stock_price)
            return index()
    else:
        return render_template("sell.html")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
     